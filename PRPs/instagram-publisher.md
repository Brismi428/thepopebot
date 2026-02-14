name: "Instagram Publisher"
description: |
  Automated Instagram content publishing system with Graph API integration and intelligent fallback handling for failed posts.

## Purpose
WAT System PRP (Product Requirements Prompt) — a structured blueprint that gives the factory enough context to build a complete, working system in one pass.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build an autonomous Instagram content publishing system that accepts content (text, images, captions, hashtags) via multiple input methods, publishes to Instagram Business accounts using the Graph API, handles failures gracefully with intelligent retry and fallback strategies, and provides detailed status reporting for every publish attempt.

The system must handle the full Instagram publishing lifecycle: content validation, image processing, API call orchestration, error detection, retry logic, and audit logging — all while running autonomously via GitHub Actions on schedule or manual dispatch.

## Why
- **Automates manual posting**: Eliminates the need for humans to manually post content to Instagram at specific times
- **Consistent scheduling**: Ensures content goes live at optimal times without human oversight
- **Error resilience**: Intelligent fallback handling prevents lost content when API calls fail
- **Audit trail**: Every publish attempt is logged with success/failure status and error details
- **Multi-account support**: Can manage multiple Instagram Business accounts from a single system
- **Content pipeline integration**: Works as the final stage in content generation pipelines (e.g., marketing-pipeline, content-repurpose-engine)

## What
From the user's perspective:
1. Drop a content JSON file into `input/queue/` OR trigger via `workflow_dispatch` with inline content
2. The system validates the content, uploads media to Instagram, creates a container, and publishes
3. If publication fails, the system retries with exponential backoff and logs detailed error information
4. Results are written to `output/published/` (success) or `output/failed/` (failure) with full metadata
5. Status reports are committed to the repo with timestamps, post IDs, and error details

### Success Criteria
- [ ] Accepts content via file drop (`input/queue/*.json`) or manual dispatch (JSON payload)
- [ ] Validates all required fields (caption, image_url, business_account_id) before attempting publish
- [ ] Successfully publishes images to Instagram Business accounts via Graph API
- [ ] Handles Instagram API errors gracefully with 3 retry attempts and exponential backoff
- [ ] Logs all publish attempts with timestamps, status, post ID (if success), and error details
- [ ] Commits results to repo: success → `output/published/`, failure → `output/failed/`
- [ ] System runs autonomously via GitHub Actions on schedule (e.g., every 15 minutes to process queue)
- [ ] All three execution paths work: CLI (local testing), GitHub Actions (production), Agent HQ (issue-driven)
- [ ] No secrets are hardcoded — all API keys come from GitHub Secrets or .env

---

## Inputs
Content to be published to Instagram.

```yaml
- name: "content_payload"
  type: "JSON"
  source: "File drop in input/queue/*.json OR workflow_dispatch input parameter"
  required: true
  description: "Instagram post content with caption, image URL, and metadata"
  example: |
    {
      "caption": "Check out our latest product! #marketing #business",
      "image_url": "https://example.com/images/product.jpg",
      "business_account_id": "17841405309211844",
      "alt_text": "Product photo showing new feature",
      "hashtags": ["#marketing", "#business", "#product"],
      "scheduled_time": "2026-02-15T10:00:00Z"
    }

- name: "publishing_schedule"
  type: "cron expression"
  source: ".github/workflows/publish.yml schedule trigger"
  required: false
  description: "Cron schedule for processing the queue (e.g., every 15 minutes)"
  example: "*/15 * * * *"

- name: "business_account_id"
  type: "string"
  source: "Content payload OR environment variable"
  required: true
  description: "Instagram Business Account ID (from Graph API)"
  example: "17841405309211844"
```

## Outputs
Published posts, status reports, and error logs.

