# Instagram Publisher

> **Automated Instagram content publishing system with Graph API integration and intelligent fallback handling.**

Autonomous system for publishing content to Instagram Business accounts via the Graph API. Processes a queue of posts, validates them, publishes to Instagram, and generates detailed reports — all running autonomously via GitHub Actions.

---

## Features

✅ **Automated Publishing** — Drop JSON files in `input/queue/`, system publishes automatically  
✅ **Content Validation** — Pre-publish checks for caption length, hashtags, image URLs  
✅ **Intelligent Retry** — Exponential backoff for rate limits, no retry for permanent errors  
✅ **Error Isolation** — One failed post doesn't stop the batch  
✅ **Detailed Reporting** — Daily markdown reports with success/failure breakdown  
✅ **Optional AI Enrichment** — Claude/OpenAI can suggest hashtags or generate alt text  
✅ **Git-Native State** — All results committed to repo, full audit trail  
✅ **Three Execution Paths** — Scheduled (cron), manual dispatch, or local CLI

---

## Quick Start

### Prerequisites

1. Instagram Business Account connected to a Facebook Page
2. Facebook Developer App with Instagram Graph API product
3. GitHub repository with this system
4. GitHub Secrets configured (see Setup below)

### Setup

#### 1. Clone or Copy This System

```bash
# If building from WAT Factory:
git clone <your-repo>
cd instagram-publisher

# If starting fresh:
# Copy this directory structure to your repo
```

#### 2. Configure Secrets

In GitHub repository settings → Secrets and variables → Actions, add:

| Secret | How to Get It |
|--------|---------------|
| `INSTAGRAM_ACCESS_TOKEN` | [Facebook Developers](https://developers.facebook.com/) → Your App → Tools → Graph API Explorer → Generate Access Token with `instagram_content_publish` permission |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Call `GET https://graph.facebook.com/me/accounts?access_token={your_token}` → Find Instagram Business Account ID |
| `ANTHROPIC_API_KEY` | (Optional) For content enrichment — [console.anthropic.com](https://console.anthropic.com/) |
| `OPENAI_API_KEY` | (Optional) Fallback LLM — [platform.openai.com](https://platform.openai.com/) |

**Getting Instagram Credentials (Detailed):**

```bash
# 1. Get Access Token
# Go to: https://developers.facebook.com/tools/explorer/
# Select your app → Add a permission → instagram_content_publish
# Generate Access Token (User Token)
# For production, generate a Long-Lived Token (60 days):

curl -X GET "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}"

# 2. Get Business Account ID
curl -X GET "https://graph.facebook.com/me/accounts?access_token={your-token}"
# Find the Instagram Business Account connected to your page
# Use the numeric 'id' field
```

#### 3. Install Dependencies (Local Development)

```bash
pip install -r requirements.txt
```

#### 4. Test Locally

```bash
# Create a test post
cat > input/queue/test.json << EOF
{
  "caption": "Test post from instagram-publisher #test #automation",
  "image_url": "https://picsum.photos/1080/1080",
  "business_account_id": "${INSTAGRAM_BUSINESS_ACCOUNT_ID}"
}
EOF

# Validate it
python tools/validate_content.py --file input/queue/test.json

# (Optional) Publish it manually
export INSTAGRAM_ACCESS_TOKEN="your_token"
export INSTAGRAM_BUSINESS_ACCOUNT_ID="your_account_id"

python tools/instagram_create_container.py \
  --image-url "https://picsum.photos/1080/1080" \
  --caption "Test post from instagram-publisher #test #automation" \
  --business-account-id "$INSTAGRAM_BUSINESS_ACCOUNT_ID"

# If successful, you'll get a creation_id
# Then publish:
python tools/instagram_publish_container.py \
  --creation-id "YOUR_CREATION_ID" \
  --business-account-id "$INSTAGRAM_BUSINESS_ACCOUNT_ID"
```

#### 5. Enable Automated Publishing

Push to GitHub and enable Actions:

```bash
git add .
git commit -m "Set up Instagram Publisher"
git push origin main
```

The workflow will run:
- **Every 15 minutes** (processes queue automatically)
- **On manual trigger** (via GitHub Actions UI or API)

---

## Usage

### Publishing via Queue

**1. Create a content file:**

```json
{
  "caption": "Amazing sunset over the mountains 🌄 #nature #sunset #photography",
  "image_url": "https://example.com/sunset.jpg",
  "business_account_id": "17841405309211844"
}
```

**2. Save to `input/queue/`:**

```bash
# Example: Via GitHub web UI
# - Navigate to input/queue/
# - Click "Add file" → "Create new file"
# - Name it: my-post.json
# - Paste JSON content
# - Commit

# Example: Via Git
echo '{...}' > input/queue/sunset-post.json
git add input/queue/sunset-post.json
git commit -m "Add sunset post to queue"
git push
```

**3. Wait for next scheduled run (up to 15 minutes)**

Or trigger immediately:

```bash
gh workflow run publish.yml
```

**4. Check results:**

- Success: `output/published/{timestamp}_{post_id}.json` + post is live on Instagram
- Failure: `output/failed/{timestamp}_{hash}.json` with error details
- Report: `logs/{date}_publish_report.md` with full summary

### Manual Dispatch with Inline Content

```bash
# Publish immediately without queue file
gh workflow run publish.yml \
  -f content='{"caption":"Quick post #test","image_url":"https://picsum.photos/1080/1080","business_account_id":"17841405309211844"}'
```

### Batch Processing with Agent Teams (Parallel)

```bash
# For large batches (10+ posts), use parallel processing
gh workflow run publish.yml -f use_parallel=true
```

**Note:** Agent Teams provides 2x speedup for batches of 3+ posts, but is optional. Sequential mode is the default.

---

## Content Format

### Required Fields

```json
{
  "caption": "Your post text (max 2,200 chars) #hashtags",
  "image_url": "https://example.com/image.jpg",
  "business_account_id": "17841405309211844"
}
```

### Optional Fields

```json
{
  "caption": "...",
  "image_url": "...",
  "business_account_id": "...",
  "alt_text": "Descriptive text for screen readers",
  "hashtags": ["#additional", "#tags"],
  "scheduled_time": "2026-02-15T10:00:00Z"
}
```

**Note:** `scheduled_time` is for reference only. The post publishes when the workflow runs, not at the scheduled time.

### Image Requirements

- **Format:** JPEG or PNG only
- **Size:** Max 8 MB
- **Dimensions:** Min 320px width
- **Aspect Ratio:** 4:5 to 1.91:1 (vertical to landscape)
- **Accessibility:** Must be publicly accessible (Instagram fetches the image from the URL)

### Content Validation Rules

- ✅ Caption ≤ 2,200 characters
- ✅ Max 30 hashtags (combined from `caption` and `hashtags` array)
- ✅ Image URL must return 200 status (HEAD request)
- ✅ Image Content-Type must be `image/jpeg` or `image/png`
- ✅ `business_account_id` must be numeric

Invalid posts are written to `output/failed/` with specific error details.

---

## Workflow Architecture

### System Components

```
input/queue/          → Content to publish (JSON files)
    ↓
tools/validate_content.py → Pre-publish validation
    ↓
tools/instagram_create_container.py → Create media container (Step 1)
    ↓
tools/instagram_publish_container.py → Publish container (Step 2)
    ↓
output/published/ OR output/failed/ → Results
    ↓
tools/generate_report.py → Daily summary report
    ↓
logs/{date}_publish_report.md → Readable report
    ↓
Git commit + push → Audit trail
```

### Specialist Subagents

The system uses 4 specialist subagents for delegation:

| Subagent | Responsibility |
|----------|----------------|
| **content-validator-specialist** | Validates posts before publishing |
| **publisher-specialist** | Handles Instagram Graph API operations |
| **fallback-handler-specialist** | Manages failed posts and retry decisions |
| **report-generator-specialist** | Generates daily summary reports |

Subagents are the **default delegation mechanism** for all major workflow phases.

### Error Handling Strategy

| Error Type | Code | Action |
|------------|------|--------|
| Rate limit exceeded | 429 | Retry with exponential backoff (3x) → Queue for next run if fails |
| Invalid token | 190 | **HALT WORKFLOW** immediately (all posts will fail) |
| Bad request | 400 | Write to failed, no retry (needs content fix) |
| Invalid container | 100 | Write to failed, no retry (investigate) |
| Server error | 500-504 | Retry once → Queue for next run if fails |

**Per-post error isolation:** One failed post does NOT stop the batch. The workflow continues processing remaining posts.

---

## Monitoring & Reporting

### Daily Reports

Every run generates `logs/YYYY-MM-DD_publish_report.md` with:

```markdown
# Instagram Publish Report - 2026-02-14

## Summary
- Total attempts: 15
- Successful: 13 (86.7%)
- Failed: 2

## Published Posts
| Time | Post ID | Caption |
|------|---------|---------|
| 10:15:32 | [17899999999](https://instagram.com/p/ABC/) | Amazing sunset... |
...

## Failed Posts
### Error Breakdown
- 429: 1 occurrence(s)
- 400: 1 occurrence(s)

### Details
| Time | Error Code | Message | Caption |
|------|------------|---------|---------|
| 11:30:15 | 429 | Rate limit exceeded | Product launch... |
...

## Recommendations
⚠️ 1 rate limit error detected. Consider reducing frequency...
```

### GitHub Actions Status

- ✅ **Green checkmark:** All posts published OR queue was empty
- ❌ **Red X:** Workflow failed (auth error or Git push failure)
- 🟡 **Yellow dot:** Workflow running

### Failure Artifacts

On workflow failure, GitHub Actions uploads:
- `output/failed/*.json` — Failed post details
- `logs/*.md` — Reports

Download from Actions UI → Run details → Artifacts

---

## Troubleshooting

### Common Issues

#### "No content in queue"

**Not an error.** Workflow exits gracefully when queue is empty.

#### "Validation failed: Caption exceeds 2,200 character limit"

**Fix:** Shorten caption or move some content to comments.

**Location:** `output/failed/` has specific error details.

#### "Rate limit exceeded after 3 retries"

**Cause:** Publishing too frequently (200 calls/hour limit).

**Fix:**
- Reduce posting frequency (30-minute intervals instead of 15)
- Wait 1 hour for limit to reset
- Spread posts across multiple accounts

#### "Invalid access token (190)"

**Cause:** Token expired or lacks permissions.

**Fix:**
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Regenerate token with `instagram_content_publish` permission
3. Update `INSTAGRAM_ACCESS_TOKEN` secret in GitHub
4. Re-run workflow

#### "Image URL not accessible: returned 404"

**Cause:** Image URL is broken or not publicly accessible.

**Fix:** Replace with valid, public URL. Test it in a browser first.

#### "Container not ready after retries"

**Cause:** Instagram is processing the image slowly (rare).

**Fix:** Post is in `output/failed/` — move back to `input/queue/` and retry later.

### Debug Mode

Enable detailed logging:

```bash
# In GitHub Actions workflow
# Add to env section:
DEBUG: true
PYTHONUNBUFFERED: 1
```

---

## Performance & Costs

### Execution Time

**Per post:**
- Validation: 1-2s
- Container creation: 2-3s
- Publishing: 2-3s (includes 2s processing delay)
- **Total: ~7-8 seconds**

**Batch of 10 posts:**
- Sequential: ~70-80 seconds
- Parallel (Agent Teams): ~10-12 seconds (7x faster)

### API Rate Limits

- **Instagram Graph API:** 200 calls/hour per user
- Each post = 2 API calls (create + publish)
- **Max sustainable rate:** ~100 posts/hour

**Recommended schedule:**
- 15-minute intervals = max 4 runs/hour
- ~20-30 posts per run = ~80-120 posts/hour
- Slight margin below limit to avoid errors

### Cost Estimate

**Per 100 posts/day:**

| Service | Usage | Cost |
|---------|-------|------|
| Instagram API | 200 calls | **FREE** (within limit) |
| GitHub Actions | ~15 minutes | **FREE** (2,000 min/month free tier) |
| LLM (if enrichment enabled) | 100 API calls | ~$1/day = $30/month |

**Recommendation:** Start with enrichment **DISABLED**. Enable only if you need AI-generated hashtags/alt text.

---

## Security

- ✅ **Secrets managed via GitHub Secrets** (never committed to repo)
- ✅ **Minimal token permissions** (`instagram_content_publish` only)
- ✅ **Audit trail** (Git history logs all publish attempts)
- ✅ **Per-post validation** (catches invalid/unsafe content before API call)
- ✅ **Rate limit respect** (automatic backoff to avoid temporary bans)

**Best practices:**
- Use long-lived tokens (60 days) from Facebook
- Rotate tokens regularly (before expiry)
- Monitor `logs/` for suspicious activity
- Validate image URLs before adding to queue

---

## Limitations

- **Single account per repo** — To publish to multiple Instagram accounts, create separate repos or workflows
- **Image posts only** — No video or carousel support (yet)
- **No Instagram Stories** — Separate API required
- **No scheduled publish** — Posts publish when workflow runs, not at a specific future time
- **Rate limits** — Hard limit of 200 API calls/hour (cannot be increased)

---

## Roadmap

Possible future enhancements:

- [ ] Video post support
- [ ] Carousel (multi-image) posts
- [ ] Instagram Stories publishing
- [ ] Multi-account support (parallel publish to multiple accounts)
- [ ] Scheduled publish times (hold posts until specific time)
- [ ] Post analytics (fetch engagement metrics after publish)
- [ ] Automatic hashtag optimization based on engagement
- [ ] Integration with marketing-pipeline for lead gen

---

## Contributing

This system was generated by the [WAT Systems Factory](https://github.com/yourorg/wat-factory). To modify:

1. **For tool changes:** Edit Python files in `tools/`
2. **For workflow changes:** Edit `workflow.md` and regenerate via factory
3. **For subagent changes:** Edit `.claude/agents/*.md`
4. **For GitHub Actions changes:** Edit `.github/workflows/publish.yml`

Run tests after changes:
```bash
# Level 1: Syntax check
python -m py_compile tools/*.py

# Level 2: Unit tests
python tools/validate_content.py --file input/queue/test.json

# Level 3: Integration test (requires credentials)
# See PRP validation section for full test suite
```

---

## Support

- **Issues:** Open an issue in this repository
- **Documentation:** See `CLAUDE.md` for detailed system internals
- **Workflow Details:** See `workflow.md` for step-by-step execution
- **WAT Factory:** [github.com/yourorg/wat-factory](https://github.com/yourorg/wat-factory)

---

## License

[Your License Here]

---

**Built with ❤️ by the WAT Systems Factory**
