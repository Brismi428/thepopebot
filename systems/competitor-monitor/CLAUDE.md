# Competitor Monitor - Operating Instructions

This is a WAT system that autonomously monitors competitor websites weekly, detects changes to blog posts, pricing, and features, and generates a digest report committed to Git.

## System Identity

**Name:** competitor-monitor  
**Purpose:** Weekly competitive intelligence automation  
**Pattern:** Monitor > Detect > Alert + Scrape > Process > Output + Collect > Transform > Store  
**Execution:** GitHub Actions (scheduled), Claude Code CLI (local), Agent HQ (issue-driven)

## How It Works

1. **Every Monday at 8 AM UTC**, GitHub Actions triggers this workflow
2. **Crawl all competitors** listed in `config/competitors.json` (blog, pricing, features pages)
3. **Detect changes** by comparing current snapshots against previous week's snapshots
4. **Generate markdown report** summarizing all changes across competitors
5. **Commit everything** to Git (report + snapshots)
6. **Send email** (optional) with plain-text digest

## Inputs

### Required
- `config/competitors.json` - Competitor configuration (URLs, selectors)
  - Must define at least 1 competitor
  - Each competitor needs: `name`, `slug`, `urls` (object with page types)
  - `selectors` are optional (tool falls back to generic extraction)

### Optional
- `force_run` - GitHub Actions workflow_dispatch input (boolean)
  - Allows manual triggering outside the Monday 8 AM schedule

## Outputs

### Git Committed
- `reports/YYYY-MM-DD.md` - Weekly digest markdown report
- `state/snapshots/{slug}/YYYY-MM-DD.json` - Dated snapshot for each competitor
- `state/snapshots/{slug}/latest.json` - Latest snapshot (copy of dated file)

### Email (Optional)
- Plain-text digest sent via SMTP to configured recipients
- Only if `config.email.enabled = true`

## Required Secrets

Configure these in GitHub repository secrets:

| Secret | Purpose | Required |
|--------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API access for AI agent | Yes |
| `FIRECRAWL_API_KEY` | Web scraping API (primary method) | Recommended |
| `SMTP_HOST` | SMTP server hostname | Only if email enabled |
| `SMTP_PORT` | SMTP server port (usually 587) | Only if email enabled |
| `SMTP_USER` | SMTP authentication username | Only if email enabled |
| `SMTP_PASS` | SMTP authentication password | Only if email enabled |
| `EMAIL_FROM` | From address for outgoing emails | Only if email enabled |

**Note:** If `FIRECRAWL_API_KEY` is not set, the system falls back to HTTP + BeautifulSoup (no JS rendering).

## Subagent Architecture

This system uses **specialist subagents** for focused delegation:

### crawl-specialist
**When to delegate:** Need to scrape competitor websites and extract structured content  
**Tools:** Bash, Read  
**Responsibilities:**
- Execute `crawl_competitor.py` with competitor config
- Handle site-specific selectors
- Fall back to generic extraction if selectors fail
- Return JSON snapshot for each competitor

**Delegation syntax:**
```
@crawl-specialist Please crawl competitor-a.
Config: /tmp/config-competitor-a.json
Output: /tmp/snapshot-competitor-a.json
```

### change-detector-specialist
**When to delegate:** Need to compare current vs previous snapshots  
**Tools:** Bash, Read  
**Responsibilities:**
- Load previous snapshot from `state/snapshots/{slug}/latest.json`
- Execute `detect_changes.py` to compare snapshots
- Identify new blog posts, pricing changes, new features
- Handle first-run initialization (no previous snapshot)

**Delegation syntax:**
```
@change-detector-specialist Please detect changes for competitor-a.
Current: /tmp/snapshot-competitor-a.json
Previous: state/snapshots/competitor-a/latest.json
Output: /tmp/changes-competitor-a.json
```

### report-generator-specialist
**When to delegate:** Need to generate markdown digest from all changes  
**Tools:** Write, Read, Bash  
**Responsibilities:**
- Execute `generate_digest.py` with all changes files
- Generate markdown report with summary + per-competitor sections
- Generate plain-text email body
- Handle zero-changes case (still create report)