```yaml
- name: "publish_success"
  type: "JSON"
  destination: "output/published/{timestamp}_{post_id}.json"
  description: "Successful publish result with post ID, timestamp, and metadata"
  example: |
    {
      "status": "published",
      "post_id": "17895695668004550",
      "permalink": "https://www.instagram.com/p/ABC123/",
      "timestamp": "2026-02-14T12:21:57Z",
      "caption": "Check out our latest product!",
      "image_url": "https://example.com/images/product.jpg",
      "business_account_id": "17841405309211844"
    }

- name: "publish_failure"
  type: "JSON"
  destination: "output/failed/{timestamp}_{hash}.json"
  description: "Failed publish result with error details and retry count"
  example: |
    {
      "status": "failed",
      "error_code": "OAuthException",
      "error_message": "Invalid OAuth access token",
      "retry_count": 3,
      "timestamp": "2026-02-14T12:21:57Z",
      "caption": "Check out our latest product!",
      "image_url": "https://example.com/images/product.jpg",
      "business_account_id": "17841405309211844"
    }

- name: "publish_report"
  type: "Markdown"
  destination: "logs/{date}_publish_report.md"
  description: "Daily summary of all publish attempts (success/failure breakdown)"
  example: |
    # Instagram Publish Report - 2026-02-14
    
    ## Summary
    - Total attempts: 12
    - Successful: 10
    - Failed: 2
    
    ## Failed Posts
    1. [12:21:57] OAuthException: Invalid token
    2. [14:35:12] Rate limit exceeded
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://developers.facebook.com/docs/instagram-api/guides/content-publishing"
  why: "Core Instagram Graph API publishing flow: upload media, create container, publish container"

- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-user/media"
  why: "API endpoint reference for creating media containers"

- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-user/media_publish"
  why: "API endpoint reference for publishing media containers"

- url: "https://developers.facebook.com/docs/graph-api/overview/rate-limiting"
  why: "Instagram API rate limits: 200 calls per hour per user, must implement backoff"

- url: "https://developers.facebook.com/docs/instagram-api/reference/error-codes"
  why: "Complete list of error codes and recommended handling strategies"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide the capabilities this system needs"

- doc: "library/patterns.md"
  why: "Select the best workflow pattern for this system"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns to adapt (rest_client, oauth_token_refresh)"
```

### Workflow Pattern Selection
```yaml
pattern: "Intake > Enrich > Deliver"
rationale: |
  This system receives raw content (Intake), validates and potentially enriches it with 
  metadata like hashtag analysis or image optimization (Enrich), then delivers to Instagram 
  via the Graph API (Deliver). The pattern's error isolation and graceful degradation fit 
  Instagram's API constraints perfectly.
modifications: |
  - Add intelligent retry logic with exponential backoff (Instagram rate limits)
  - Add per-post error isolation (one failed post doesn't kill the batch)
  - Add detailed audit logging for every publish attempt
  - Add fallback queue for failed posts (retry on next run)
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "HTTP API calls to Instagram Graph API"
    primary_mcp: "fetch"
    alternative_mcp: "none"
    fallback: "Python requests library with retry logic via tenacity"
    secret_name: "INSTAGRAM_ACCESS_TOKEN"

  - name: "Image validation and processing"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "Pillow (PIL) for image validation, format checks, size validation"
    secret_name: "none"

  - name: "LLM for content validation and hashtag analysis"
    primary_mcp: "anthropic"
    alternative_mcp: "none"
    fallback: "OpenAI API via openai Python package"
    secret_name: "ANTHROPIC_API_KEY or OPENAI_API_KEY"

  - name: "Optional: Web content scraping for image URLs"
    primary_mcp: "firecrawl"
    alternative_mcp: "fetch"
    fallback: "Python requests + BeautifulSoup"
    secret_name: "FIRECRAWL_API_KEY (optional)"
```

### Known Gotchas & Constraints
```
# CRITICAL: Instagram Graph API rate limit is 200 calls per hour per user
# CRITICAL: Publishing requires TWO API calls: (1) create container, (2) publish container
# CRITICAL: Image must be publicly accessible URL — Instagram fetches it, we don't upload binary
# CRITICAL: Image format requirements: JPEG or PNG, max 8MB, min 320px width, aspect ratio 4:5 to 1.91:1
# CRITICAL: Caption max length: 2,200 characters including hashtags
# CRITICAL: Max 30 hashtags per post (Instagram limit)
# CRITICAL: Business Account ID required — cannot publish to personal accounts
# CRITICAL: Access token must have instagram_content_publish permission
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: Container creation returns creation_id — must be used in publish step
# CRITICAL: Rate limit errors (code 32) should trigger exponential backoff, not immediate retry
# CRITICAL: Invalid token errors (code 190) should NOT retry — fail immediately
```

---

## System Design

### Subagent Architecture
Specialist subagents for each major capability.

