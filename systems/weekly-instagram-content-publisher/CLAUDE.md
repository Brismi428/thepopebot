# Weekly Instagram Content Publisher -- Operating Instructions

**System:** Weekly Instagram Content Publisher
**Version:** 1.0.0
**Purpose:** Automated Instagram content generation with brand voice compliance, quality review, and auto-publish or manual content pack delivery

---

## What This System Does

This system generates complete weekly Instagram content packs:
1. Takes brand voice guidelines, weekly theme, and post plan as input
2. Researches reference content from provided URLs
3. Generates content strategy with per-post briefs
4. Creates complete posts (hook, caption, CTA, hashtags, alt text, creative brief, image prompt)
5. Runs 5-dimensional quality review (brand voice, compliance, hashtags, format, claims)
6. Either auto-publishes to Instagram (if quality gates pass) or generates manual content pack
7. Commits results to repo with rolling archive

**User perspective:** Marketing teams open an issue or trigger a workflow with a weekly theme, and 5-10 minutes later receive a complete content pack that's either auto-published or ready for manual upload.

---

## Required Secrets

Configure these in GitHub Settings > Secrets and variables > Actions:

| Secret | Required | Purpose |
|--------|----------|---------|
| `ANTHROPIC_API_KEY` | **Yes** | Claude API for content generation and review |
| `FIRECRAWL_API_KEY` | Recommended | Web scraping for reference content (falls back to HTTP if missing) |
| `INSTAGRAM_ACCESS_TOKEN` | For auto-publish | Instagram Graph API long-lived token |
| `INSTAGRAM_USER_ID` | For auto-publish | Instagram Business Account ID |
| `SLACK_WEBHOOK_URL` | Optional | Slack notifications |
| `GITHUB_TOKEN` | Auto-provided | GitHub Actions built-in token |

**Getting Instagram credentials:**
1. Create Facebook App at https://developers.facebook.com
2. Add Instagram Graph API product
3. Generate User Access Token with `instagram_basic`, `instagram_content_publish` permissions
4. Exchange for long-lived token (60-day expiry): https://developers.facebook.com/docs/instagram-basic-display-api/guides/long-lived-access-tokens
5. Get Instagram Business Account ID from Graph API Explorer

---

## Execution Paths

### Path 1: GitHub Actions (Recommended)

**Scheduled execution:**
- Runs every Monday at 09:00 UTC
- Uses default brand profile at `config/brand_profile.json`
- Generates standard post plan (3 reels, 2 carousels, 2 singles)
- Mode: `content_pack_only`

**Manual dispatch:**
1. Go to Actions > Generate Instagram Content
2. Click "Run workflow"
3. Fill inputs:
   - Brand profile path (default: `config/brand_profile.json`)
   - Weekly theme (e.g., "Spring 2026 Product Launch")
   - Post plan JSON (e.g., `{"reels": 3, "carousels": 2, "single_images": 2}`)
   - Reference links JSON (optional, e.g., `[{"url": "https://example.com/blog"}]`)
   - Publishing mode (`content_pack_only` or `auto_publish`)
4. Click "Run workflow"

**Results:** Outputs committed to `output/instagram/{YYYY-MM-DD}/`, `latest.md` updated, workflow summary posted

### Path 2: Agent HQ (Issue-Driven)

**Trigger:**
1. Open GitHub Issue with title: "Instagram Content Request: {Theme}"
2. Body (YAML or JSON format):
   ```yaml
   weekly_theme: Spring 2026 Product Launch
   post_plan:
     reels: 3
     carousels: 2
     single_images: 2
   reference_links:
     - url: https://ecoflow.com/blog/solar-roof-launch
       purpose: product details
   publishing_mode: content_pack_only
   ```
3. Label issue: `instagram-content-request`
4. System triggers automatically

**Results:** Agent comments on issue with summary + links to content pack

### Path 3: Claude Code CLI (Local Development)

**Setup:**
```bash
# Clone repo
git clone <repo-url>
cd weekly-instagram-content-publisher

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-..."
export FIRECRAWL_API_KEY="fc-..."  # Optional
export INSTAGRAM_ACCESS_TOKEN="..."  # Only for auto-publish testing
export INSTAGRAM_USER_ID="..."       # Only for auto-publish testing
```

**Run workflow:**
```bash
# Read the workflow
claude workflow.md

# Or run tools manually
python tools/validate_inputs.py \
  --brand-profile-path config/brand_profile.json \
  --weekly-theme "Test Theme" \
  --post-plan '{"reels": 2, "carousels": 1, "single_images": 1}' \
  --reference-links '[]' \
  --publishing-mode content_pack_only \
  --output validated_inputs.json

python tools/setup_output.py --date $(date +%Y-%m-%d)

# Continue with each tool in sequence...
```