**Delegation syntax:**
```
@report-generator-specialist Please generate the weekly digest report.
Changes files: /tmp/changes-*.json
Report date: 2026-02-12
Output: reports/
```

### snapshot-manager-specialist
**When to delegate:** Need to load or save historical snapshots  
**Tools:** Read, Write, Bash  
**Model:** haiku (fast, simple task)  
**Responsibilities:**
- Load previous snapshot from `state/snapshots/{slug}/latest.json`
- Execute `save_snapshot.py` with atomic writes
- Update `latest.json` (copy of dated snapshot)
- Prune old snapshots (keep last 52 weeks)
- Handle snapshot size management (compress if > 10MB)

**Delegation syntax:**
```
@snapshot-manager-specialist Please save the current snapshot for competitor-a.
Snapshot: /tmp/snapshot-competitor-a.json
Date: 2026-02-12
```

## Agent Teams Usage

**Condition:** Use Agent Teams IF 3+ competitors are configured  
**Benefit:** 2-4x faster wall time for crawling phase (parallel execution)  
**Fallback:** Sequential crawling always available

### When to Use Agent Teams

The system checks `config/competitors.json` at runtime:
- **3+ competitors** → Create team with one crawler per competitor
- **1-2 competitors** → Sequential execution (overhead not justified)

### Team Structure

**Team Lead (main agent):**
- Reads competitor config
- Creates shared task list (one task per competitor)
- Spawns crawler teammates
- Collects all snapshots
- Coordinates with change-detector-specialist

**Teammates (one per competitor):**
- Each receives a single competitor config
- Delegates to `crawl-specialist` subagent
- Returns snapshot file path
- Independent execution (no data dependencies)

**Example:**
```
5 competitors:
- Sequential: 75 seconds (5 × 15s)
- Parallel (Agent Teams): ~20 seconds (max 15s + overhead)
- Speedup: 3.75x
```

### Cost Note
Agent Teams does NOT increase token cost - same number of API calls, just parallel execution.

## Workflow Execution

### Step-by-Step Process

1. **Load Configuration**
   - Read `config/competitors.json`
   - Validate structure (at least 1 competitor)
   - Extract competitor list

2. **Crawl Competitors**
   - **If 3+ competitors:** Use Agent Teams (parallel)
   - **If 1-2 competitors:** Sequential delegation
   - Each competitor: Delegate to `crawl-specialist`
   - Output: `/tmp/snapshot-{slug}.json` per competitor

3. **Detect Changes**
   - For each competitor:
     - Delegate to `snapshot-manager-specialist` to load previous
     - Delegate to `change-detector-specialist` to compare
   - Output: `/tmp/changes-{slug}.json` per competitor

4. **Generate Digest**
   - Delegate to `report-generator-specialist`
   - Input: All `/tmp/changes-*.json` files
   - Output: `reports/YYYY-MM-DD.md` + email body

5. **Save Snapshots**
   - For each competitor:
     - Delegate to `snapshot-manager-specialist`
   - Output: `state/snapshots/{slug}/YYYY-MM-DD.json` + `latest.json`

6. **Send Email (Optional)**
   - Check `config.email.enabled`
   - If true: Execute `send_email.py` with plain-text body
   - If false: Skip this step

7. **Commit Results**
   - Stage specific files: `git add reports/*.md state/snapshots/*/*.json`
   - Commit with detailed message (competitor count, change count)
   - Push to origin with retry logic

### Failure Handling

| Scenario | Action |
|----------|--------|
| Config missing/invalid | HALT - cannot proceed |
| 1 competitor fails crawl | SKIP - continue with others |
| All competitors fail crawl | HALT - no data to process |
| Previous snapshot missing | CONTINUE - treat as first run |
| Change detection fails | SKIP that competitor, continue |
| Zero changes detected | CONTINUE - generate "no changes" report |
| Snapshot too large (>10MB) | COMPRESS - drop excerpts, retry |
| Email send fails | LOG error, continue (report already saved) |
| Git push fails | RETRY once, then HALT (not persisted) |

## Tool Reference