```yaml
subagents:
  - name: "content-validator-specialist"
    description: "Validates Instagram content before publish attempt. Delegate when you need to check caption length, hashtag count, image URL validity, or format requirements."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Validate caption length (max 2,200 chars)"
      - "Validate hashtag count (max 30)"
      - "Validate image URL format and accessibility"
      - "Check image dimensions and format (via HEAD request or PIL)"
      - "Return validation report with pass/fail and specific error messages"
    inputs: "Content payload JSON"
    outputs: "Validation report JSON with is_valid, errors list, warnings list"

  - name: "publisher-specialist"
    description: "Handles Instagram Graph API operations. Delegate when you need to create containers, publish posts, or handle API errors. This is the core publishing agent."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Call Graph API to create media container"
      - "Call Graph API to publish media container"
      - "Implement retry logic with exponential backoff"
      - "Parse API error responses and determine retry eligibility"
      - "Return publish result with post ID or detailed error"
    inputs: "Validated content payload, access token, business account ID"
    outputs: "Publish result JSON with status, post_id, permalink, or error details"

  - name: "fallback-handler-specialist"
    description: "Manages failed posts and retry queue. Delegate when a publish attempt fails and you need to decide whether to retry now, queue for later, or mark as permanently failed."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Analyze failure type (transient vs permanent)"
      - "Decide retry strategy based on error code"
      - "Write failed posts to retry queue or permanent failure log"
      - "Generate actionable error reports for humans"
    inputs: "Failed publish result with error code and message"
    outputs: "Fallback action recommendation and updated queue files"

  - name: "report-generator-specialist"
    description: "Generates daily/weekly publish reports. Delegate when you need to summarize batch results or produce audit logs."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Aggregate publish results from output/ directories"
      - "Generate markdown reports with success/failure breakdown"
      - "Calculate metrics (success rate, error frequency, retry counts)"
      - "Produce actionable recommendations for improving success rate"
    inputs: "All JSON files in output/published/ and output/failed/"
    outputs: "Markdown report in logs/{date}_publish_report.md"
```

### Agent Teams Analysis
```yaml
independent_tasks:
  - "Validate content payload (no dependency on other tasks)"
  - "Fetch image metadata from URL (no dependency on validation)"
  - "Analyze hashtags for optimal engagement (no dependency on validation)"

independent_task_count: 3
recommendation: "Use Agent Teams for batch processing multiple posts"
rationale: |
  When processing a batch of 10+ posts, each post is independent. Validation, publishing, 
  and reporting for each post can run in parallel. However, for single-post triggers or 
  small queues (<3 posts), sequential execution is sufficient and simpler.
  
  Sequential execution time: 3 posts × 8 seconds per post = 24 seconds
  Agent Teams execution: 3 posts in parallel = ~10 seconds (2x speedup)
  
  Recommendation: Implement sequential as default, with Agent Teams as an opt-in for 
  batch processing via a workflow input parameter (use_parallel: true).

team_lead_responsibilities:
  - "Load all posts from input/queue/"
  - "Create task list (one publish task per post)"
  - "Spawn teammates for independent publish tasks (if use_parallel=true)"
  - "Merge results and generate batch report"
  - "Commit all outputs to repo"

teammates:
  - name: "post-publisher-1"
    task: "Validate and publish post 1 from queue"
    inputs: "Content payload 1"
    outputs: "Publish result JSON"

  - name: "post-publisher-2"
    task: "Validate and publish post 2 from queue"
    inputs: "Content payload 2"
    outputs: "Publish result JSON"

  - name: "post-publisher-N"
    task: "Validate and publish post N from queue"
    inputs: "Content payload N"
    outputs: "Publish result JSON"

sequential_rationale: "For single posts or small queues, sequential execution is simpler and avoids Agent Teams overhead. Parallel processing is opt-in."
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "*/15 * * * *  # Every 15 minutes"
    description: "Process all posts in input/queue/ and publish to Instagram"

  - type: "workflow_dispatch"
    config: |
      inputs:
        content:
          description: 'JSON content payload for immediate publish'
          required: false
        use_parallel:
          description: 'Use Agent Teams for batch processing'
          required: false
          default: 'false'
    description: "Manual publish trigger with inline content or batch processing flag"

  - type: "repository_dispatch"
    config: "event_type: instagram_publish"
    description: "Triggered by upstream content pipelines (e.g., marketing-pipeline)"
```