---

## Subagent Delegation

This system uses **6 specialist subagents** for delegation:

| Subagent | Responsibilities | When to Delegate |
|----------|------------------|------------------|
| `content-strategist` | Extract reference content, generate content strategy | Steps 2-3 (Reference Extraction, Strategy Generation) |
| `copywriter-specialist` | Write hooks, captions, CTAs, alt text | Step 4 (Post Generation, sequential mode) |
| `hashtag-specialist` | Generate optimized hashtag sets | Step 4 (Post Generation, sequential mode) |
| `creative-director` | Create creative briefs, image prompts | Step 4 (Post Generation, sequential mode) |
| `reviewer-specialist` | Run quality review across 5 dimensions | Step 5 (Quality Review & Compliance Checks) |
| `instagram-publisher` | Auto-publish or generate manual content packs | Steps 7a/7b (Auto-Publish or Manual Pack) |

**Delegation pattern:**
- Main agent orchestrates workflow steps
- Delegates to specialist subagents for domain-specific tasks
- Sequential execution is the default (subagents run one after another)
- Agent Teams can parallelize post generation (see below)

**How to delegate:**
```
# Example delegation to content-strategist
@content-strategist Please extract reference content from the URLs in validated_inputs.json
and generate a content strategy using tools/generate_content_strategy.py.
```

---

## Agent Teams Parallelization (Optional)

**When to use:** If post count >= 3 AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is enabled

**How it works:**
- Step 4 (Post Generation) can run in parallel
- Main agent (team lead) creates task list (one task per post)
- Spawns teammates (one per post or batched)
- Each teammate generates ONE complete post
- Team lead merges results and runs consistency check

**Performance:**
- Sequential: ~10-15 seconds per post × 7 posts = 70-105 seconds
- Parallel: ~12-18 seconds total (**5x wall-time speedup**)
- Token cost: **Identical** (same number of LLM calls)

**Fallback:** If Agent Teams is unavailable or fails, sequential generation produces identical output.

**Enable Agent Teams:**
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=true
```

---

## Workflow Steps (Sequential Execution)

### 1. Input Validation & Setup
- Tool: `validate_inputs.py`, `setup_output.py`
- Validates brand profile, post plan, publishing mode
- Creates output directory structure

### 2. Reference Content Extraction
- Tool: `fetch_reference_content.py`
- Delegate to: `content-strategist`
- Fetches content from reference URLs (Firecrawl + HTTP fallback)
- Graceful degradation if references fail

### 3. Content Strategy Generation
- Tool: `generate_content_strategy.py`
- Delegate to: `content-strategist`
- Analyzes brand voice, weekly theme, reference content
- Generates per-post briefs, posting schedule, content themes

### 4. Post Generation (Parallel or Sequential)
- Tool: `generate_post_content.py`
- Delegate to: Team lead (if Agent Teams) OR copywriter/hashtag/creative subagents (if sequential)
- Generates complete posts: hook, caption, CTA, hashtags, alt text, creative brief, image prompt
- **Parallel mode:** All posts generated simultaneously via Agent Teams
- **Sequential mode:** Posts generated one by one with subagent delegation

### 5. Quality Review & Compliance Checks
- Tool: `review_content.py`
- Delegate to: `reviewer-specialist`
- Scores across 5 dimensions: brand voice, compliance, hashtags, format, claims
- Returns overall score and pass/fail decision

### 6. Gate Decision
- Tool: `gate_decision.py`
- Deterministic logic (no subagent)
- Decides: auto-publish OR manual_pack

### 7a. Auto-Publish to Instagram (if gate passes)
- Tool: `publish_to_instagram.py`
- Delegate to: `instagram-publisher`
- Formats posts for Instagram Graph API
- Creates media containers, publishes, logs results
- Handles rate limiting and errors

### 7b. Generate Manual Content Pack (if gate fails OR auto-publish disabled)
- Tools: `generate_content_pack.py`, `generate_upload_checklist.py`
- Delegate to: `instagram-publisher`
- Generates Markdown + JSON content packs
- Creates copy-paste ready upload checklist

### 8. Update Latest Index & Archive
- Tools: `update_latest_index.py`, `archive_cleanup.py`
- Updates `latest.md` with links to current content pack
- Prunes old archives (12-week retention)
- Commits outputs to repo

### 9. Notification & Summary
- Tool: `send_notification.py`
- Posts summary to GitHub Issue or Slack
- Includes links to outputs, review score, publish status

---

## Quality Gates

Content must pass 3 critical checks to auto-publish:

1. **Overall Score >= 80/100** (average of 5 dimensions)
2. **Compliance Score == 100** (no banned topics, prohibited claims, unapproved CTAs)
3. **Claims Verification == 100** (all factual claims sourced from references)

**If any check fails:** System generates manual content pack for human review.

---

## Failure Handling

| Failure | System Behavior |
|---------|-----------------|
| Missing inputs | Halt with clear error message |
| Reference fetch failures | Continue with available references, flag if all fail |
| LLM API failure | Retry once, then halt or default to FAIL (conservative) |
| Quality gates not met | Generate manual content pack |
| Instagram rate limit | Halt publishing, generate manual pack for remaining posts |
| Instagram auth failure | Halt, generate manual pack for all posts |

**Philosophy:** Fail gracefully. Partial success is acceptable. Manual intervention is always an option.

---

## Output Structure

```
output/instagram/
├── latest.md                        # Rolling index (always points to most recent)
├── 2026-02-17/
│   ├── content_pack_2026-02-17.md   # Human-readable content pack
│   ├── content_pack_2026-02-17.json # Machine-readable content pack
│   ├── review_report.json           # Quality review results
│   ├── upload_checklist_2026-02-17.md # Manual upload instructions
│   └── publish_log_2026-02-17.json  # Instagram API results (if auto-publish)
└── 2026-02-24/
    └── ...
