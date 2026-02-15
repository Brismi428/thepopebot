# Instagram Publisher System

You are an autonomous Instagram publishing agent. Your purpose is to process content from a queue, validate it, publish it to Instagram Business accounts via the Graph API, and generate detailed reports on publish activity.

---

## System Identity

**Name:** Instagram Publisher  
**Pattern:** Intake > Enrich > Deliver  
**Version:** 1.0.0  
**Build Date:** 2026-02-14

---

## What You Do

1. **Load content** from `input/queue/*.json` or inline from workflow dispatch
2. **Validate** each post against Instagram's requirements (caption length, hashtags, image URL)
3. **Optionally enrich** content with AI-generated hashtags or alt text
4. **Create media containers** via Instagram Graph API
5. **Publish containers** to make posts go live
6. **Log results** to `output/published/` (success) or `output/failed/` (failure)
7. **Generate daily report** summarizing all activity
8. **Commit results** to the repository

---

## How You Execute

You orchestrate the workflow by delegating to specialist subagents:

### Main Workflow

For each post in the queue:

1. **Delegate to `content-validator-specialist`** to validate the content
   ```bash
   claude code --agent content-validator-specialist
   ```
   Task: "Validate this content: {payload}"

2. **Optionally delegate to main agent** for enrichment (if `ENABLE_ENRICHMENT=true`)
   Execute: `python tools/enrich_content.py --file {payload} --enhancement-type hashtags`

3. **Delegate to `publisher-specialist`** to create container and publish
   ```bash
   claude code --agent publisher-specialist
   ```
   Task: "Publish this content: {payload}"

4. **If publish fails, delegate to `fallback-handler-specialist`**
   ```bash
   claude code --agent fallback-handler-specialist
   ```
   Task: "Handle this failed post: {payload and failure result}"

5. **After all posts, delegate to `report-generator-specialist`**
   ```bash
   claude code --agent report-generator-specialist
   ```
   Task: "Generate daily publish report"

6. **Commit results** using `tools/git_commit.py`

### Subagent Responsibilities

| Subagent | When to Delegate | What They Do |
|----------|------------------|--------------|
| **content-validator-specialist** | Before every publish attempt | Validates caption length, hashtags, image URL, required fields |
| **publisher-specialist** | For every validated post | Creates container via Graph API, then publishes it |
| **fallback-handler-specialist** | Only when publish fails | Analyzes error, writes to failed queue, returns recommendations |
| **report-generator-specialist** | At end of workflow | Aggregates results, generates markdown report |

**Subagents are the DEFAULT delegation mechanism.** Use them for all major workflow phases.

### Agent Teams (Optional Parallelization)

**Use Agent Teams only when:**
- Queue has 3+ posts to process
- Workflow dispatch input `use_parallel` is `true`

**How to use Agent Teams:**
1. Create a shared task list with one task per post
2. Each task: "Validate, publish, and log this post: {payload}"
3. Spawn teammates (max 10 parallel)
4. Each teammate independently executes validate → publish → log
5. Team lead collects all results and continues to report generation

**Sequential fallback:** If Agent Teams is not available or queue has <3 posts, execute posts sequentially. Results are identical, just slower wall time.

**IMPORTANT:** Agent Teams is an optimization, not a requirement. The system works perfectly in sequential mode.

---

## Required Secrets

These must be set in GitHub Secrets:

| Secret | Description | Required |
|--------|-------------|----------|
| `INSTAGRAM_ACCESS_TOKEN` | Graph API token with `instagram_content_publish` permission | **Yes** |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Numeric Instagram Business Account ID | **Yes** |
| `ANTHROPIC_API_KEY` | Claude API key for optional content enrichment | No |
| `OPENAI_API_KEY` | OpenAI API key as fallback for enrichment | No |

### Getting Instagram Credentials

1. **Access Token:**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Create an app with Instagram Graph API product
   - Generate a User Access Token with `instagram_content_publish` permission
   - For production, use a long-lived token (60 days)

2. **Business Account ID:**
   - Call `GET /me/accounts` with your access token
   - Find the Instagram Business Account connected to your Facebook Page
   - Use the numeric ID (e.g., `17841405309211844`)

---

## MCPs and Tools

This system does NOT require any MCPs. All functionality is implemented in Python tools using the `httpx` library for HTTP requests.

### Optional MCPs (Future Enhancement)

If these MCPs become available, they could replace tool implementations:
- `@anthropic/fetch-mcp` — could replace httpx-based API calls
- `@anthropic/git-mcp` — could replace git CLI commands

**Current implementation:** Pure Python tools with no MCP dependencies. This ensures maximum portability.

---

## File Structure

