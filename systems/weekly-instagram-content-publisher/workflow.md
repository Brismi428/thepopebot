# Weekly Instagram Content Publisher -- Workflow

**System:** Weekly Instagram Content Publisher
**Purpose:** Automated Instagram content generation with brand voice compliance, quality review, and auto-publish or manual content pack delivery.

---

## Inputs

- **brand_profile** (JSON): Brand voice guidelines, target audience, banned topics, prohibited claims, preferred CTAs, emoji style, hashtag preferences
- **weekly_theme** (string): Focus topic for the week's posts (e.g., "Spring 2026 Product Launch")
- **post_plan** (JSON): Post counts by type (reels, carousels, single_images), series templates, posting schedule
- **reference_links** (JSON array, optional): URLs to blog posts, announcements, product pages for accurate content extraction
- **publishing_mode** (choice): `auto_publish` (if quality gates pass) or `content_pack_only` (always manual)

---

## Outputs

- **content_pack_{YYYY-MM-DD}.md**: Human-readable content pack with all posts (hook, caption, hashtags, creative brief, alt text, posting time)
- **content_pack_{YYYY-MM-DD}.json**: Machine-readable structured data for all posts
- **review_report_{YYYY-MM-DD}.md**: Quality review results with dimension scores (brand voice, compliance, hashtags, format, claims)
- **publish_log_{YYYY-MM-DD}.json** (if auto_publish): Instagram Graph API responses (media IDs, permalinks, errors)
- **upload_checklist_{YYYY-MM-DD}.md** (if content_pack_only or publish fails): Manual upload instructions with copy-paste ready content
- **latest.md**: Rolling index pointing to most recent content pack

---

## Workflow Steps

### 1. Input Validation & Setup

**Objective:** Parse all inputs, validate required fields, load brand profile, initialize output directory structure.

**Tools:**
- `validate_inputs.py` -- Parse and validate all workflow inputs
- `setup_output.py` -- Create output directory structure

**Process:**
1. Parse workflow inputs (brand_profile_path, weekly_theme, post_plan, reference_links, publishing_mode)
2. Load and validate brand_profile.json against required schema
3. Validate post_plan structure (at least one post type specified)
4. Parse reference_links array (optional)
5. Validate publishing_mode is either `auto_publish` or `content_pack_only`
6. Initialize output directory: `output/instagram/{YYYY-MM-DD}/`
7. Write validated inputs to `validated_inputs.json`

**Outputs:** `validated_inputs.json`, output directory initialized

**Failure Mode:** Missing required fields, invalid JSON, brand_profile.json not found, invalid publishing_mode

**Fallback:** Halt workflow with clear error message listing missing/invalid inputs. DO NOT proceed with incomplete inputs.

---

### 2. Reference Content Extraction

**Objective:** Fetch and extract clean content from reference URLs using Firecrawl, fall back to HTTP+BeautifulSoup if unavailable.

**Subagent:** `content-strategist`

**Tools:**
- `fetch_reference_content.py` -- Firecrawl scrape with HTTP fallback

**Process:**
1. Read reference_links from validated inputs
2. For each URL:
   - Try Firecrawl API first (markdown extraction)
   - On failure, fall back to HTTP GET + BeautifulSoup
   - Extract clean text content
   - Capture metadata (title, description)
3. Handle failures gracefully (log and continue with available references)
4. Compile all extracted content into structured JSON
5. Write to `reference_content.json`

**Outputs:** `reference_content.json` with extracted text, metadata, success status per URL

**Failure Mode:** URL unreachable, paywall, timeout, invalid response

**Fallback:** Log failed URL, continue with available references. If ALL references fail, proceed without reference content (flag in strategy as 'no reference material'). Never halt due to reference failures.

---

### 3. Content Strategy Generation

**Objective:** Analyze brand voice, weekly theme, post plan, and reference content. Generate content strategy with per-post briefs, themes, posting schedule.

**Subagent:** `content-strategist`

**Tools:**
- `generate_content_strategy.py` -- LLM-powered strategy generation

