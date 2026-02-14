# Instagram Publisher - Workflow

**System Purpose:** Automated Instagram content publishing with Graph API integration and intelligent fallback handling for failed posts.

**Pattern:** Intake > Enrich > Deliver

---

## Inputs

- **content_payload** (JSON) -- Instagram post content from `input/queue/*.json` or `workflow_dispatch` input
  - Required fields: `caption`, `image_url`, `business_account_id`
  - Optional fields: `alt_text`, `hashtags`, `scheduled_time`
- **publishing_schedule** (cron) -- Schedule for processing queue (default: every 15 minutes)
- **use_parallel** (boolean) -- Use Agent Teams for batch processing (default: false)

## Outputs

- **output/published/{timestamp}_{post_id}.json** -- Successful publish results with post ID and permalink
- **output/failed/{timestamp}_{hash}.json** -- Failed publish results with error details and retry count
- **logs/{date}_publish_report.md** -- Daily summary of all publish attempts

---

## Workflow Steps

### 1. Load Content Queue

**Description:** Read all JSON files from `input/queue/` or parse inline content from workflow dispatch.

**Delegate to:** Main agent (no subagent needed for simple file listing)

**Tools:** `bash` (ls, cat), `filesystem`

**Actions:**
1. Check if `input/queue/` directory exists and has JSON files
2. If files exist, read and parse each JSON file
3. If workflow dispatch provided `inputs.content`, parse that instead
4. Build list of content payloads to process

**Outputs:** List of content payload dictionaries

**Failure Mode:** No files in queue and no inline content provided

**Fallback:** Log info message "No content to publish" and exit 0 (silent success). This is not an error -- it means the queue is empty.

---

### 2. Validate Content

**Description:** For each content payload, validate caption length, hashtag count, image URL format, and API requirements.

**Delegate to:** `content-validator-specialist`

**Delegation command:**
```bash
claude code --agent content-validator-specialist
```

**Task for subagent:**
"Validate the following content payload against Instagram API requirements: {payload}. Check caption length (max 2,200 chars), hashtag count (max 30), image URL accessibility (HEAD request), and required fields. Return validation report JSON."

**Tools used by subagent:** `bash`, `read`, `write`

**Actions:**
1. Check caption length ≤ 2,200 characters
2. Count hashtags (extract from caption or hashtags array), verify ≤ 30
3. Verify `image_url` is a valid HTTP/HTTPS URL
4. Send HEAD request to `image_url` to verify accessibility (200 status)
5. Verify `business_account_id` is present and numeric
6. Check image format from Content-Type header (must be image/jpeg or image/png)
7. Return validation report: `{is_valid: bool, errors: list, warnings: list}`

**Outputs:** Validation report JSON for each content payload

**Failure Mode:** Validation fails (invalid image URL, caption too long, missing required fields)

**Fallback:** Skip invalid posts, log detailed errors to stderr, continue processing valid posts. Invalid posts are written to `output/failed/` with validation errors.

---

### 3. Enrich Metadata (Optional)

**Description:** Optionally enhance content with hashtag analysis, alt text generation, or caption improvements using Claude.

**Delegate to:** Main agent (optional step, can be skipped)

**Tools:** `tools/enrich_content.py`

**Actions:**
1. For each validated content payload, check if enrichment is requested (environment variable `ENABLE_ENRICHMENT=true`)
2. If enabled, call `tools/enrich_content.py` with payload and enhancement type
3. Enhancement types: `hashtags` (suggest additional relevant hashtags), `alt_text` (generate from image URL), `caption` (improve for engagement)
4. Merge enriched fields back into content payload

**Outputs:** Enhanced content payloads with additional metadata

**Failure Mode:** Enrichment API call fails (Claude or OpenAI unavailable)

**Fallback:** Skip enrichment, log warning, proceed with original content. Enrichment is a nice-to-have, not a blocker.

---

### 4. Create Media Container

**Description:** For each validated post, call Instagram Graph API to create a media container with the image URL and caption.

**Delegate to:** `publisher-specialist`

**Delegation command:**
```bash
claude code --agent publisher-specialist
```

**Task for subagent:**
"Create Instagram media container for: {payload}. Use Graph API endpoint POST /{business_account_id}/media with image_url and caption. Return container creation_id or error details."

**Tools used by subagent:** `bash`, `read`, `write`

**Actions:**
1. Call `tools/instagram_create_container.py` with:
   - `image_url` from payload
   - `caption` from payload
   - `business_account_id` from payload or environment
   - `access_token` from `INSTAGRAM_ACCESS_TOKEN` secret
2. Tool makes POST request to `https://graph.facebook.com/v18.0/{business_account_id}/media`
3. Tool implements retry with exponential backoff (3 attempts)
4. Return container `creation_id` on success or error JSON on failure