---

## Implementation Blueprint

### Workflow Steps
Ordered workflow phases matching the Intake > Enrich > Deliver pattern.

```yaml
steps:
  - name: "Load Content Queue"
    description: "Read all JSON files from input/queue/ or parse inline content from workflow_dispatch"
    subagent: "none (main agent)"
    tools: ["fs_read.py"]
    inputs: "input/queue/*.json OR workflow_dispatch inputs.content"
    outputs: "List of content payloads"
    failure_mode: "No files in queue and no inline content provided"
    fallback: "Log info message 'No content to publish' and exit 0 (silent success)"

  - name: "Validate Content"
    description: "For each content payload, validate caption, hashtags, image URL, and format requirements"
    subagent: "content-validator-specialist"
    tools: ["validate_content.py"]
    inputs: "Content payload JSON"
    outputs: "Validation report JSON (is_valid, errors, warnings)"
    failure_mode: "Validation fails (invalid image URL, caption too long, etc.)"
    fallback: "Skip invalid posts, log detailed errors, continue with valid posts"

  - name: "Enrich Metadata (Optional)"
    description: "Optionally enhance content with hashtag analysis, image alt text generation, or caption improvements"
    subagent: "none (optional step)"
    tools: ["enrich_content.py"]
    inputs: "Validated content payload"
    outputs: "Enhanced content payload with additional metadata"
    failure_mode: "Enrichment API fails (Claude or OpenAI)"
    fallback: "Skip enrichment, proceed with original content"

  - name: "Create Media Container"
    description: "Call Instagram Graph API to create a media container with image URL and caption"
    subagent: "publisher-specialist"
    tools: ["instagram_create_container.py"]
    inputs: "Validated content payload, INSTAGRAM_ACCESS_TOKEN, business_account_id"
    outputs: "Container creation_id"
    failure_mode: "API error (rate limit, invalid token, image fetch failure)"
    fallback: "Retry with exponential backoff (3 attempts). If all fail, write to output/failed/ and continue"

  - name: "Publish Container"
    description: "Call Instagram Graph API to publish the media container"
    subagent: "publisher-specialist"
    tools: ["instagram_publish_container.py"]
    inputs: "Container creation_id, INSTAGRAM_ACCESS_TOKEN, business_account_id"
    outputs: "Published post ID and permalink"
    failure_mode: "API error (rate limit, invalid container ID)"
    fallback: "Retry with exponential backoff (3 attempts). If all fail, write to output/failed/"

  - name: "Log Results"
    description: "Write publish results to output/published/ (success) or output/failed/ (failure)"
    subagent: "none (main agent)"
    tools: ["write_result.py"]
    inputs: "Publish result JSON"
    outputs: "JSON file in output/published/ or output/failed/"
    failure_mode: "File write fails (disk full, permission error)"
    fallback: "Log to stderr and continue (don't fail the entire workflow)"

  - name: "Generate Report"
    description: "Aggregate all results and generate a markdown summary report"
    subagent: "report-generator-specialist"
    tools: ["generate_report.py"]
    inputs: "All JSON files in output/published/ and output/failed/"
    outputs: "Markdown report in logs/{date}_publish_report.md"
    failure_mode: "Report generation fails (parse error)"
    fallback: "Log error and skip report generation (results are already written)"

  - name: "Commit Results"
    description: "Stage and commit all output files to the repo"
    subagent: "none (main agent)"
    tools: ["git_commit.py"]
    inputs: "All files in output/ and logs/"
    outputs: "Git commit with message 'Published N posts, M failures [YYYY-MM-DD HH:MM:SS]'"
    failure_mode: "Git commit fails (merge conflict, network error)"
    fallback: "Retry commit once. If fails, log error but don't fail workflow (results are still on disk)"
```

### Tool Specifications
Tools needed for the system, referencing reusable patterns from tool_catalog.md.