**Process:**
1. Read validated inputs and reference content
2. Analyze brand profile (tone, target audience, preferences)
3. Synthesize weekly theme with brand voice
4. Extract key facts/details from reference content
5. Generate per-post content briefs based on post_plan:
   - One brief per reel
   - One brief per carousel
   - One brief per single image
   - Include series templates if specified
6. Create posting schedule (spread posts across 7 days per post_plan.posting_schedule)
7. Define content themes/pillars for the week
8. Write to `content_strategy.json`

**Outputs:** `content_strategy.json` with post_briefs (array), posting_schedule (array), content_themes (array)

**Failure Mode:** LLM API failure, insufficient context, unclear theme

**Fallback:** Retry once with simplified prompt. If fails again, halt and open GitHub Issue requesting human clarification of theme. Include available context in the issue.

---

### 4. Post Generation (Parallel with Agent Teams)

**Objective:** Generate complete content for all posts in parallel (if 3+ posts) using Agent Teams. Each teammate generates one post: hook, caption, CTA, hashtags, alt text, creative brief, image prompt.

**Coordinator:** Main agent (team lead) OR sequential execution if Agent Teams unavailable

**Subagents:** `copywriter-specialist`, `hashtag-specialist`, `creative-director` (if sequential)

**Tools:**
- `generate_post_content.py` -- Parallelized post generation with Agent Teams support

**Process:**

**If post count >= 3 AND Agent Teams enabled:**
1. Team lead reads content_strategy.json
2. Create task list (one task per post in post_plan)
3. Spawn teammates (one per post or batched if >10 posts)
4. Each teammate generates for ONE post:
   - Hook (attention-grabbing first 125 chars)
   - Full caption (brand voice matched, 125-300 words)
   - CTA from brand preferences
   - 8-12 hashtags (mix of broad/niche, no banned/generic)
   - Alt text (max 100 chars, descriptive)
   - Creative brief (what to show, how to shoot/design)
   - Image prompt (AI guidance: style, composition, mood)
5. Team lead collects all teammate outputs
6. Run consistency check (no duplicate hooks/captions across posts)
7. Merge into unified `generated_content.json`

**If post count < 3 OR Agent Teams unavailable:**
1. Main agent reads content_strategy.json
2. For each post brief in sequence:
   - Delegate to copywriter-specialist for hook, caption, CTA, alt_text
   - Delegate to hashtag-specialist for hashtag set
   - Delegate to creative-director for creative_brief and image_prompt
3. Compile all posts into `generated_content.json`

**Outputs:** `generated_content.json` with complete content for all posts (posts array with all fields)

**Failure Mode:** LLM API failure, teammate timeout, incomplete generation

**Fallback:** If Agent Teams fails, fall back to sequential generation. Log mode used (parallel vs sequential). If sequential also fails, retry failed post once, then halt with error detailing which posts failed.

---

### 5. Quality Review & Compliance Checks

**Objective:** Run multi-dimensional quality review: brand voice alignment, compliance (banned topics, prohibited claims), hashtag hygiene, format validation, claims verification.

**Subagent:** `reviewer-specialist`

**Tools:**
- `review_content.py` -- Multi-dimension scoring with structured LLM review