### crawl_competitor.py
**Purpose:** Scrape competitor website pages  
**Method:** Firecrawl API → HTTP + BeautifulSoup fallback  
**Input:** `--config PATH` (competitor JSON)  
**Output:** JSON snapshot to stdout  
**Exit codes:** 0 = success (full/partial), 1 = fatal error

### detect_changes.py
**Purpose:** Compare current vs previous snapshots  
**Method:** Structural diff (URL/title matching, price comparison)  
**Input:** `--current PATH`, `--previous PATH` (optional)  
**Output:** JSON changes object to stdout  
**Exit codes:** 0 = success (with/without changes), 1 = fatal error

### generate_digest.py
**Purpose:** Generate markdown report from changes  
**Input:** `--changes PATH [PATH ...]`, `--date YYYY-MM-DD`, `--output DIR`  
**Output:** JSON with report_path and email_body  
**Exit codes:** 0 = success, 1 = fatal error

### save_snapshot.py
**Purpose:** Save snapshot with atomic writes and pruning  
**Method:** Temp file + rename (atomic), auto-prune to 52 snapshots  
**Input:** `--snapshot PATH`, `--slug SLUG`, `--date YYYY-MM-DD`  
**Output:** JSON with success status and paths  
**Exit codes:** 0 = success, 1 = fatal error

### send_email.py
**Purpose:** Send email via SMTP (optional)  
**Method:** SMTP with TLS, retry on transient failure  
**Input:** `--subject STR`, `--body-text STR`, `--recipients STR` (comma-separated)  
**Output:** JSON with success status  
**Exit codes:** 0 = success, 1 = failed

## Three Execution Paths

### 1. GitHub Actions (Production)

**Trigger:** Schedule (every Monday at 8 AM UTC) or manual dispatch

```yaml
# Automatic
on:
  schedule:
    - cron: '0 8 * * 1'

# Manual
on:
  workflow_dispatch:
    inputs:
      force_run:
        type: boolean
```

**Process:**
1. GitHub Actions checks out repo
2. Installs Python deps + Claude Code CLI
3. Runs `claude -p workflow.md`
4. Commits results to Git
5. Uploads logs on failure

**Setup:**
- Configure secrets in GitHub repository settings
- Ensure GitHub Actions is enabled
- Push config file to `config/competitors.json`

### 2. Claude Code CLI (Local Testing)

**When:** Development, testing changes, debugging

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export FIRECRAWL_API_KEY="fc-..."

# Run workflow
claude -p workflow.md
```

**Output:** Same as GitHub Actions (creates report, snapshots locally)

**Commit:** Manually commit and push results after verifying

### 3. GitHub Agent HQ (Issue-Driven)

**Trigger:** Assign an issue to `@claude` or mention in issue comments

**Issue body format:**
```
Run the competitor monitor workflow and generate the weekly report.

Config: config/competitors.json
Force run: true
```

**Process:**
1. Agent reads issue body as task description
2. Executes workflow.md
3. Commits results to a branch
4. Opens draft PR linked to the issue
5. Comments on issue with PR link

**Setup:**
- Requires GitHub Agent HQ integration
- Agent must have write access to the repository

## Troubleshooting

### Problem: "All crawling methods failed"
**Cause:** Site is blocking scrapers or down  
**Solution:**
- Check site is reachable: `curl -I https://competitor.com`
- Verify `FIRECRAWL_API_KEY` is set (fallback is HTTP-only)
- Try manual crawl: `python tools/crawl_competitor.py --config config/competitors.json`

### Problem: "Snapshot too large after compression"
**Cause:** Competitor site has massive content (>10MB)  
**Solution:**
- Reduce number of pages crawled (remove `blog` or `features`)
- Adjust selectors to be more specific (fewer items)
- Increase limit in `save_snapshot.py` (risky - Git performance)

### Problem: "No changes detected every week"
**Cause:** Either competitors are inactive OR selectors are broken  
**Solution:**
- Check manual crawl output: `cat /tmp/snapshot-*.json`
- Verify selectors match current site structure
- Update selectors in `config/competitors.json`