```yaml
tools:
  - name: "validate_content.py"
    purpose: "Validate Instagram content against API requirements"
    catalog_pattern: "new (Instagram-specific validation logic)"
    inputs:
      - "content: dict — Content payload with caption, image_url, hashtags"
    outputs: "JSON: {is_valid: bool, errors: list[str], warnings: list[str]}"
    dependencies: ["requests", "pillow"]
    mcp_used: "none"
    error_handling: "Return validation report with specific error messages, never raise exceptions"

  - name: "instagram_create_container.py"
    purpose: "Create Instagram media container via Graph API"
    catalog_pattern: "rest_client (adapted for Instagram Graph API)"
    inputs:
      - "image_url: str — Publicly accessible image URL"
      - "caption: str — Post caption with hashtags"
      - "business_account_id: str — Instagram Business Account ID"
      - "access_token: str — Instagram access token with publish permission"
    outputs: "JSON: {creation_id: str, status: str}"
    dependencies: ["httpx", "tenacity"]
    mcp_used: "fetch (optional)"
    error_handling: "Retry on rate limit (429), fail immediately on auth errors (190), return error JSON on failure"

  - name: "instagram_publish_container.py"
    purpose: "Publish Instagram media container via Graph API"
    catalog_pattern: "rest_client (adapted for Instagram Graph API)"
    inputs:
      - "creation_id: str — Container ID from create step"
      - "business_account_id: str — Instagram Business Account ID"
      - "access_token: str — Instagram access token"
    outputs: "JSON: {post_id: str, permalink: str, status: str}"
    dependencies: ["httpx", "tenacity"]
    mcp_used: "fetch (optional)"
    error_handling: "Retry on rate limit (429), fail immediately on invalid container (100), return error JSON"

  - name: "enrich_content.py"
    purpose: "Optionally enhance content with LLM-generated insights"
    catalog_pattern: "llm_prompt (adapted for content enhancement)"
    inputs:
      - "content: dict — Content payload"
      - "enhancement_type: str — 'hashtags' or 'alt_text' or 'caption'"
    outputs: "JSON: {enhanced_content: dict}"
    dependencies: ["anthropic", "openai"]
    mcp_used: "anthropic (primary), none (fallback to openai)"
    error_handling: "If LLM call fails, return original content unchanged (graceful degradation)"

  - name: "write_result.py"
    purpose: "Write publish result to output directory"
    catalog_pattern: "json_read_write (adapted for timestamped output)"
    inputs:
      - "result: dict — Publish result with status, post_id, or error"
      - "output_dir: str — 'output/published' or 'output/failed'"
    outputs: "File path of written JSON"
    dependencies: ["pathlib", "json"]
    mcp_used: "none"
    error_handling: "Create directories if missing, log error if write fails but don't raise exception"

  - name: "generate_report.py"
    purpose: "Generate markdown summary report of publish results"
    catalog_pattern: "new (aggregation and markdown generation)"
    inputs:
      - "published_dir: str — Path to output/published/"
      - "failed_dir: str — Path to output/failed/"
    outputs: "Markdown report string"
    dependencies: ["pathlib", "json"]
    mcp_used: "none"
    error_handling: "Skip malformed JSON files, continue aggregation"

  - name: "git_commit.py"
    purpose: "Stage and commit output files to repo"
    catalog_pattern: "git_commit_push (from tool_catalog.md)"
    inputs:
      - "files: list[str] — Specific file paths to stage"
      - "message: str — Commit message"
    outputs: "JSON: {commit_sha: str, committed: bool}"
    dependencies: ["subprocess"]
    mcp_used: "git (via subprocess)"
    error_handling: "Retry once on failure, log error if both attempts fail"
```

### Per-Tool Pseudocode
High-level logic for each tool.