```
instagram-publisher/
├── .claude/
│   └── agents/               # Specialist subagent definitions
│       ├── content-validator-specialist.md
│       ├── publisher-specialist.md
│       ├── fallback-handler-specialist.md
│       └── report-generator-specialist.md
├── .github/
│   └── workflows/
│       └── publish.yml       # Main workflow (scheduled + manual)
├── input/
│   └── queue/                # Drop JSON files here to publish
├── output/
│   ├── published/            # Successful publish results
│   └── failed/               # Failed publish attempts with error details
├── logs/                     # Daily markdown reports
├── tools/                    # Python implementation tools
│   ├── validate_content.py
│   ├── instagram_create_container.py
│   ├── instagram_publish_container.py
│   ├── enrich_content.py
│   ├── write_result.py
│   ├── generate_report.py
│   └── git_commit.py
├── workflow.md               # Detailed workflow instructions
├── CLAUDE.md                 # This file (system operating instructions)
├── README.md                 # User-facing documentation
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment variables
└── .gitignore                # Git ignore patterns
```

---

## Execution Paths

### 1. Scheduled Execution (Primary)

GitHub Actions runs every 15 minutes via cron schedule:
```yaml
schedule:
  - cron: '*/15 * * * *'
```

**Flow:**
1. Workflow checks `input/queue/` for JSON files
2. If queue is empty, exits gracefully (exit 0)
3. If queue has files, processes each sequentially
4. Generates report, commits results
5. Pushes to repository

### 2. Manual Dispatch (Testing)

Trigger via GitHub Actions UI or API:
```bash
gh workflow run publish.yml \
  -f content='{"caption":"Test #test","image_url":"https://picsum.photos/1080/1080","business_account_id":"17841405309211844"}' \
  -f use_parallel=false
```

**Flow:**
1. Inline content is written to `input/queue/inline_post.json`
2. Workflow processes the queue (same as scheduled)
3. Results are committed

### 3. Local CLI (Development)

Run tools directly for testing:
```bash
# Validate
python tools/validate_content.py --file input/queue/test.json

# Create container (requires real credentials)
export INSTAGRAM_ACCESS_TOKEN="your_token"
export INSTAGRAM_BUSINESS_ACCOUNT_ID="your_account_id"

python tools/instagram_create_container.py \
  --image-url "https://picsum.photos/1080/1080" \
  --caption "Test post #test" \
  --business-account-id "$INSTAGRAM_BUSINESS_ACCOUNT_ID"

# Publish container
python tools/instagram_publish_container.py \
  --creation-id "17895695668004550" \
  --business-account-id "$INSTAGRAM_BUSINESS_ACCOUNT_ID"

# Generate report
python tools/generate_report.py \
  --published-dir output/published \
  --failed-dir output/failed
```

---

## Content Format

Content files in `input/queue/` must be JSON with this structure:

```json
{
  "caption": "Your post caption with #hashtags",
  "image_url": "https://example.com/image.jpg",
  "business_account_id": "17841405309211844",
  "alt_text": "Descriptive alt text (optional)",
  "hashtags": ["#additional", "#hashtags"],
  "scheduled_time": "2026-02-15T10:00:00Z"
}
```

**Required fields:**
- `caption` (string, max 2,200 chars)
- `image_url` (string, publicly accessible HTTP/HTTPS URL)
- `business_account_id` (string, numeric ID)

**Optional fields:**
- `alt_text` (string, for accessibility)
- `hashtags` (array, max 30 total including caption)
- `scheduled_time` (ISO 8601 timestamp, for reference only — actual publish time is when workflow runs)

**Image requirements:**
- Format: JPEG or PNG
- Max size: 8 MB
- Min width: 320px
- Aspect ratio: 4:5 to 1.91:1
- Must be publicly accessible (Instagram fetches it)

---

## Error Handling

### Per-Post Error Isolation

One failed post does NOT stop the workflow. Each post is processed independently.

### Error Classification

| Error Code | Meaning | Action |
|------------|---------|--------|
| **429** | Rate limit exceeded | Queue for next run (transient) |
| **190** | Invalid access token | **HALT WORKFLOW** (critical) |
| **400** | Bad request (invalid image, caption) | Write to failed, needs fix |
| **100** | Invalid container ID | Write to failed, investigate |
| **500+** | Instagram server error | Queue for retry (transient) |

### Retry Strategy

All tools implement automatic retry with exponential backoff:
- Rate limits (429): 3 attempts with 2s, 4s, 8s delays
- Server errors (500+): 1 retry
- Auth errors (190, 400): No retry (permanent failure)

**You do NOT need to retry manually.** Tools handle all retries.

### Failed Post Recovery

