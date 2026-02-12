## Inputs

- `config/competitors.json` - Configuration file listing competitor URLs and selectors (committed to Git)
- `force_run` - Boolean (optional, from GitHub Actions workflow_dispatch input) - Force crawl even if not scheduled time

## Outputs

- `reports/YYYY-MM-DD.md` - Weekly digest report showing all detected changes (committed to main branch)
- `state/snapshots/{competitor_slug}/YYYY-MM-DD.json` - Historical snapshot for each competitor (committed to main branch)
- `state/snapshots/{competitor_slug}/latest.json` - Latest snapshot for each competitor (committed to main branch)
- Email digest (optional, if email.enabled=true in config) - HTML + plain text email to configured recipients

---

## Step 1: Load Configuration

**Read** `config/competitors.json` and validate structure.

```bash
cat config/competitors.json
```

**Expected structure:**

```json
{
  "competitors": [
    {
      "name": "Competitor A",
      "slug": "competitor-a",
      "urls": {
        "blog": "https://competitora.com/blog",
        "pricing": "https://competitora.com/pricing",
        "features": "https://competitora.com/features"
      },
      "selectors": {
        "blog_items": "article.post",
        "price_value": ".price-amount",
        "feature_items": ".feature-card"
      }
    }
  ],
  "email": {
    "enabled": false,
    "recipients": ["team@example.com"]
  }
}
```

**Validation:**
- `competitors` array must have at least 1 entry
- Each competitor must have: `name`, `slug`, `urls` (object with at least one URL)
- `selectors` is optional (fallback extraction if missing)

**Failure mode:** Config file missing or invalid JSON → **HALT** with clear error. Cannot proceed without competitor list.

**Fallback:** None. This is a required input.

---

## Step 2: Crawl Competitors

**If 3+ competitors configured:** Use **Agent Teams** for parallel crawling (faster)  
**If 1-2 competitors configured:** Use **sequential crawling** (simpler)

### Option A: Parallel Crawling (Agent Teams)

**When:** 3 or more competitors in config

**Team Lead (main agent) responsibilities:**
1. Parse `config/competitors.json` and extract competitor list
2. Create shared task list with one task per competitor
3. Spawn crawl-specialist teammates (one per competitor)
4. Collect all snapshots from teammates
5. Pass snapshots to change-detector-specialist

**Teammate task template:**
```
Crawl competitor {name} using the crawl-specialist subagent.
Config: {competitor_config_json}
Output: Save snapshot to /tmp/snapshot-{slug}.json
```

**Task execution:** Each teammate delegates to `crawl-specialist` subagent with competitor config.

**Merge logic:** Simple collection - no conflict resolution needed. Each teammate returns a snapshot file path.

**Performance:** If 5 competitors at 15s each:
- Sequential: 75 seconds
- Parallel: ~20 seconds (3-4x speedup)

### Option B: Sequential Crawling (Fallback)

**When:** 1-2 competitors in config OR Agent Teams disabled/failed

**Execution:** For each competitor in config:

1. **Write temp config file:**
   ```bash
   echo '{competitor_json}' > /tmp/config-{slug}.json
   ```

2. **Delegate to crawl-specialist:**
   ```
   @crawl-specialist Please crawl this competitor.
   Config: /tmp/config-{slug}.json
   Output: /tmp/snapshot-{slug}.json
   ```

3. **Validate snapshot:**
   ```bash
   if [ -f /tmp/snapshot-{slug}.json ]; then
     echo "✓ Crawl successful: {slug}"
   else
     echo "✗ Crawl failed: {slug} (skipping)"
   fi
   ```

**Per-competitor error isolation:** If one competitor fails, log the error and continue with others. Partial results are acceptable.

**Failure mode:** Competitor site unreachable, selectors fail, Firecrawl API error → **SKIP** that competitor, log error, continue with others.

**Fallback:** HTTP + BeautifulSoup if Firecrawl unavailable. Partial content extraction if selectors fail.

**Output:** `/tmp/snapshot-{slug}.json` for each competitor (or error flag if failed)

---

## Step 3: Detect Changes

For each competitor snapshot:

1. **Delegate to snapshot-manager-specialist** to load previous snapshot:
   ```
   @snapshot-manager-specialist Please load the previous snapshot for {slug}.
   Path: state/snapshots/{slug}/latest.json
   ```