```python
# validate_content.py
def main(content: dict) -> dict:
    # PATTERN: Validation with detailed error reporting
    errors, warnings = [], []
    
    # Validate caption
    if len(content.get("caption", "")) > 2200:
        errors.append("Caption exceeds 2,200 character limit")
    
    # Validate hashtags
    hashtags = content.get("hashtags", [])
    if len(hashtags) > 30:
        errors.append(f"Too many hashtags: {len(hashtags)} (max 30)")
    
    # Validate image URL
    image_url = content.get("image_url", "")
    if not image_url.startswith("http"):
        errors.append("Invalid image URL format")
    else:
        # HEAD request to check if image is accessible
        try:
            resp = requests.head(image_url, timeout=5)
            if resp.status_code != 200:
                errors.append(f"Image URL not accessible: {resp.status_code}")
        except Exception as e:
            errors.append(f"Image URL fetch failed: {str(e)}")
    
    return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# instagram_create_container.py
def main(image_url: str, caption: str, business_account_id: str, access_token: str) -> dict:
    # PATTERN: rest_client with Instagram-specific retry logic
    # CRITICAL: Instagram API rate limit is 200 calls/hour
    # CRITICAL: Must retry on 429 (rate limit), fail fast on 190 (invalid token)
    
    url = f"https://graph.facebook.com/v18.0/{business_account_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=2, min=4, max=60),
           retry=retry_if_exception(_is_retryable))
    def _create():
        resp = httpx.post(url, json=payload, timeout=30)
        if resp.status_code == 429:
            raise RetryableError("Rate limit exceeded")
        if resp.status_code in (190, 400):
            raise NonRetryableError(f"Auth/validation error: {resp.text}")
        resp.raise_for_status()
        return resp.json()
    
    try:
        result = _create()
        return {"creation_id": result["id"], "status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# instagram_publish_container.py
def main(creation_id: str, business_account_id: str, access_token: str) -> dict:
    # PATTERN: rest_client with retry logic
    # CRITICAL: Container must be fully processed before publishing (can take 1-2 seconds)
    
    url = f"https://graph.facebook.com/v18.0/{business_account_id}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    
    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=2, min=4, max=60))
    def _publish():
        resp = httpx.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    
    try:
        result = _publish()
        post_id = result["id"]
        permalink = f"https://www.instagram.com/p/{_post_id_to_code(post_id)}/"
        return {"post_id": post_id, "permalink": permalink, "status": "published"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# enrich_content.py
def main(content: dict, enhancement_type: str) -> dict:
    # PATTERN: llm_prompt with graceful degradation
    # If LLM fails, return original content unchanged
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        
        prompt = _build_enhancement_prompt(content, enhancement_type)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        enhanced = _parse_enhancement(msg.content[0].text)
        return {"enhanced_content": {**content, **enhanced}}
    except Exception:
        # Graceful degradation: return original content
        return {"enhanced_content": content}

# generate_report.py
def main(published_dir: str, failed_dir: str) -> str:
    # PATTERN: Aggregation and markdown generation
    published = list(Path(published_dir).glob("*.json"))
    failed = list(Path(failed_dir).glob("*.json"))
    
    report = f"# Instagram Publish Report - {date.today()}\n\n"
    report += f"## Summary\n"
    report += f"- Total attempts: {len(published) + len(failed)}\n"
    report += f"- Successful: {len(published)}\n"
    report += f"- Failed: {len(failed)}\n\n"
    
    if failed:
        report += "## Failed Posts\n"
        for f in failed:
            data = json.loads(f.read_text())
            report += f"- [{data['timestamp']}] {data['error_code']}: {data['error_message']}\n"
    
    return report
```

### Integration Points
Environment, secrets, and GitHub Actions configuration.

```yaml
SECRETS:
  - name: "INSTAGRAM_ACCESS_TOKEN"
    purpose: "Instagram Graph API access token with instagram_content_publish permission"
    required: true

  - name: "INSTAGRAM_BUSINESS_ACCOUNT_ID"
    purpose: "Instagram Business Account ID (numeric string)"
    required: true

  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API key for optional content enrichment"
    required: false

  - name: "OPENAI_API_KEY"
    purpose: "OpenAI API key as fallback for content enrichment"
    required: false

  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API key for optional image scraping from web pages"
    required: false

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "INSTAGRAM_ACCESS_TOKEN=your_token_here  # Get from Facebook Developer Portal"
      - "INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id  # Numeric ID from Graph API"
      - "ANTHROPIC_API_KEY=your_api_key  # Optional: For content enrichment"
      - "OPENAI_API_KEY=your_api_key  # Optional: Fallback LLM"
      - "FIRECRAWL_API_KEY=your_api_key  # Optional: For image scraping"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "httpx>=0.27.0  # HTTP client with retry support"
      - "tenacity>=8.2.0  # Retry logic and exponential backoff"
      - "pillow>=10.0.0  # Image validation"
      - "anthropic>=0.18.0  # Claude API (optional)"
      - "openai>=1.12.0  # OpenAI API (optional fallback)"

GITHUB_ACTIONS:
  - trigger: "schedule"
    config: "cron: '*/15 * * * *'  # Every 15 minutes"
  - trigger: "workflow_dispatch"
    config: |
      inputs:
        content:
          description: 'JSON content payload'
          required: false
        use_parallel:
          description: 'Use Agent Teams for batch'
          required: false
          default: 'false'
```