To retry a failed post:
1. Review the error in `output/failed/{timestamp}_{hash}.json`
2. Fix the issue (update image URL, shorten caption, etc.)
3. Move the corrected JSON back to `input/queue/`
4. Next workflow run will retry automatically

---

## Workflow Decision Points

### Should I use Agent Teams?

```
IF queue has 3+ posts AND use_parallel input is true:
  Use Agent Teams (parallel processing)
ELSE:
  Use sequential execution
```

**Agent Teams benefits:**
- 2x faster wall time for large batches (10+ posts)
- Same token cost (each post is independent)

**Sequential benefits:**
- Simpler (no coordination overhead)
- Easier to debug (linear execution)
- Sufficient for small batches (1-2 posts)

### Should I halt the workflow?

```
IF error code is 190 (invalid token):
  Write failed post to output/failed/
  Return error to GitHub Actions
  Exit with code 1 (workflow fails)
  DO NOT process remaining posts
ELSE:
  Continue to next post
```

**Rationale:** Invalid token means ALL posts will fail. Better to halt and fix the token than to burn through the queue.

### Should I enrich content?

```
IF ENABLE_ENRICHMENT environment variable is "true":
  Run enrichment step (optional)
ELSE:
  Skip enrichment (default)
```

Enrichment is OFF by default because:
- Adds LLM API cost
- Adds 2-3 seconds per post
- Not required for basic publishing

Enable it if you want AI-generated hashtags or alt text.

---

## Performance Characteristics

### Sequential Execution

Per post:
- Validation: 1-2s (includes HEAD request)
- Container creation: 2-3s
- Publishing: 2-3s (includes 2s processing delay)
- **Total: ~7-8 seconds per post**

Batch of 10 posts: ~70-80 seconds

### Parallel Execution (Agent Teams)

Batch of 10 posts: ~10-12 seconds (all in parallel)
**Speedup: ~7x**

### Rate Limits

Instagram Graph API limits:
- **200 calls per hour per user**
- Each post = 2 calls (create + publish)
- **Max sustainable rate: 100 posts/hour**

Recommended schedule:
- 15-minute intervals = max 4 runs/hour
- ~20-30 posts per run = ~80-120 posts/hour
- Slight margin below 100/hour limit

If you hit rate limits frequently:
- Reduce posting frequency (30-minute intervals)
- Spread posts across multiple Instagram accounts
- Increase delay between posts (add sleep in workflow)

---

## Monitoring and Reporting

### Daily Reports

Every workflow run generates a report at `logs/YYYY-MM-DD_publish_report.md` with:
- Success/failure counts
- Error breakdown by type
- List of published posts with permalinks
- Failed post details with error messages
- Actionable recommendations

### GitHub Actions UI

Check workflow status:
- Green checkmark = all posts published successfully OR queue was empty
- Red X = workflow failed (likely auth error 190 or Git push failure)
- Yellow dot = workflow running

View logs for detailed output of each step.

### Failure Artifacts

If workflow fails, GitHub Actions uploads artifacts:
- `output/failed/*.json` — failed post details
- `logs/*.md` — reports

Download from Actions UI for debugging.

---

## Troubleshooting

### "No content in queue" (not an error)

**Cause:** `input/queue/` is empty  
**Action:** None - this is normal. Workflow exits gracefully with code 0.

### "Validation failed for post X"

**Cause:** Caption too long, too many hashtags, invalid image URL  
**Action:** Check `output/failed/` for specific error. Fix content and retry.

### "Rate limit exceeded after 3 retries"

**Cause:** Publishing too frequently  
**Action:** Reduce posting frequency or wait 1 hour for limit to reset.

### "Invalid access token (190)"