2. **Delegate to change-detector-specialist** to detect changes:
   ```
   @change-detector-specialist Please detect changes for {slug}.
   Current: /tmp/snapshot-{slug}.json
   Previous: state/snapshots/{slug}/latest.json (or none if first run)
   Output: /tmp/changes-{slug}.json
   ```

3. **Validate changes output:**
   ```bash
   if [ -f /tmp/changes-{slug}.json ]; then
     echo "✓ Change detection complete: {slug}"
     jq '.summary' /tmp/changes-{slug}.json
   else
     echo "✗ Change detection failed: {slug}"
   fi
   ```

**First-run handling:** If no previous snapshot exists, treat all content as "new". This is expected behavior.

**Failure mode:** Previous snapshot missing (first run) → Treat all content as new. Snapshot format mismatch → Fall back to full-text diff.

**Fallback:** If change detection fails for a competitor, create an empty changes file (zero changes) and continue.

**Output:** `/tmp/changes-{slug}.json` for each competitor

---

## Step 4: Generate Digest Report

**Delegate to report-generator-specialist** to create the markdown report:

```
@report-generator-specialist Please generate the weekly digest report.
Changes files:
  - /tmp/changes-competitor-a.json
  - /tmp/changes-competitor-b.json
  - /tmp/changes-competitor-c.json
Report date: {YYYY-MM-DD}
Output: reports/
```

**Date determination:**
```bash
REPORT_DATE=$(date -u +%Y-%m-%d)
```

**Validation:**
```bash
REPORT_PATH="reports/$REPORT_DATE.md"
if [ -f "$REPORT_PATH" ]; then
  echo "✓ Report generated: $REPORT_PATH"
  wc -l "$REPORT_PATH"
else
  echo "✗ Report generation failed"
  exit 1
fi
```

**Zero-changes case:** If no changes detected across all competitors, still generate a report saying "No changes this week". This serves as a "heartbeat" confirmation that the system ran.

**Failure mode:** No changes files found → **HALT** with error. Invalid date format → **HALT** with error.

**Fallback:** If a single competitor's changes file is corrupted, skip that competitor and generate report with remaining competitors. Partial report is acceptable.

**Output:** 
- `reports/YYYY-MM-DD.md` - Markdown report
- `/tmp/email-body.txt` - Plain text email body (from tool stdout)

---

## Step 5: Save Snapshots

For each competitor snapshot:

**Delegate to snapshot-manager-specialist** to save the current snapshot:

```
@snapshot-manager-specialist Please save the current snapshot for {slug}.
Snapshot: /tmp/snapshot-{slug}.json
Date: {YYYY-MM-DD}
```

**Validation:**
```bash
jq -r '.success' /tmp/save-result-{slug}.json

if [ "$SUCCESS" = "true" ]; then
  echo "✓ Snapshot saved: {slug}"
else
  echo "✗ Snapshot save failed: {slug}"
  jq '.error' /tmp/save-result-{slug}.json
fi
```

**Atomic writes:** The tool uses temp files + rename to prevent corruption.

**Pruning:** Automatically keeps last 52 snapshots (1 year), deletes older ones.

**Failure mode:** Snapshot too large (>10MB) → Compress (drop excerpts). If still too large → Skip save, log error, but DO NOT fail workflow (report is already committed).

**Fallback:** If compression fails, log error and continue. The previous snapshot remains intact.

**Output:**
- `state/snapshots/{slug}/YYYY-MM-DD.json` - Dated snapshot
- `state/snapshots/{slug}/latest.json` - Copy of dated snapshot

---

## Step 6: Send Email (Optional)

**Condition:** Skip this step if `config.email.enabled` is `false`.

**Check email configuration:**
```bash
EMAIL_ENABLED=$(jq -r '.email.enabled' config/competitors.json)

if [ "$EMAIL_ENABLED" = "true" ]; then
  echo "Email enabled, sending digest..."
else
  echo "Email disabled, skipping..."
  exit 0
fi
```

**Extract recipients:**
```bash
RECIPIENTS=$(jq -r '.email.recipients | join(",")' config/competitors.json)
```

**Send email:**
```bash
python tools/send_email.py \
  --subject "Competitor Monitor Report - $REPORT_DATE" \
  --body-text "$(cat /tmp/email-body.txt)" \
  --recipients "$RECIPIENTS" \
  > /tmp/email-result.json
```

