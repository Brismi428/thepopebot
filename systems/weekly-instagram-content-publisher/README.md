# Weekly Instagram Content Publisher

An AI-powered social media content generation system that creates Instagram-ready content packs (captions, hashtags, creative briefs, image prompts) based on brand voice and weekly themes, runs multi-dimensional quality review checks, and either auto-publishes via Instagram Graph API or prepares manual upload packages.

**What it does:** Marketing teams describe a weekly theme, and 5-10 minutes later receive a complete content pack with 3-10 Instagram posts that's either auto-published or ready for manual upload.

---

## Features

✅ **Automated Content Generation**: Creates hooks, captions, CTAs, hashtags, alt text, creative briefs, and image prompts
✅ **Brand Voice Compliance**: Enforces brand guidelines, banned topics, prohibited claims
✅ **5-Dimensional Quality Review**: Brand voice, compliance, hashtag hygiene, format validation, claims verification
✅ **Auto-Publish or Manual**: Either publishes to Instagram Graph API or generates manual content packs
✅ **Rolling Archive**: 12-week retention with `latest.md` index
✅ **Three Execution Paths**: CLI, GitHub Actions, or Agent HQ (issue-driven)
✅ **Subagent Delegation**: 6 specialist subagents for focused domain expertise
✅ **Agent Teams Parallelization**: Optional 5x speedup for post generation

---

## Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd weekly-instagram-content-publisher
pip install -r requirements.txt
```

### 2. Configure Secrets

**For GitHub Actions (recommended):**
- Go to Settings > Secrets and variables > Actions
- Add required secrets (see [Required Secrets](#required-secrets))

**For local CLI:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Customize Brand Profile

Edit `config/brand_profile.json`:
```json
{
  "brand_name": "Your Brand",
  "tone": "friendly, professional",
  "target_audience": "your target audience description",
  "products": ["product1", "product2"],
  "banned_topics": ["politics", "religion"],
  "prohibited_claims": ["guaranteed", "miracle"],
  "preferred_cta": ["Learn more", "Shop now"],
  "emoji_style": "minimal (1-2 per post)",
  "hashtag_preferences": {
    "count": "8-12 per post",
    "avoid": ["generic", "spammy"]
  }
}
```

### 4. Run the System

**Option A: GitHub Actions (Scheduled)**
- Push to GitHub
- System runs automatically every Monday at 09:00 UTC
- Results committed to `output/instagram/{date}/`

**Option B: GitHub Actions (Manual)**
- Go to Actions > Generate Instagram Content
- Click "Run workflow"
- Fill inputs (theme, post plan, publishing mode)
- View results in `output/instagram/{date}/`

**Option C: Agent HQ (Issue-Driven)**
- Open GitHub Issue with label `instagram-content-request`
- Include theme and post plan in issue body (YAML or JSON)
- System triggers automatically
- Results posted as issue comment + committed to repo

**Option D: Local CLI**
```bash
export ANTHROPIC_API_KEY="sk-..."
export FIRECRAWL_API_KEY="fc-..."  # Optional

python tools/validate_inputs.py \
  --brand-profile-path config/brand_profile.json \
  --weekly-theme "Spring 2026 Product Launch" \
  --post-plan '{"reels": 3, "carousels": 2, "single_images": 2}' \
  --reference-links '[]' \
  --publishing-mode content_pack_only
```

---

## Required Secrets

| Secret | Required | Purpose |
|--------|----------|---------|
| `ANTHROPIC_API_KEY` | **Yes** | Claude API for content generation and review |
| `FIRECRAWL_API_KEY` | Recommended | Web scraping for reference content (falls back to HTTP) |
| `INSTAGRAM_ACCESS_TOKEN` | For auto-publish | Instagram Graph API long-lived token |
| `INSTAGRAM_USER_ID` | For auto-publish | Instagram Business Account ID |
| `SLACK_WEBHOOK_URL` | Optional | Slack notifications |

**Getting Instagram credentials:**
1. Create Facebook App: https://developers.facebook.com
2. Add Instagram Graph API product
3. Generate User Access Token with permissions: `instagram_basic`, `instagram_content_publish`
4. Exchange for long-lived token (60-day expiry): https://developers.facebook.com/docs/instagram-basic-display-api/guides/long-lived-access-tokens
5. Get Instagram Business Account ID from Graph API Explorer

---

## Workflow Overview

```
1. Input Validation → Parse inputs, load brand profile
2. Reference Extraction → Fetch content from URLs (Firecrawl + fallback)
3. Content Strategy → Generate per-post briefs, themes, schedule
4. Post Generation → Create hooks, captions, hashtags, creative briefs
5. Quality Review → Score across 5 dimensions (brand voice, compliance, etc.)
6. Gate Decision → Auto-publish OR manual content pack
7a. Auto-Publish → Publish to Instagram Graph API (if gates pass)
7b. Manual Pack → Generate markdown/JSON + upload checklist
8. Archive & Index → Update latest.md, prune old archives
9. Notification → Post summary to GitHub Issue or Slack
```

---

## Subagent Architecture

This system uses **6 specialist subagents** for delegation:

| Subagent | Responsibilities |
|----------|------------------|
| `content-strategist` | Extract reference content, generate content strategy |
| `copywriter-specialist` | Write hooks, captions, CTAs, alt text |
| `hashtag-specialist` | Generate optimized hashtag sets |
| `creative-director` | Create creative briefs, image prompts |
| `reviewer-specialist` | Run 5-dimensional quality review |
| `instagram-publisher` | Auto-publish or generate manual content packs |

**Delegation is the default.** Subagents handle domain-specific tasks, reducing complexity and improving maintainability.

---

## Agent Teams Parallelization (Optional)

**When:** Post count >= 3 AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` enabled