### Problem: "Email send fails with auth error"
**Cause:** SMTP credentials incorrect or expired  
**Solution:**
- Test SMTP manually: `python tools/send_email.py --subject "Test" --body-text "Test" --recipients "you@example.com"`
- Verify all SMTP secrets are set correctly
- Check if SMTP provider requires app-specific password

### Problem: "Git push failed after 3 retries"
**Cause:** Network issue or concurrent commits  
**Solution:**
- Check GitHub status page
- Manually push from local: `git pull --rebase && git push`
- Results are in local Git history, not lost

## Configuration Guide

### Adding a New Competitor

Edit `config/competitors.json`:

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
  ]
}
```

**Finding selectors:**
1. Open site in browser
2. Right-click element → Inspect
3. Find CSS selector (e.g., `article.post`, `.pricing-card`)
4. Test in browser console: `document.querySelectorAll("article.post")`

**Fallback:** If selectors don't work, leave them empty - tool falls back to generic extraction

### Enabling Email Delivery

In `config/competitors.json`:

```json
{
  "competitors": [ ... ],
  "email": {
    "enabled": true,
    "recipients": ["team@example.com", "cto@example.com"]
  }
}
```

Set SMTP secrets in GitHub:
- `SMTP_HOST` (e.g., `smtp.gmail.com`)
- `SMTP_PORT` (usually `587`)
- `SMTP_USER` (your email)
- `SMTP_PASS` (app-specific password)
- `EMAIL_FROM` (from address)

### Changing Schedule

Edit `.github/workflows/monitor.yml`:

```yaml
on:
  schedule:
    # Every day at 6 AM UTC
    - cron: '0 6 * * *'
```

**Cron syntax:** `minute hour day month weekday`

## Performance & Cost

### Execution Time
- **Sequential (1-2 competitors):** ~15-30 seconds per competitor
- **Parallel (3+ competitors with Agent Teams):** ~20-40 seconds total

### GitHub Actions Minutes
- **Weekly run:** ~5 minutes per run = 20 minutes/month
- **Well within free tier:** 2,000 minutes/month (private repos)

### API Costs (per run)
- **Firecrawl:** ~$0.01-0.02 per page (3 pages × N competitors)
- **Claude (Anthropic):** ~$0.05-0.15 per run (depends on content size)
- **Estimated monthly cost:** ~$2-8 for 3 competitors

### Token Usage
- **Crawling:** Low (tools do most work)
- **Change detection:** Low (simple comparison logic)
- **Report generation:** Low (template-based)
- **Total per run:** ~50K-150K tokens (input + output)

## System Dependencies

### Python Packages (requirements.txt)
- `firecrawl-py==0.1.0` - Firecrawl API client
- `httpx==0.27.0` - HTTP client for fallback
- `beautifulsoup4==4.12.3` - HTML parsing
- `lxml==5.1.0` - Fast HTML parser

### External APIs
- **Firecrawl API** (optional) - https://firecrawl.dev
  - Handles JS-rendered sites
  - Falls back to HTTP if not available
- **Anthropic API** (required) - https://claude.ai
  - Powers the Claude agent

### No External Database
- **State storage:** Git repository (JSON files)
- **Version control:** Git history = audit trail
- **Query method:** `git log`, `jq`, `grep`

## Security Considerations

- **Secrets never hardcoded** - All credentials via GitHub Secrets or env vars
- **API keys filtered from logs** - Secrets are redacted in CI output
- **Atomic Git commits** - Prevents partial state corruption
- **Rate limit protection** - 2-second delay between Firecrawl requests
- **Snapshot size limits** - 10MB cap prevents repo bloat

## Maintenance

### Weekly
- Review generated reports for accuracy
- Check for crawl failures in GitHub Actions logs

### Monthly
- Verify selectors still work (site redesigns break them)
- Audit snapshot size growth: `du -sh state/snapshots/`

### Quarterly
- Review competitor list - add/remove as needed
- Update Python dependencies: `pip list --outdated`

### Annually
- Prune old reports (keep last 52 weeks): `git rm reports/2025-*.md`
- Review API costs and usage patterns

## Support

- **Source code:** This repository
- **Issues:** Open a GitHub issue
- **Logs:** Check GitHub Actions workflow runs
- **Debugging:** Run locally with `claude -p workflow.md`