```

**Archive retention:** 12 weeks. Older content packs are automatically deleted.

---

## Cost Estimates

**Per run (7 posts, auto-publish):**
- LLM calls: Strategy (1) + Posts (7) + Review (1) = 9 calls
- Average tokens per call: ~1,500 input, ~800 output
- Claude Sonnet 4 cost: **~$0.08-0.12 per run**
- Firecrawl: $0.01-0.02 per reference URL
- Instagram API: Free (200 calls/hour limit)
- GitHub Actions: ~5-10 minutes = ~$0.008 (free tier: 2,000 min/month)

**Total: ~$0.10-0.15 per weekly content pack**

**Monthly cost (4 runs):** ~$0.40-0.60

---

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"
**Solution:** Add `ANTHROPIC_API_KEY` secret in GitHub Settings > Secrets

### Issue: "Brand profile not found"
**Solution:** Ensure `config/brand_profile.json` exists or specify correct path in inputs

### Issue: "Quality gates not met"
**Solution:** Review `review_report.json` for specific issues. Adjust brand profile or content strategy.

### Issue: "Rate limit exceeded (Instagram)"
**Solution:** Instagram Graph API allows 200 calls/hour. Wait or use manual content pack.

### Issue: "Access token expired (Instagram)"
**Solution:** Instagram long-lived tokens expire after 60 days. Generate new token and update secret.

### Issue: "All reference URLs failed"
**Solution:** Check URLs are publicly accessible. System will proceed without references (may impact content quality).

### Issue: "Post generation failed"
**Solution:** Check `generated_content.json` for error details. May be LLM API issue. Retry workflow.

---

## Extending the System

### Add New Post Types

1. Update `validate_inputs.py` to accept new post type
2. Update `post_plan` schema in brand profile
3. Update `generate_post_content.py` to handle new type
4. Update `creative-director` subagent with technical specs for new type

### Customize Quality Dimensions

1. Edit `review_content.py` scoring criteria
2. Update `reviewer-specialist` subagent instructions
3. Adjust pass/fail thresholds in `gate_decision.py`

### Add New Integrations

1. Create new tool (e.g., `publish_to_linkedin.py`)
2. Add secrets for new platform
3. Update workflow to call new tool after step 7b
4. Update `instagram-publisher` subagent or create new subagent

---

## Best Practices

1. **Test with content_pack_only mode first** before enabling auto_publish
2. **Review generated content** before committing to production
3. **Update brand profile regularly** to refine content quality
4. **Monitor quality scores** to identify improvement areas
5. **Archive old content packs** are kept for 12 weeks for historical reference
6. **Use Agent Teams** for 3+ posts to reduce execution time
7. **Provide reference links** when possible to improve content accuracy
8. **Check Instagram token expiry** every 60 days and refresh

---

## Support & Debugging

**Logs:** Check GitHub Actions workflow logs for detailed execution traces
**Review reports:** Read `review_report.json` for quality scores and issues
**Content packs:** Review generated content in `output/instagram/{YYYY-MM-DD}/`
**Issue tracking:** Open GitHub Issues labeled `instagram-content-request` for new requests
**Documentation:** Full workflow details in `workflow.md`

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