**Validation:**
```bash
EMAIL_SUCCESS=$(jq -r '.success' /tmp/email-result.json)

if [ "$EMAIL_SUCCESS" = "true" ]; then
  echo "✓ Email sent successfully"
else
  echo "✗ Email send failed (non-fatal)"
  jq '.error' /tmp/email-result.json
fi
```

**Failure mode:** SMTP credentials missing → Log error, skip email, **DO NOT fail workflow**. SMTP server unreachable → Retry once after 30s. If still fails, log error and continue.

**Fallback:** Email is optional. If it fails, the report is still committed to the repo. Log the error for investigation but don't block the workflow.

**Output:** Email delivery status (logged, not committed)

---

## Step 7: Commit Results

**Stage files for commit:**
```bash
git add reports/$REPORT_DATE.md
git add state/snapshots/*/$(date -u +%Y-%m-%d).json
git add state/snapshots/*/latest.json
```

**CRITICAL:** Only stage specific files. **NEVER** use `git add -A` or `git add .`

**Verify staged files:**
```bash
git status --short
# Should show only:
# A  reports/2026-02-12.md
# A  state/snapshots/competitor-a/2026-02-12.json
# A  state/snapshots/competitor-a/latest.json
# A  state/snapshots/competitor-b/2026-02-12.json
# A  state/snapshots/competitor-b/latest.json
```

**Commit:**
```bash
TOTAL_CHANGES=$(jq -s 'map(.summary | .new_posts_count + .pricing_changes_count + .new_features_count) | add' /tmp/changes-*.json)

git commit -m "chore: competitor monitor report - $REPORT_DATE

- Monitored: $(jq '.competitors | length' config/competitors.json) competitors
- Changes detected: $TOTAL_CHANGES
- Report: reports/$REPORT_DATE.md"
```

**Push:**
```bash
git push origin main
```

**Retry logic:** If push fails (network error, conflict):
1. Pull with rebase: `git pull --rebase origin main`
2. Retry push once
3. If still fails → **HALT** workflow with error (results not persisted)

**Failure mode:** Git push fails → **HALT** workflow with error. Results are NOT persisted. This is intentional - we want atomic success (all or nothing).

**Fallback:** One retry after 10s delay. If that fails, job fails.

**Output:** Git commit SHA, pushed to remote

---

## Success Criteria

✅ All required files committed to Git:
- `reports/YYYY-MM-DD.md`
- `state/snapshots/{slug}/YYYY-MM-DD.json` (one per competitor)
- `state/snapshots/{slug}/latest.json` (one per competitor)

✅ Workflow completes with exit code 0

✅ At least 1 competitor was successfully crawled

## Failure Modes Summary

| Step | Failure Scenario | Action |
|------|------------------|--------|
| 1. Load Config | Config file missing/invalid | **HALT** - cannot proceed |
| 2. Crawl | One competitor site down | **SKIP** that competitor, continue |
| 2. Crawl | All competitors fail | **HALT** - no data to process |
| 3. Detect | Previous snapshot missing | **CONTINUE** - treat as first run |
| 3. Detect | One competitor fails detection | **SKIP** that competitor, continue |
| 4. Generate | No valid changes files | **HALT** - cannot generate report |
| 4. Generate | Zero changes detected | **CONTINUE** - generate "no changes" report |
| 5. Save | Snapshot too large | **COMPRESS** - drop excerpts, retry |
| 5. Save | Still too large after compression | **LOG** error, continue (report already saved) |
| 6. Email | SMTP credentials missing | **LOG** error, skip email, continue |
| 6. Email | SMTP send fails | **RETRY** once, then log and continue |
| 7. Commit | Git push fails | **RETRY** once, then **HALT** (not persisted) |

---

## Notes

- **Subagent delegation is the default** - Use `@subagent-name` syntax to delegate steps
- **Agent Teams is optional** - Only use for 3+ competitors (parallel speedup)
- **Sequential fallback always available** - If Agent Teams fails or is disabled, fall back to sequential
- **Partial success is acceptable** - 3 out of 5 competitors crawled is better than all-or-nothing
- **Commit is atomic** - Either all files commit or none (git push retry logic ensures this)
- **Email is optional** - Report is still valuable without email delivery