**Process:**
1. Load generated_content.json
2. Load brand_profile for compliance rules
3. Load reference_content for claims verification
4. Score across 5 dimensions (each 0-100):
   - **Brand Voice Alignment** (90-100: excellent, 80-89: good, <80: needs work)
     - Tone match (formal/casual/technical)
     - Audience fit (messaging resonates)
     - Emoji usage matches brand guidelines
   - **Compliance Checks** (100 required to pass)
     - No banned topics detected
     - No prohibited claims found
     - All CTAs are from approved list
   - **Hashtag Hygiene** (80+ to pass)
     - Count within brand preferences (8-12 per post)
     - No banned hashtags
     - Limit generic hashtags (#love, #instagood → flagged)
   - **Format Validation** (80+ to pass)
     - Caption length under 2200 chars per post
     - Alt text present for all posts
     - Creative briefs have sufficient detail
   - **Claims Verification** (100 required to pass)
     - All factual claims sourced from reference links
     - No unsupported statistics
     - No unverifiable guarantees
5. Calculate overall score (average of 5 dimensions)
6. Determine pass/fail: overall >= 80 AND compliance == 100 AND claims == 100
7. Generate detailed review_report.md with:
   - Overall score
   - Per-dimension breakdown
   - Specific issues flagged
   - Pass/fail decision
8. Write review_report.json (machine-readable) and review_report.md (human-readable)

**Outputs:** `review_report.json`, `review_report_{YYYY-MM-DD}.md` with scores, issues, pass/fail decision

**Failure Mode:** LLM API failure during review

**Fallback:** Retry review once with exponential backoff. If fails again, default to FAIL decision (conservative - do not auto-publish without review). Output content pack for manual review with warning about missing automated review.

---

### 6. Gate Decision: Auto-Publish vs Manual Content Pack

**Objective:** Check review_report overall score and publishing_mode. If score >= 80/100 AND mode = auto_publish: proceed to publish. Otherwise: generate manual content pack.

**Tools:**
- `gate_decision.py` -- Deterministic gate logic

**Process:**
1. Read review_report.json for overall_score and pass_fail
2. Read publishing_mode from validated inputs
3. Apply gate logic:
   - **IF** pass_fail == "PASS" AND publishing_mode == "auto_publish":
     - action = "publish"
     - rationale = "Quality gates passed, auto-publish enabled"
   - **ELSE IF** pass_fail == "FAIL":
     - action = "manual_pack"
     - rationale = f"Quality score {overall_score}/100 below threshold or compliance issues detected"
   - **ELSE** (publishing_mode == "content_pack_only"):
     - action = "manual_pack"
     - rationale = "Content pack only mode enabled, skipping auto-publish"
4. Write decision to `publish_decision.json`

**Outputs:** `publish_decision.json` with action (publish | manual_pack) and rationale

**Failure Mode:** None (deterministic logic)

**Fallback:** None (no failures possible)

---

### 7a. Auto-Publish to Instagram (if gate passes)

**Objective:** Format posts for Instagram Graph API, create media containers, execute publish API calls with retry logic, handle rate limiting, log results.

**Subagent:** `instagram-publisher`

**Tools:**
- `publish_to_instagram.py` -- Instagram Graph API integration

**Process:**
1. Read generated_content.json and publish_decision.json
2. Verify publish_decision.action == "publish"
3. Load Instagram credentials from environment (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID)
4. For each post in sequence:
   - Format caption (hook + body + CTA + hashtags, max 2200 chars)
   - **NOTE:** Media URLs must be publicly accessible HTTPS URLs. If media generation is not part of this system, creative_brief serves as manual guidance only.
   - Create media container via Graph API:
     - POST `/v{version}/{ig_user_id}/media`
     - Include: caption, media_url (if available), media_type
   - Wait for container to be ready
   - Publish media container via Graph API:
     - POST `/v{version}/{ig_user_id}/media_publish`
     - creation_id = container_id
   - Handle scheduling if posting_time is in the future
   - Log result (success: media_id + permalink, failure: error message)
   - Handle errors:
     - **429 Rate Limit**: Log, halt further publishing, include unpublished posts in manual pack
     - **Auth failure**: Log, halt, generate manual pack for all posts
     - **Media URL error**: Log, skip post, continue with others
5. Write publish_log.json with all publish results
6. Write publish_log_{YYYY-MM-DD}.json to output directory

**Outputs:** `publish_log_{YYYY-MM-DD}.json` with per-post publish results (media_ids, permalinks, errors)

**Failure Mode:** Rate limit (200 calls/hour), auth failure, media URL not accessible, API error

**Fallback:** On rate limit: log next retry time, halt publishing, generate manual pack for unpublished posts. On auth/media failure: halt, fall back to step 7b (manual content pack), log specific error. Include partial publish results in logs.

---

### 7b. Generate Manual Content Pack (if gate fails OR auto-publish fails)

**Objective:** Generate human-readable Markdown and JSON content packs, plus upload checklist with copy-paste ready captions, hashtags, posting times.

**Subagent:** `instagram-publisher`

**Tools:**
- `generate_content_pack.py` -- Markdown + JSON content pack generation
- `generate_upload_checklist.py` -- Copy-paste ready manual upload instructions

**Process:**
1. Read generated_content.json and review_report.json
2. Generate content_pack_{YYYY-MM-DD}.md:
   - Header with metadata (generated date, theme, brand, total posts)
   - For each post:
     - Post number and type (reel/carousel/single)
     - Posting time (formatted human-readable)
     - Hook (highlighted)
     - Full caption
     - CTA
     - Hashtags (formatted list)
     - Alt text
     - Creative brief
     - Image prompt
   - Footer with review summary
3. Write content_pack_{YYYY-MM-DD}.json (machine-readable copy)
4. Generate upload_checklist_{YYYY-MM-DD}.md:
   - Checklist format ([ ] checkboxes)
   - For each post:
     - Posting time
     - Caption (ready to copy-paste)
     - Hashtags (one block, copy-paste ready)
     - Alt text (separate field)
     - Creative brief reference
     - Image prompt reference
5. Write both files to output directory

**Outputs:** `content_pack_{YYYY-MM-DD}.md`, `content_pack_{YYYY-MM-DD}.json`, `upload_checklist_{YYYY-MM-DD}.md`

**Failure Mode:** File write failure

**Fallback:** Retry write once with exponential backoff. If fails again, log error and write to stdout so GitHub Actions captures it in logs. Outputs can be recovered from logs if filesystem write fails.

---

### 8. Update Latest Index & Archive

**Objective:** Update latest.md with links to current content pack. Commit all outputs to repo. Maintain rolling archive (keep last 12 weeks, delete older).

**Tools:**
- `update_latest_index.py` -- Update rolling index
- `archive_cleanup.py` -- Prune old archives

**Process:**
1. Read all output file paths from current run
2. Generate latest.md:
   - Header with current date and theme
   - Links to content pack (markdown + json)
   - Link to review report
   - Link to publish log (if exists)
   - Link to upload checklist (if exists)
   - Quick stats (total posts, overall score, publish status)
3. Write to `output/instagram/latest.md`
4. Run archive cleanup:
   - Scan `output/instagram/` for dated directories
   - Keep most recent 12 weeks of content packs
   - Delete directories older than 12 weeks
   - Log deletion summary
5. Stage outputs for commit:
   - `git add output/instagram/{YYYY-MM-DD}/`
   - `git add output/instagram/latest.md`
   - DO NOT use `git add -A`
6. Commit with message: "Weekly Instagram content pack - {YYYY-MM-DD}"
7. Push to remote

**Outputs:** Updated `latest.md`, pruned archives, committed outputs

**Failure Mode:** Git commit failure, file write failure

**Fallback:** Retry commit once with rebase if push fails. If fails again, outputs still exist locally (GitHub Actions artifacts preserve them). Log error but do not halt workflow.

---

### 9. Notification & Summary

**Objective:** Post summary to GitHub Issue (Agent HQ) or send Slack notification. Include links to outputs, review score, publish status.

**Tools:**
- `send_notification.py` -- GitHub comment or Slack message

**Process:**
1. Read review_report.json and publish_log.json (or upload_checklist path)
2. Compile summary:
   - Weekly theme
   - Total posts generated
   - Overall quality score
   - Publish status (auto-published X posts, manual pack for Y posts, or all manual)
   - Links to content pack, review report, and latest.md
   - Next steps for user (view content pack, upload manually if needed)
3. Determine notification target:
   - If triggered via Agent HQ (issue): Post GitHub comment on issue
   - If Slack webhook configured: Send Slack message
   - Fallback: Log summary to stdout (captured in GitHub Actions logs)
4. Send notification with formatted summary

**Outputs:** GitHub comment OR Slack message with summary + links

**Failure Mode:** Notification delivery failure (Slack API error, GitHub API error)

**Fallback:** Log notification failure. DO NOT halt workflow - outputs are committed to repo regardless of notification success. User can review outputs via GitHub directly.

---

## Failure Handling Summary

| Step | Failure Mode | Fallback |
|------|--------------|----------|
| Input Validation | Missing fields, invalid JSON | Halt with clear error (cannot proceed without valid inputs) |
| Reference Extraction | URL unreachable, timeout | Continue with available references; flag if all fail |
| Strategy Generation | LLM API failure | Retry once, then halt with issue requesting clarification |
| Post Generation | LLM API failure, Agent Teams timeout | Fall back to sequential, retry failed posts once |
| Quality Review | LLM API failure | Retry once, default to FAIL if fails (conservative) |
| Gate Decision | N/A | No failures (deterministic logic) |
| Auto-Publish | Rate limit, auth failure | Halt publishing, generate manual pack for remaining posts |
| Manual Pack | File write failure | Retry once, log to stdout if fails |
| Archive & Commit | Git commit failure | Retry with rebase once, log error if fails |
| Notification | Delivery failure | Log error, do not halt (outputs are in repo) |

---

## Execution Paths

### Path 1: CLI Execution (Local Development)

```bash
# Setup
export ANTHROPIC_API_KEY="sk-..."
export FIRECRAWL_API_KEY="fc-..."
export INSTAGRAM_ACCESS_TOKEN="..."  # Only if testing auto-publish
export INSTAGRAM_USER_ID="..."       # Only if testing auto-publish

# Run workflow
python tools/validate_inputs.py \
  --brand-profile-path config/brand_profile.json \
  --weekly-theme "Spring 2026 Product Launch" \
  --post-plan '{"reels": 3, "carousels": 2, "single_images": 2}' \
  --reference-links '[]' \
  --publishing-mode content_pack_only > validated_inputs.json

python tools/fetch_reference_content.py \
  --reference-links "$(jq -r '.reference_links' validated_inputs.json)" > reference_content.json

# ... continue with each tool in sequence
```

### Path 2: GitHub Actions (Scheduled or Manual Dispatch)

Trigger via:
- **Schedule**: Every Monday at 09:00 UTC (cron)
- **Manual**: Workflow dispatch with inputs
- **Agent HQ**: Issue labeled `instagram-content-request`

GitHub Actions runs the workflow, commits outputs, posts summary.

### Path 3: Agent HQ (Issue-Driven)

1. Open GitHub Issue with title: "Instagram Content Request: {Theme}"
2. Body includes inputs as YAML or JSON
3. Label issue: `instagram-content-request`
4. System triggers, processes, commits results
5. Agent comments on issue with summary + links
6. Close issue or request revisions

---

## Agent Teams Parallelization

**When:** Post count >= 3 AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` enabled

**How:**
- Team lead creates task list (one per post)
- Spawns teammates (one per post or batched)
- Each teammate generates one complete post
- Team lead merges results and runs consistency check

**Performance:**
- Sequential: ~10-15 seconds per post × 7 posts = 70-105 seconds
- Parallel: ~12-18 seconds total (5x wall-time speedup)
- Token cost: Identical (same number of LLM calls)

**Fallback:** If Agent Teams unavailable or fails, sequential execution produces identical output.

---

## Cost Estimates

**Per run (7 posts, auto-publish):**
- LLM calls: Strategy (1) + Posts (7) + Review (1) = 9 calls
- Average tokens per call: ~1,500 input, ~800 output
- Claude Sonnet 4 cost: ~$0.08-0.12 per run
- Firecrawl: $0.01-0.02 per reference URL
- Instagram API: Free (200 calls/hour limit)
- GitHub Actions: ~5-10 minutes = ~$0.008 (free tier: 2,000 min/month)

**Total: ~$0.10-0.15 per weekly content pack**

---

## Success Metrics

✅ Generates complete content packs with 3-10 posts
✅ Runs 5-dimensional quality review
✅ Auto-publishes to Instagram when quality gates pass and mode enabled
✅ Falls back to manual content packs when needed
✅ Outputs structured JSON + human-readable Markdown
✅ Maintains rolling archive with latest.md index
✅ System runs autonomously via GitHub Actions
✅ Results committed back to repo with clear naming
✅ All three execution paths work (CLI, GitHub Actions, Agent HQ)