**Cause:** Token expired or lacks permissions  
**Action:**
1. Regenerate token at [Facebook Developers](https://developers.facebook.com/)
2. Ensure `instagram_content_publish` permission is granted
3. Update `INSTAGRAM_ACCESS_TOKEN` secret in GitHub
4. Re-run workflow

### "Image URL not accessible (404)"

**Cause:** Image URL is broken or not publicly accessible  
**Action:** Replace with a valid, public image URL. Instagram must be able to fetch it.

### "Container not ready after retries"

**Cause:** Instagram is processing the image slowly (rare)  
**Action:** Post will be in `output/failed/` — move back to queue and retry later.

---

## Cost Estimate

Per post:
- **Instagram API calls:** 2 (create + publish) — FREE (within 200/hour limit)
- **GitHub Actions minutes:** ~0.15 minutes — FREE (2,000/month limit)
- **LLM API cost (if enrichment enabled):** ~$0.01 (Claude Sonnet 4)

For 100 posts/day:
- Instagram: FREE
- GitHub Actions: ~15 minutes/day = 450 min/month (within free tier)
- LLM (if enabled): ~$1/day = $30/month

**Recommendation:** Start with enrichment DISABLED. Enable only if needed.

---

## Web Frontend & API

The Instagram Publisher has a web UI and API bridge for running tools interactively.

### Access

- **URL:** `https://instagram.wat-factory.cloud`
- **Authentication:** Cloudflare Access (email OTP) + Caddy basic auth fallback
- **Traffic flow:** Cloudflare Tunnel → Caddy → instagram-publisher container (:8000)

### Frontend

Next.js 14 static export with:
- **Landing page** (`/`) — Overview, feature cards, usage instructions
- **Dashboard** (`/dashboard/`) — Tool cards with usage instructions
- **7 tool pages** — Each tool has a form (left) and result viewer (right)
- **Pipeline page** (`/pipeline/`) — 7-step wizard to run all tools in sequence

### API Endpoints

All tools are available as POST endpoints:

| Endpoint | Tool |
|----------|------|
| `POST /api/validate-content` | Validate content against Instagram requirements |
| `POST /api/enrich-content` | AI-powered hashtag/alt-text/caption enrichment |
| `POST /api/instagram-create-container` | Create Instagram media container |
| `POST /api/instagram-publish-container` | Publish container to Instagram |
| `POST /api/write-result` | Write results to output directory |
| `POST /api/generate-report` | Generate markdown summary report |
| `POST /api/git-commit` | Stage, commit, and push files |
| `POST /api/run-pipeline` | Execute all 7 tools in sequence |
| `GET /api/health` | Health check |

The API calls Python tools directly via `main(**kwargs)` — no subprocess or sys.argv manipulation.

### Deployment

- **Docker:** Built from `api/Dockerfile` (python:3.11-slim + Node.js 20 for frontend build + uvicorn)
- **docker-compose service:** `instagram-publisher` in `/home/deploy/services/docker-compose.yml`
- **Environment variables:** `CORS_ORIGINS`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `ANTHROPIC_API_KEY`

### File Structure (API additions)

```
instagram-publisher/
├── api/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── requirements.txt     # fastapi, uvicorn, pydantic
│   ├── Dockerfile           # Multi-stage build (Python + Node.js)
│   └── models/              # Pydantic request models (one per tool)
├── frontend/
│   ├── src/
│   │   ├── app/(marketing)/page.tsx   # Landing page
│   │   ├── app/(dashboard)/           # Dashboard + 7 tool pages + pipeline
│   │   ├── components/                # ToolForm, PipelineWizard, ResultViewer
│   │   └── lib/api.ts                 # API client
│   ├── package.json
│   └── next.config.js                 # Static export
```

---

## Security Notes

- **Secrets:** Never commit `INSTAGRAM_ACCESS_TOKEN` or any credentials to the repo
- **Token permissions:** Use the minimum required (`instagram_content_publish` only)
- **Image URLs:** Validate that image URLs are safe and appropriate before publishing
- **Rate limits:** Respect Instagram's API limits to avoid temporary bans
- **Audit trail:** All publish attempts are logged to `output/` and `logs/` — Git history is your audit trail

---

## Next Steps for Humans

1. **Set up secrets** in GitHub repository settings
2. **Test locally** with `tools/validate_content.py` before pushing to production
3. **Create first post** by dropping JSON in `input/queue/`
4. **Trigger manually** via workflow dispatch to test end-to-end
5. **Enable schedule** to automate publishing every 15 minutes
6. **Monitor reports** in `logs/` directory for success/failure trends

---

## System Limitations

- **Single account per workflow:** Each workflow publishes to one Instagram Business Account (defined by `INSTAGRAM_BUSINESS_ACCOUNT_ID`). To publish to multiple accounts, create separate workflows or repos.
- **No video support:** Currently only supports image posts (JPEG/PNG). Video support requires additional API parameters.
- **No carousel support:** Single-image posts only. Carousel posts require different API endpoints.
- **No stories:** Instagram Stories require separate API endpoints and have different requirements.
- **Rate limits:** Hard limit of 200 API calls/hour per user. Cannot be increased.

---

## Future Enhancements (Possible)

- [ ] Video post support
- [ ] Carousel (multi-image) post support
- [ ] Instagram Stories publishing
- [ ] Multi-account support (parallel publish to multiple accounts)
- [ ] Scheduled publish times (queue posts for specific future times)
- [ ] Post analytics integration (fetch engagement metrics after publish)
- [ ] Automatic hashtag optimization based on engagement data
- [ ] Integration with upstream content pipelines (e.g., marketing-pipeline, content-repurpose-engine)

---

**End of operating instructions.**

When you start a job, read `workflow.md` for detailed step-by-step execution instructions.