---

## Validation Loop

### Level 1: Syntax & Structure
Run FIRST — every tool must pass before proceeding to Level 2.

```bash
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/validate_content.py').read())"
python -c "import ast; ast.parse(open('tools/instagram_create_container.py').read())"
python -c "import ast; ast.parse(open('tools/instagram_publish_container.py').read())"
python -c "import ast; ast.parse(open('tools/enrich_content.py').read())"
python -c "import ast; ast.parse(open('tools/write_result.py').read())"
python -c "import ast; ast.parse(open('tools/generate_report.py').read())"
python -c "import ast; ast.parse(open('tools/git_commit.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.validate_content')"
python -c "import importlib; importlib.import_module('tools.instagram_create_container')"
python -c "import importlib; importlib.import_module('tools.instagram_publish_container')"
python -c "import importlib; importlib.import_module('tools.enrich_content')"
python -c "import importlib; importlib.import_module('tools.write_result')"
python -c "import importlib; importlib.import_module('tools.generate_report')"
python -c "import importlib; importlib.import_module('tools.git_commit')"

# Structure check — verify main() exists
python -c "from tools.validate_content import main; assert callable(main)"
python -c "from tools.instagram_create_container import main; assert callable(main)"
python -c "from tools.instagram_publish_container import main; assert callable(main)"
python -c "from tools.enrich_content import main; assert callable(main)"
python -c "from tools.write_result import main; assert callable(main)"
python -c "from tools.generate_report import main; assert callable(main)"
python -c "from tools.git_commit import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
Run SECOND — each tool must produce correct output for sample inputs.

```bash
# Test validate_content.py with valid content
python tools/validate_content.py --content '{
  "caption": "Test post #instagram #test",
  "image_url": "https://picsum.photos/1080/1080",
  "hashtags": ["#instagram", "#test"],
  "business_account_id": "17841405309211844"
}'
# Expected output: {"is_valid": true, "errors": [], "warnings": []}

# Test validate_content.py with invalid content (caption too long)
python tools/validate_content.py --content '{
  "caption": "'"$(python -c 'print("a" * 2300)')"'",
  "image_url": "https://picsum.photos/1080/1080",
  "hashtags": []
}'
# Expected output: {"is_valid": false, "errors": ["Caption exceeds 2,200 character limit"], "warnings": []}

# Test write_result.py
mkdir -p /tmp/test_output
python tools/write_result.py --result '{
  "status": "published",
  "post_id": "test123",
  "timestamp": "2026-02-14T12:00:00Z"
}' --output_dir /tmp/test_output
# Expected: File created at /tmp/test_output/<timestamp>_test123.json

# Test generate_report.py with sample data
mkdir -p /tmp/test_published /tmp/test_failed
echo '{"status": "published", "post_id": "123"}' > /tmp/test_published/post1.json
echo '{"status": "failed", "error_code": "OAuthException"}' > /tmp/test_failed/post2.json
python tools/generate_report.py --published_dir /tmp/test_published --failed_dir /tmp/test_failed
# Expected output: Markdown report with "Total attempts: 2, Successful: 1, Failed: 1"

# NOTE: instagram_create_container.py and instagram_publish_container.py require 
# real API credentials and cannot be unit tested without mocking. Test in Level 3.
```

### Level 3: Integration Tests
Run THIRD — verify tools work together as a pipeline with REAL API credentials.

```bash
# CRITICAL: This test requires valid Instagram credentials in .env
# Set up test environment
export $(cat .env | xargs)
mkdir -p input/queue output/published output/failed logs

# Create a test content file
cat > input/queue/test_post.json << 'EOF'
{
  "caption": "Test post from instagram-publisher system #test #automation",
  "image_url": "https://picsum.photos/1080/1080",
  "hashtags": ["#test", "#automation"],
  "business_account_id": "$INSTAGRAM_BUSINESS_ACCOUNT_ID"
}
EOF

# Run the full workflow
python -c "
import sys
sys.path.insert(0, 'tools')
from validate_content import main as validate
from instagram_create_container import main as create_container
from instagram_publish_container import main as publish_container
from write_result import main as write_result
import json
import os

# Load content
content = json.load(open('input/queue/test_post.json'))

# Step 1: Validate
validation = validate(content)
assert validation['is_valid'], f'Validation failed: {validation}'
print('✓ Validation passed')