**Performance:**
- Sequential: ~70-105 seconds (7 posts × 10-15 sec each)
- Parallel: ~12-18 seconds (**5x wall-time speedup**)
- Token cost: Identical

**Enable:**
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=true
```

**Fallback:** If Agent Teams unavailable or fails, sequential execution produces identical output.

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

---

## Quality Gates

Content must pass **3 critical checks** to auto-publish:

1. **Overall Score >= 80/100** (average of 5 dimensions)
2. **Compliance Score == 100** (no banned topics, prohibited claims, unapproved CTAs)
3. **Claims Verification == 100** (all factual claims sourced from references)

**If any check fails:** System generates manual content pack for human review.

---

## Cost Estimates

**Per run (7 posts, auto-publish):**
- LLM calls: Strategy (1) + Posts (7) + Review (1) = 9 calls
- Claude Sonnet 4 cost: **~$0.08-0.12 per run**
- Firecrawl: $0.01-0.02 per reference URL
- Instagram API: Free (200 calls/hour limit)
- GitHub Actions: ~5-10 minutes (~$0.008, free tier: 2,000 min/month)

**Total: ~$0.10-0.15 per weekly content pack**
**Monthly cost (4 runs): ~$0.40-0.60**

---

## Troubleshooting

### Quality Gates Not Met
- **Check:** `review_report.json` for specific issues
- **Fix:** Adjust brand profile or reference content

### Instagram Rate Limit Exceeded
- **Cause:** 200 calls/hour limit
- **Fix:** Wait 1 hour or use `content_pack_only` mode

### Reference URLs Failed
- **Cause:** Paywall, timeout, or unreachable URL
- **Fix:** System continues with available references (may impact quality)

### Access Token Expired
- **Cause:** Instagram long-lived tokens expire after 60 days
- **Fix:** Generate new token and update `INSTAGRAM_ACCESS_TOKEN` secret

### Post Generation Failed
- **Check:** `generated_content.json` for error details
- **Fix:** Retry workflow (may be transient LLM API issue)

---

## Extending the System

### Add New Post Types
1. Update `validate_inputs.py` to accept new type
2. Update `generate_post_content.py` with new type logic
3. Update `creative-director` subagent with technical specs

### Customize Quality Dimensions
1. Edit `review_content.py` scoring criteria
2. Update `reviewer-specialist` subagent instructions
3. Adjust pass/fail thresholds in `gate_decision.py`

### Add New Integrations
1. Create new tool (e.g., `publish_to_linkedin.py`)
2. Add platform secrets
3. Update workflow to call new tool
4. Create new subagent or extend `instagram-publisher`

---

## Best Practices

✅ Test with `content_pack_only` mode before enabling `auto_publish`
✅ Review generated content before committing to production
✅ Update brand profile regularly to refine quality
✅ Monitor quality scores to identify improvement areas
✅ Use Agent Teams for 3+ posts to reduce execution time
✅ Provide reference links when possible for better accuracy
✅ Refresh Instagram token every 60 days

---

## Documentation

- **CLAUDE.md** - Detailed operating instructions for Claude Code
- **workflow.md** - Complete workflow specification
- **.claude/agents/** - Subagent definitions

---

## License

MIT License - See LICENSE file for details

---

## Support

**Issues:** Open GitHub Issue with label `instagram-content-request` for new content requests
**Bugs:** Open GitHub Issue with label `bug`
**Documentation:** Read `CLAUDE.md` and `workflow.md`
**Logs:** Check GitHub Actions workflow logs for detailed execution traces