**Outputs:** Container `creation_id` string

**Failure Mode:** API error (rate limit 429, invalid token 190, image fetch failure, invalid URL)

**Fallback:**
- **Rate limit (429):** Retry with exponential backoff (2s, 4s, 8s). If all 3 attempts fail, write to `output/failed/` with status "rate_limited" and continue to next post.
- **Invalid token (190):** Do NOT retry. Fail immediately, write to `output/failed/` with status "auth_failed", halt workflow (no point continuing).
- **Image fetch failure (400):** Do NOT retry. Write to `output/failed/` with status "image_invalid", continue to next post.
- **Other errors:** Retry once, then write to `output/failed/` and continue.

---

### 5. Publish Container

**Description:** Call Instagram Graph API to publish the media container created in step 4.

**Delegate to:** `publisher-specialist`

**Delegation command:**
```bash
claude code --agent publisher-specialist
```

**Task for subagent:**
"Publish Instagram container {creation_id} for business account {business_account_id}. Use Graph API endpoint POST /{business_account_id}/media_publish. Return post ID and permalink or error details."

**Tools used by subagent:** `bash`, `read`, `write`

**Actions:**
1. Wait 2 seconds (containers take 1-2s to process on Instagram's side)
2. Call `tools/instagram_publish_container.py` with:
   - `creation_id` from step 4
   - `business_account_id`
   - `access_token` from secret
3. Tool makes POST request to `https://graph.facebook.com/v18.0/{business_account_id}/media_publish`
4. Tool implements retry with exponential backoff (3 attempts)
5. Return `post_id` and `permalink` on success or error JSON on failure

**Outputs:** Published post ID (e.g., "17895695668004550") and permalink (e.g., "https://www.instagram.com/p/ABC123/")

**Failure Mode:** API error (rate limit 429, invalid container ID 100, publish failed)

**Fallback:**
- **Rate limit (429):** Retry with exponential backoff (2s, 4s, 8s). If all fail, write to `output/failed/` with status "rate_limited".
- **Invalid container (100):** Do NOT retry. Write to `output/failed/` with status "container_invalid", continue to next post.
- **Container not ready (error about processing):** Retry up to 3 times with 3-second delays. If still failing, write to `output/failed/` with status "container_not_ready".

---

### 6. Log Results

**Description:** Write publish result to `output/published/` (success) or `output/failed/` (failure) with full metadata.

**Delegate to:** Main agent (simple file write)

**Tools:** `tools/write_result.py`

**Actions:**
1. For each processed post, determine success or failure status
2. Build result JSON:
   - **Success:** `{status, post_id, permalink, timestamp, caption, image_url, business_account_id}`
   - **Failure:** `{status, error_code, error_message, retry_count, timestamp, caption, image_url, business_account_id}`
3. Generate filename: `{timestamp}_{post_id or hash}.json`
4. Write to `output/published/` or `output/failed/` directory
5. Create directories if they don't exist

**Outputs:** JSON file written to output directory

**Failure Mode:** File write fails (disk full, permission error, directory not writable)

**Fallback:** Log error to stderr with full details but do NOT fail the workflow. Results are still in memory for the report step. If file write consistently fails, open a GitHub Issue.

---

### 7. Generate Report

**Description:** Aggregate all publish results and generate a markdown summary report.

**Delegate to:** `report-generator-specialist`

**Delegation command:**
```bash
claude code --agent report-generator-specialist
```

**Task for subagent:**
"Generate daily publish report from all JSON files in output/published/ and output/failed/. Include summary stats, failed post details, and recommendations."

**Tools used by subagent:** `bash`, `read`, `write`

**Actions:**
1. Call `tools/generate_report.py` with:
   - `published_dir`: "output/published"
   - `failed_dir`: "output/failed"
2. Tool reads all JSON files from both directories
3. Tool aggregates stats:
   - Total attempts (published + failed)
   - Success count and percentage
   - Failure count and breakdown by error type
4. Tool generates markdown report with sections:
   - Summary (counts, success rate)
   - Failed Posts (timestamp, error code, error message)
   - Recommendations (e.g., "3 rate limit errors - consider reducing frequency")
5. Write report to `logs/{date}_publish_report.md`

**Outputs:** Markdown report file in `logs/` directory

**Failure Mode:** Report generation fails (parse error in JSON files, missing directories)

**Fallback:** Log error and skip report generation. Results are already written to output directories, so report is informational only. Do NOT fail the workflow.

---

### 8. Commit Results

**Description:** Stage and commit all output files to the repository.

**Delegate to:** Main agent (Git operations)

**Tools:** `tools/git_commit.py` or direct Git CLI

**Actions:**
1. Stage specific files:
   - `git add output/published/*.json`
   - `git add output/failed/*.json`
   - `git add logs/{date}_publish_report.md`
2. Create commit message: `"Published {N} posts, {M} failures [{timestamp}]"`
3. Commit staged files: `git commit -m "{message}"`
4. Push to origin: `git push origin main`

**Outputs:** Git commit SHA and push status

**Failure Mode:** Git commit fails (merge conflict, network error, push rejected)

**Fallback:**
1. Retry commit once with `git pull --rebase origin main` first
2. If still fails, log detailed error to stderr
3. Do NOT fail the workflow -- results are on disk and will be committed on next successful run
4. If push fails due to network, results are committed locally and will be pushed on next run

**CRITICAL Git Rule:** Use ONLY `git add <specific-file-paths>`. NEVER use `git add -A` or `git add .` because that could stage unintended files.

---

## Decision Points

### Should I use Agent Teams for parallel processing?

**Check:** `inputs.use_parallel` is true AND queue has 3+ posts

**If yes:**
- Main agent creates a shared task list with one task per post
- Spawn N teammates (one per post, max 10 parallel)
- Each teammate independently executes steps 2-6 for their assigned post
- Team lead collects all results and continues to steps 7-8

**If no:**
- Execute steps 2-6 sequentially for each post
- Continue to steps 7-8

**Rationale:** Agent Teams provides 2x speedup for batches of 3+ posts, but adds overhead for small batches. Sequential execution is simpler and sufficient for 1-2 posts.

---

## Failure Recovery

### Per-Post Error Isolation

Each post is processed independently. If post A fails, posts B, C, D continue processing. Partial success is acceptable.

### Retry Strategy by Error Type

| Error Code | Meaning | Retry? | Fallback |
|------------|---------|--------|----------|
| 429 | Rate limit exceeded | Yes, 3x with backoff | Fail after 3 attempts, queue for next run |
| 190 | Invalid token | No | Halt workflow, alert admin |
| 400 | Bad request (invalid image, etc.) | No | Skip post, log details |
| 100 | Invalid container ID | No | Skip post, log details |
| 500+ | Instagram server error | Yes, 1x | Fail after 1 retry, queue for next run |

### State Persistence

Failed posts remain in `output/failed/`. Humans can:
1. Fix the issue (update caption, replace image URL)
2. Move JSON from `output/failed/` back to `input/queue/`
3. Next workflow run will retry automatically

### Emergency Halt Conditions

Stop the workflow immediately if:
- Invalid token error (190) -- no point continuing, all posts will fail
- Disk full error when writing results
- 5+ consecutive rate limit errors -- Instagram API is overloaded

---

## Success Criteria

- ✅ At least one content file processed (or silent success if queue empty)
- ✅ All valid posts either published successfully OR logged to `output/failed/` with error details
- ✅ No unhandled exceptions that crash the workflow
- ✅ Report generated (or logged error if generation fails)
- ✅ Results committed to repo (or logged error if commit fails)
- ✅ Exit code 0 (even if some posts failed -- partial success is success)

---

## Performance Characteristics

**Sequential execution (1 post):**
- Validation: 1-2s (includes HEAD request)
- Create container: 2-3s
- Publish container: 2-3s (includes 2s wait)
- Total: ~7-8 seconds per post

**Parallel execution (10 posts with Agent Teams):**
- Wall time: ~10-12 seconds (all posts in parallel)
- Total tokens: Same as sequential (each post is independent)
- Speedup: ~7x for large batches

**Rate limit considerations:**
- Instagram API: 200 calls/hour per user
- Each post = 2 API calls (create + publish)
- Max sustainable rate: 100 posts/hour
- Recommended: 15-minute intervals (max ~400 posts/day)

---

## Environment Requirements

### Required Secrets
- `INSTAGRAM_ACCESS_TOKEN` -- Instagram Graph API token with `instagram_content_publish` permission
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` -- Numeric Instagram Business Account ID

### Optional Secrets
- `ANTHROPIC_API_KEY` -- For optional content enrichment
- `OPENAI_API_KEY` -- Fallback LLM for enrichment

### Python Dependencies
See `requirements.txt`

---

## Testing Strategy

See Step 8 validation gates in PRP for full testing procedures.

**Quick smoke test:**
```bash
# Create test post
cat > input/queue/test.json << 'EOF'
{
  "caption": "Test post #test",
  "image_url": "https://picsum.photos/1080/1080",
  "business_account_id": "$INSTAGRAM_BUSINESS_ACCOUNT_ID"
}
EOF

# Run workflow
python tools/validate_content.py input/queue/test.json
# Expected: {"is_valid": true, "errors": [], "warnings": []}
```

For full integration test with real API, see Level 3 validation in PRP.