# Step 2: Create container
container = create_container(
    image_url=content['image_url'],
    caption=content['caption'],
    business_account_id=os.environ['INSTAGRAM_BUSINESS_ACCOUNT_ID'],
    access_token=os.environ['INSTAGRAM_ACCESS_TOKEN']
)
assert container['status'] == 'success', f'Container creation failed: {container}'
print(f'✓ Container created: {container[\"creation_id\"]}')

# Step 3: Publish container
result = publish_container(
    creation_id=container['creation_id'],
    business_account_id=os.environ['INSTAGRAM_BUSINESS_ACCOUNT_ID'],
    access_token=os.environ['INSTAGRAM_ACCESS_TOKEN']
)
assert result['status'] == 'published', f'Publish failed: {result}'
print(f'✓ Post published: {result[\"post_id\"]}')

# Step 4: Write result
write_result(result, 'output/published')
print('✓ Result written to output/published/')

print('Integration test PASSED')
"

# Verify workflow.md references match actual tool files
grep -F "validate_content.py" workflow.md
grep -F "instagram_create_container.py" workflow.md
grep -F "instagram_publish_container.py" workflow.md

# Verify CLAUDE.md documents all tools and subagents
grep -F "content-validator-specialist" CLAUDE.md
grep -F "publisher-specialist" CLAUDE.md
grep -F "fallback-handler-specialist" CLAUDE.md

# Verify .github/workflows/ YAML is valid
yamllint .github/workflows/publish.yml
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test with real API)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/publish.yml has timeout-minutes (30) and failure notifications
- [ ] .env.example lists all required environment variables with descriptions
- [ ] .gitignore excludes .env, __pycache__/, input/queue/, output/
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files (.claude/agents/*.md) have valid YAML frontmatter
- [ ] requirements.txt lists all Python dependencies with versions
- [ ] Instagram API rate limit handling implemented (exponential backoff)
- [ ] Error codes properly categorized (retryable vs non-retryable)

---

## Anti-Patterns to Avoid
- Do not hardcode INSTAGRAM_ACCESS_TOKEN or any credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only specific output files
- Do not skip Level 3 integration tests — Instagram API has subtle error behaviors
- Do not retry on invalid token errors (190) — these are permanent failures
- Do not publish without validating caption length and hashtag count first
- Do not assume image URL is accessible — always validate with HEAD request
- Do not ignore rate limit errors — implement exponential backoff
- Do not create MCP-dependent tools without HTTP fallback
- Do not design subagents that call other subagents — only main agent delegates
- Do not use Agent Teams for single posts — overhead is not justified
- Do not commit .env files or API tokens to the repository
- Do not publish the container ID returned from create step — publish the POST_ID
- Do not forget to handle the async nature of container creation (1-2 second delay)

---

## Confidence Score: 9/10

**Score rationale:**
- **Instagram Graph API integration**: High confidence — API is well-documented, error codes are clear, retry strategies are proven — Confidence: high
- **Content validation logic**: High confidence — requirements are explicit (caption length, hashtag count, image format), validation is straightforward — Confidence: high
- **Error handling and fallback**: High confidence — Instagram error codes are documented, retry vs fail-fast logic is clear — Confidence: high
- **Workflow pattern selection**: High confidence — Intake > Enrich > Deliver fits perfectly, proven pattern from library — Confidence: high
- **Subagent architecture**: High confidence — Clear separation of concerns (validate, publish, fallback, report), no circular dependencies — Confidence: high
- **Agent Teams decision**: High confidence — 3+ Independent Tasks Rule applies for batch processing, sequential fallback is simple — Confidence: high
- **Tool implementations**: High confidence — All tools have clear inputs/outputs, reusable patterns from catalog, retry logic defined — Confidence: high
- **Validation strategy**: High confidence — Three-level validation with real API test is robust — Confidence: high
- **Secrets management**: High confidence — All secrets via GitHub Secrets or .env, no hardcoding — Confidence: high
- **Edge case handling**: Medium confidence — Image accessibility validation and container processing delay need real-world testing — Confidence: medium

**Ambiguity flags** (areas requiring clarification before building):
- [ ] NONE — All requirements are clear and well-specified

**Ready to build: YES** — No ambiguity flags, confidence score 9/10, all patterns and tools are well-defined.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/instagram-publisher.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
