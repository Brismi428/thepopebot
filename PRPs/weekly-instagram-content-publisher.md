name: "weekly-instagram-content-publisher"
description: |
  WAT System PRP (Product Requirements Prompt) — Weekly Instagram Content Generation & Publishing Pipeline

## Purpose
A weekly automated social media content factory that generates Instagram-ready posts (captions, hashtags, creative briefs, optional image prompts) aligned with brand voice and weekly themes, validates them through multi-gate quality review, and either auto-publishes via Instagram Graph API or prepares a manual-ready content pack.

## Core Principles
1. **Brand Voice Consistency**: All content must match documented brand guidelines (tone, style, dos/don'ts)
2. **Quality Gates Before Publishing**: Two-pass process (Generate > Review) with explicit approval gates
3. **Safe Fallback**: If auto-publish fails, gracefully degrade to manual content pack
4. **Audit Trail**: All generated content, reviews, and publish actions are logged and archived
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a GitHub-native social media content pipeline that eliminates weekly Instagram content creation drudgery while maintaining strict brand compliance and quality standards. The system runs autonomously on a schedule (Monday 09:00 UTC), generates a week's worth of Instagram posts, validates them against brand guardrails, and either publishes automatically or delivers a ready-to-post pack.

Success looks like: A brand opens their repo every Monday at 9:05 AM to find either (a) their content live on Instagram, or (b) a formatted content pack ready for manual upload -- both with full quality reports and zero prohibited claims or off-brand messaging.

## Why
- **Business value**: Saves 4-6 hours/week of manual content creation and review time
- **User impact**: Marketing teams get consistent, on-brand Instagram content without the weekly scramble
- **Automation gap**: Existing tools either skip quality review (risky) or require full human approval (not automated)
- **Who benefits**: Small-to-medium brands, agencies managing multiple clients, solopreneurs with consistent posting needs
- **Frequency**: Weekly (52 content packs/year), but can be triggered on-demand for special campaigns

## What
A scheduled GitHub Actions workflow that:
1. Reads brand profile, weekly theme, and post plan from repo config or workflow dispatch inputs
2. Optionally scrapes reference URLs (blog posts, product pages) for accurate details using Firecrawl
3. Generates Instagram posts (reels concepts, carousels, single images) via Claude/GPT with brand-aligned prompts
4. Runs quality review gates: brand voice match, prohibited claims detection, banned topics scan, hashtag hygiene, IG format compliance
5. Publishes approved posts via Instagram Graph API (auto_publish mode) OR prepares a manual upload pack (content_pack_only mode)
6. Archives all content in `output/instagram/archive/` with rolling index
7. Commits all artifacts back to the repo with detailed logs

### Success Criteria
- [ ] All generated posts pass brand voice alignment check (threshold: 85%+)
- [ ] Zero prohibited claims or banned topics detected
- [ ] All hashtags meet Instagram guidelines (no banned tags, 10-30 tags per post)
- [ ] All posts meet IG format constraints (caption ≤ 2200 chars, proper line breaks, CTA present)
- [ ] Auto-publish succeeds OR manual content pack is generated with checklist
- [ ] System runs autonomously via GitHub Actions on schedule (Monday 09:00 UTC)
- [ ] Results are committed back to repo with structured logs
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ
- [ ] Rate limiting and retry logic handle API failures gracefully

---

## Inputs

```yaml
- name: "brand_profile"
  type: "JSON"
  source: "repo file at config/brand_profile.json OR workflow_dispatch input"
  required: true
  description: "Complete brand voice definition, guardrails, and content policies"
  example: |
    {
      "brand_name": "EcoStyle",
      "tone": "friendly, educational, empowering",
      "voice_attributes": ["warm", "authentic", "fact-based"],
      "target_audience": "eco-conscious millennials, 25-40, urban",
      "products_services": ["sustainable fashion", "upcycled accessories", "zero-waste lifestyle"],
      "do_list": ["use first-person plural (we/our)", "cite sources", "celebrate small wins"],
      "dont_list": ["use corporate jargon", "guilt-trip readers", "make health claims"],
      "banned_topics": ["politics", "religion", "weight loss"],
      "prohibited_claims": ["cure", "detox", "guaranteed results"],
      "preferred_cta": ["Shop now", "Learn more", "Join the movement"],
      "emoji_style": "moderate (3-5 per post, relevant only)",
      "hashtag_strategy": "10-15 tags, mix of broad and niche, no banned tags"
    }

- name: "weekly_theme"
  type: "string"
  source: "workflow_dispatch input OR repo file at config/weekly_theme.txt"
  required: true
  description: "The content focus/topic for this week's posts"
  example: "Spring Collection Launch Week"

- name: "post_plan"
  type: "JSON"
  source: "workflow_dispatch input OR repo file at config/post_plan.json"
  required: true
  description: "Number and types of Instagram posts to generate, with any required templates or series"
  example: |
    {
      "posts": [
        {"type": "reel_concept", "count": 3, "topics": ["product spotlight", "behind the scenes", "customer story"]},
        {"type": "carousel", "count": 2, "slides_per": 5, "topics": ["style guide", "impact stats"]},
        {"type": "single_image", "count": 1, "topics": ["quote graphic"]}
      ],
      "series_tags": ["#EcoStyleSpring", "#SustainableFashion"],
      "posting_schedule": "Mon/Wed/Fri at 10am EST"
    }

- name: "reference_links"
  type: "JSON array"
  source: "workflow_dispatch input OR repo file at config/reference_links.json (optional)"
  required: false
  description: "URLs to scrape for accurate product details, blog content, or announcements"
  example: |
    [
      {"url": "https://ecostyle.com/blog/spring-collection", "context": "new product details"},
      {"url": "https://ecostyle.com/impact-report-2024", "context": "sustainability metrics"}
    ]

- name: "publishing_mode"
  type: "choice: 'auto_publish' | 'content_pack_only'"
  source: "workflow_dispatch input OR env var PUBLISHING_MODE (default: content_pack_only)"
  required: true
  description: "Whether to auto-publish to Instagram or prepare manual upload pack"
  example: "auto_publish"
```

## Outputs

```yaml
- name: "content_pack_{date}.md"
  type: "Markdown"
  destination: "repo commit at output/instagram/content_pack_2026-02-17.md"
  description: "Human-readable weekly content pack with all post details formatted for review or manual upload"
  example: "See factory/templates/instagram_content_pack.md"

- name: "content_pack_{date}.json"
  type: "JSON"
  destination: "repo commit at output/instagram/content_pack_2026-02-17.json"
  description: "Machine-readable structured data for each post (for automation or API consumption)"
  example: |
    {
      "generated_at": "2026-02-17T09:02:15Z",
      "theme": "Spring Collection Launch Week",
      "posts": [
        {
          "post_id": "post_001",
          "type": "reel_concept",
          "hook": "POV: You just discovered your new favorite sustainable brand 🌱",
          "caption": "Meet EcoStyle Spring 2026...",
          "cta": "Shop now (link in bio)",
          "hashtags": ["#EcoStyleSpring", "#SustainableFashion", ...],
          "alt_text": "Model wearing upcycled denim jacket...",
          "posting_time": "2026-02-17 10:00:00 EST",
          "creative_brief": "15-second reel showing 3 spring pieces...",
          "image_prompt": "A bright, airy flat lay of spring collection items..."
        }
      ]
    }

- name: "review_report_{date}.md"
  type: "Markdown"
  destination: "repo commit at output/instagram/review_report_2026-02-17.md"
  description: "Quality review results with pass/fail status for each gate"
  example: |
    ## Quality Review Report - 2026-02-17
    
    **Overall Status**: PASS (6/6 posts approved)
    
    ### Brand Voice Alignment
    - post_001: 92% match ✓
    - post_002: 88% match ✓
    ...
    
    ### Compliance Checks
    - Prohibited claims: 0 detected ✓
    - Banned topics: 0 detected ✓
    - Hashtag hygiene: All tags approved ✓

- name: "publish_log_{date}.json"
  type: "JSON"
  destination: "repo commit at output/instagram/publish_log_2026-02-17.json (if auto_publish mode)"
  description: "Instagram Graph API responses with media IDs or failure reasons"
  example: |
    {
      "published_at": "2026-02-17T09:04:33Z",
      "mode": "auto_publish",
      "results": [
        {"post_id": "post_001", "status": "success", "ig_media_id": "18123456789012345", "permalink": "https://instagram.com/p/..."},
        {"post_id": "post_002", "status": "failed", "error": "Rate limit exceeded", "retry_scheduled": true}
      ]
    }

- name: "upload_checklist_{date}.md"
  type: "Markdown"
  destination: "repo commit at output/instagram/upload_checklist_2026-02-17.md (if content_pack_only mode)"
  description: "Step-by-step manual upload instructions with copy-paste ready text"
  example: |
    ## Instagram Upload Checklist - Week of Feb 17, 2026
    
    ### Post 1 (Monday 10am EST)
    - [ ] Upload media: [image/video description]
    - [ ] Caption (copy below):
    ```
    [full caption with line breaks]
    ```
    - [ ] Hashtags (copy below):
    ```
    [hashtag list]
    ```
    - [ ] Schedule for: Monday, Feb 17 at 10:00 AM EST

- name: "archive/latest.md"
  type: "Markdown (rolling index)"
  destination: "repo commit at output/instagram/archive/latest.md"
  description: "Links to the 10 most recent content packs for quick access"
  example: |
    ## Recent Instagram Content Packs
    
    1. [2026-02-17 - Spring Collection Launch](../content_pack_2026-02-17.md)
    2. [2026-02-10 - Customer Love Week](../content_pack_2026-02-10.md)
    ...
```

---

## All Needed Context

### Documentation & References

```yaml
# MUST READ — Include these in context when building
- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-user/media"
  why: "Instagram Graph API media creation endpoint — POST format, field requirements, error codes"

- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-media"
  why: "IG media object structure — caption limits (2200 chars), hashtag rules, carousel vs single image"

- url: "https://help.instagram.com/477434105621119"
  why: "Instagram Community Guidelines — banned hashtags, prohibited content (official source)"

- url: "https://docs.anthropic.com/claude/docs/structured-outputs"
  why: "Claude structured output pattern for JSON schema validation — use for post generation"

- url: "https://docs.firecrawl.dev/api-reference/endpoint/scrape"
  why: "Firecrawl scraping API — for reference link content extraction"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide the capabilities this system needs (Firecrawl, Anthropic, Fetch)"

- doc: "library/patterns.md"
  why: "Select Generate > Review > Publish pattern (Pattern #5) as the base workflow"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns (llm_prompt, structured_extract, rest_client, firecrawl_scrape)"
```

### Workflow Pattern Selection

```yaml
pattern: "Generate > Review > Publish (Pattern #5)"
rationale: "Perfect fit — automated content generation with quality gates before publishing"
modifications:
  - "Add content_pack_only fallback mode (publish step becomes output-only)"
  - "Add reference link scraping step before generation (Scrape > Process > Output sub-pattern)"
  - "Add rolling archive step after publish/pack (Collect > Transform > Store sub-pattern)"
```

### MCP & Tool Requirements

```yaml
capabilities:
  - name: "web scraping (reference links)"
    primary_mcp: "firecrawl"
    alternative_mcp: "puppeteer (for JS-heavy pages)"
    fallback: "Direct HTTP with requests + BeautifulSoup4 (limited — no JS rendering)"
    secret_name: "FIRECRAWL_API_KEY"

  - name: "LLM content generation"
    primary_mcp: "anthropic"
    alternative_mcp: "openai (GPT-4)"
    fallback: "None — LLM is required for generation"
    secret_name: "ANTHROPIC_API_KEY or OPENAI_API_KEY"

  - name: "Instagram publishing"
    primary_mcp: "fetch (HTTP client)"
    alternative_mcp: "none (direct REST API)"
    fallback: "Manual content pack mode — no API required"
    secret_name: "INSTAGRAM_ACCESS_TOKEN"

  - name: "file storage and archive"
    primary_mcp: "filesystem"
    alternative_mcp: "none (direct Python pathlib)"
    fallback: "None — filesystem access is built-in"
    secret_name: "none"
```

### Known Gotchas & Constraints

```
# CRITICAL: Instagram Graph API requires a Facebook Business account and approved Instagram Business account
# CRITICAL: Access tokens expire — must implement token refresh or manual rotation instructions
# CRITICAL: Instagram rate limits: 200 API calls per hour per user — implement retry with exponential backoff
# CRITICAL: Caption limit is 2200 characters including hashtags — must validate before API call
# CRITICAL: Hashtags must be at end of caption or on separate lines — validate format
# CRITICAL: Instagram API does NOT support scheduling future posts — must use manual scheduling or third-party tools
# CRITICAL: Firecrawl has usage limits on free tier — implement HTTP fallback for reference scraping
# CRITICAL: Claude Sonnet 4 has ~8k output token limit — generating 6+ posts in one call may hit limits; use batching
# CRITICAL: Brand voice scoring requires reference examples in brand_profile — must include sample posts
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
```

---

## System Design

### Subagent Architecture

```yaml
subagents:
  - name: "content-strategist"
    description: "Delegate to this subagent when planning post types, themes, and content strategy based on brand profile and weekly theme"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Analyze brand profile and weekly theme to determine content angles"
      - "Map post_plan types to specific content topics and hooks"
      - "Identify which reference links are most relevant for each post type"
      - "Create a structured content brief for each post"
    inputs: "brand_profile.json, weekly_theme string, post_plan.json, reference_links.json"
    outputs: "List of content briefs (JSON) with post type, topic, hook angle, reference URLs, and target audience segment"

  - name: "reference-scraper-specialist"
    description: "Delegate to this subagent when extracting content from reference URLs for factual accuracy in posts"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Scrape each reference URL via Firecrawl (primary) or HTTP+BeautifulSoup (fallback)"
      - "Extract key facts, product details, metrics, quotes for content generation"
      - "Handle scraping failures gracefully (log error, continue with available data)"
      - "Return structured extracted data per URL"
    inputs: "reference_links array with URLs and context"
    outputs: "Extracted reference data (JSON) with url, context, extracted_text, key_facts, status"

  - name: "copywriter-specialist"
    description: "Delegate to this subagent when generating Instagram captions, hooks, CTAs, and creative briefs"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Generate Instagram-optimized captions (hook, body, CTA) matching brand voice"
      - "Write creative briefs for visual content (image/video descriptions)"
      - "Generate optional image prompts for AI image generation tools"
      - "Apply brand voice guidelines (tone, do/dont lists, emoji style)"
      - "Ensure caption length ≤ 2200 characters"
    inputs: "Content brief from strategist, brand_profile, extracted reference data"
    outputs: "Post content (JSON) with hook, caption, cta, creative_brief, image_prompt, alt_text"

  - name: "hashtag-specialist"
    description: "Delegate to this subagent when generating or validating Instagram hashtags"
    tools: "Read, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Generate 10-15 relevant hashtags per post based on content and brand strategy"
      - "Mix broad hashtags (100k+ posts) and niche hashtags (5k-50k posts)"
      - "Avoid banned/flagged hashtags (maintain internal banned list)"
      - "Apply series_tags from post_plan if specified"
      - "Validate hashtag count (10-30 per post, Instagram guidelines)"
    inputs: "Post content (caption, topic), brand_profile hashtag_strategy, post_plan series_tags"
    outputs: "Hashtag list (array of strings) with mix of broad/niche tags, validated for compliance"

  - name: "reviewer-specialist"
    description: "Delegate to this subagent when running quality gates on generated content before publishing"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Score brand voice alignment (0-100%) against brand_profile examples"
      - "Scan for prohibited claims from brand_profile.prohibited_claims"
      - "Scan for banned topics from brand_profile.banned_topics"
      - "Validate Instagram format compliance (caption length, hashtag placement, line breaks)"
      - "Check hashtag hygiene (no banned tags, proper count)"
      - "Return PASS/FAIL status per post with detailed feedback"
    inputs: "All generated posts (JSON), brand_profile with guardrails"
    outputs: "Review report (JSON + Markdown) with per-post scores, compliance checks, overall status, failed posts flagged for regeneration"

  - name: "publisher-specialist"
    description: "Delegate to this subagent when publishing approved content to Instagram via Graph API"
    tools: "Read, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Call Instagram Graph API to create media posts (single image or carousel)"
      - "Handle rate limiting (200 calls/hour) with retry and exponential backoff"
      - "Handle API errors gracefully (log error, mark post as failed, continue with remaining posts)"
      - "Track publish results (media ID, permalink, or error message)"
      - "If all posts fail, fall back to content_pack_only mode"
    inputs: "Approved posts (JSON with captions, hashtags, media URLs if available), INSTAGRAM_ACCESS_TOKEN"
    outputs: "Publish log (JSON) with per-post results (success/failed, media_id, permalink, error details)"
```

### Agent Teams Analysis

```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "Generate post 1 (reel concept) — no dependency on other posts"
  - "Generate post 2 (reel concept) — no dependency on other posts"
  - "Generate post 3 (reel concept) — no dependency on other posts"
  - "Generate post 4 (carousel) — no dependency on other posts"
  - "Generate post 5 (carousel) — no dependency on other posts"
  - "Generate post 6 (single image) — no dependency on other posts"

independent_task_count: "6 (assuming post_plan with 3 reels + 2 carousels + 1 single image)"
recommendation: "Use Agent Teams for post generation phase"
rationale: "6 independent content generation tasks, each taking ~15-20s with Claude API = 90-120s sequential vs ~18-22s parallel (5-6x speedup). All posts use the same brand profile and weekly theme but generate unique content. No data dependencies between posts. Merge step is simple (concatenate post arrays). Clear parallelization win."

# Agent Teams recommended:
team_lead_responsibilities:
  - "Create shared task list with one task per post from post_plan"
  - "Spawn 4-6 copywriter teammates (one per post) with scoped briefs"
  - "Collect all generated posts"
  - "Merge into single content_pack JSON array"
  - "Pass merged content to reviewer-specialist for quality gates"

teammates:
  - name: "copywriter-teammate-reel-1"
    task: "Generate Instagram reel concept #1 (product spotlight) with hook, caption, CTA, hashtags, creative brief, image prompt. Match brand voice from brand_profile. Use weekly_theme context. Output JSON."
    inputs: "brand_profile, weekly_theme, content_brief for reel 1, extracted reference data"
    outputs: "Post JSON with all fields (hook, caption, cta, hashtags, creative_brief, image_prompt, alt_text)"

  - name: "copywriter-teammate-reel-2"
    task: "Generate Instagram reel concept #2 (behind the scenes) with hook, caption, CTA, hashtags, creative brief, image prompt. Match brand voice. Output JSON."
    inputs: "brand_profile, weekly_theme, content_brief for reel 2, extracted reference data"
    outputs: "Post JSON"

  - name: "copywriter-teammate-reel-3"
    task: "Generate Instagram reel concept #3 (customer story) with hook, caption, CTA, hashtags, creative brief, image prompt. Match brand voice. Output JSON."
    inputs: "brand_profile, weekly_theme, content_brief for reel 3, extracted reference data"
    outputs: "Post JSON"

  - name: "copywriter-teammate-carousel-1"
    task: "Generate Instagram carousel post #1 (style guide, 5 slides) with hook, caption for each slide, overall CTA, hashtags, creative brief for each slide. Match brand voice. Output JSON."
    inputs: "brand_profile, weekly_theme, content_brief for carousel 1"
    outputs: "Carousel post JSON with slides array"

  - name: "copywriter-teammate-carousel-2"
    task: "Generate Instagram carousel post #2 (impact stats, 5 slides) with hook, caption per slide, CTA, hashtags, creative briefs. Match brand voice. Output JSON."
    inputs: "brand_profile, weekly_theme, content_brief for carousel 2, extracted reference data (metrics)"
    outputs: "Carousel post JSON"

  - name: "copywriter-teammate-single-1"
    task: "Generate Instagram single image post (quote graphic) with hook, caption, CTA, hashtags, creative brief, alt text. Match brand voice. Output JSON."
    inputs: "brand_profile, weekly_theme, content_brief for single image"
    outputs: "Post JSON"

# Sequential fallback:
sequential_rationale: "If Agent Teams is disabled or fails, generate posts sequentially using copywriter-specialist. Same output, 6x slower (acceptable for weekly schedule). All posts still generated, reviewed, and published/packaged."
```

### GitHub Actions Triggers

```yaml
triggers:
  - type: "schedule"
    config: "cron: '0 9 * * 1'  # Every Monday at 09:00 UTC"
    description: "Weekly automated content generation every Monday morning"

  - type: "workflow_dispatch"
    config: |
      inputs:
        weekly_theme:
          description: 'This week content theme'
          required: true
        publishing_mode:
          description: 'auto_publish or content_pack_only'
          required: true
          default: 'content_pack_only'
        post_plan_json:
          description: 'JSON post plan (optional, uses default if empty)'
          required: false
    description: "Manual trigger for on-demand content generation (campaigns, special events)"

  - type: "issues (Agent HQ)"
    config: "assigned to @claude with label 'instagram-content'"
    description: "Issue-driven content generation — paste theme and post plan in issue body"
```

---

## Implementation Blueprint

### Workflow Steps

```yaml
steps:
  - name: "Load Configuration"
    description: "Read brand profile, weekly theme, post plan, reference links from repo or workflow inputs"
    subagent: "none (main agent)"
    tools: ["read_config.py"]
    inputs: "Repo files at config/ OR workflow_dispatch inputs"
    outputs: "Loaded config (JSON) with brand_profile, weekly_theme, post_plan, reference_links, publishing_mode"
    failure_mode: "Config file missing or malformed JSON"
    fallback: "Use workflow_dispatch inputs if files missing; fail with clear error if inputs also missing"

  - name: "Scrape Reference Content"
    description: "Extract content from reference URLs for factual accuracy in posts"
    subagent: "reference-scraper-specialist"
    tools: ["scrape_references.py"]
    inputs: "reference_links array from config"
    outputs: "Extracted reference data (JSON) with url, context, text, key_facts, status per URL"
    failure_mode: "URL unreachable, paywall, Firecrawl API quota exceeded"
    fallback: "HTTP + BeautifulSoup fallback; if all scraping fails, continue with empty reference data (posts will be generic)"

  - name: "Plan Content Strategy"
    description: "Analyze brand profile and theme to create detailed content briefs for each post"
    subagent: "content-strategist"
    tools: ["plan_content.py"]
    inputs: "brand_profile, weekly_theme, post_plan, extracted reference data"
    outputs: "Content briefs array (JSON) with one brief per post: post_id, type, topic, hook_angle, target_audience, reference_data_refs"
    failure_mode: "Post plan is ambiguous or conflicts with brand guardrails"
    fallback: "Generate generic content briefs based on post types only; log warning for review"

  - name: "Generate Post Content (Parallel with Agent Teams)"
    description: "Generate Instagram posts in parallel — each teammate creates one post with caption, hashtags, creative brief"
    subagent: "copywriter-specialist (team lead) + copywriter-teammates (parallel execution)"
    tools: ["generate_content.py (uses Agent Teams if enabled)"]
    inputs: "Content briefs array, brand_profile, extracted reference data"
    outputs: "Generated posts array (JSON) with hook, caption, cta, hashtags, creative_brief, image_prompt, alt_text per post"
    failure_mode: "LLM API failure, rate limit, token limit exceeded"
    fallback: "Retry with exponential backoff (3 attempts); if Agent Teams fails, fall back to sequential generation; if all fails, halt with error"

  - name: "Validate Hashtags"
    description: "Verify all hashtags meet Instagram guidelines and brand strategy"
    subagent: "hashtag-specialist"
    tools: ["validate_hashtags.py"]
    inputs: "Generated posts with hashtags"
    outputs: "Validated posts with hashtags (replaced banned tags, ensured count 10-30 per post)"
    failure_mode: "Hashtag API unreachable (if using external hashtag validation service)"
    fallback: "Use local banned hashtag list; validate count only; log warning if external validation unavailable"

  - name: "Review Content Quality"
    description: "Run quality gates: brand voice, prohibited claims, banned topics, format compliance"
    subagent: "reviewer-specialist"
    tools: ["review_content.py"]
    inputs: "All generated posts, brand_profile with guardrails"
    outputs: "Review report (JSON + Markdown) with per-post pass/fail, scores, compliance issues; approved_posts array (only posts that passed)"
    failure_mode: "All posts fail review (e.g., severe brand voice mismatch)"
    fallback: "Regenerate failed posts with feedback (max 2 retry cycles); if still failing, halt and notify for manual review"

  - name: "Publish to Instagram OR Prepare Content Pack"
    description: "If auto_publish: call Instagram Graph API; if content_pack_only: format manual upload pack"
    subagent: "publisher-specialist (if auto_publish) OR none (if content_pack_only)"
    tools: ["publish_to_instagram.py", "format_content_pack.py"]
    inputs: "Approved posts, publishing_mode, INSTAGRAM_ACCESS_TOKEN (if auto_publish)"
    outputs: "publish_log.json (if auto_publish) OR upload_checklist.md (if content_pack_only)"
    failure_mode: "Instagram API rate limit, auth failure, invalid media format"
    fallback: "Retry with backoff (3 attempts); if all publish attempts fail, fall back to content_pack_only mode and generate manual pack"

  - name: "Archive and Index"
    description: "Save all artifacts to output/instagram/ and update rolling archive index"
    subagent: "none (main agent)"
    tools: ["archive_content.py"]
    inputs: "Generated content_pack JSON, review report, publish log (if any)"
    outputs: "content_pack_{date}.md, content_pack_{date}.json, review_report_{date}.md, publish_log_{date}.json (if auto_publish), archive/latest.md (updated)"
    failure_mode: "Filesystem write error, Git commit failure"
    fallback: "Retry write; if fails, log error but do not halt (content is in memory, can be manually saved)"

  - name: "Commit Results"
    description: "Stage and commit all output files to the repo"
    subagent: "none (main agent)"
    tools: ["git_commit.sh"]
    inputs: "All files in output/instagram/"
    outputs: "Git commit with message 'chore(instagram): weekly content pack YYYY-MM-DD'"
    failure_mode: "Git push rejected (merge conflict, branch protection)"
    fallback: "Retry push with rebase; if fails, open PR instead of direct push; notify human if PR required"
```

### Tool Specifications

```yaml
tools:
  - name: "read_config.py"
    purpose: "Load brand profile, weekly theme, post plan, reference links from repo files or workflow inputs"
    catalog_pattern: "json_read_write (catalog pattern)"
    inputs:
      - "config_dir: str — Path to config directory (default: config/)"
      - "workflow_inputs: dict — Workflow dispatch inputs (optional override)"
    outputs: "JSON object with brand_profile, weekly_theme, post_plan, reference_links, publishing_mode"
    dependencies: ["json (stdlib)", "pathlib (stdlib)"]
    mcp_used: "filesystem"
    error_handling: "FileNotFoundError → check workflow_inputs; JSONDecodeError → clear error with file path and line number"

  - name: "scrape_references.py"
    purpose: "Scrape reference URLs via Firecrawl (primary) or HTTP+BeautifulSoup (fallback) to extract content"
    catalog_pattern: "firecrawl_scrape (catalog pattern with HTTP fallback)"
    inputs:
      - "reference_links: list[dict] — Array of {url, context} objects"
      - "api_key: str — Firecrawl API key from env (FIRECRAWL_API_KEY)"
    outputs: "JSON array of {url, context, extracted_text, key_facts, status} objects"
    dependencies: ["firecrawl-py", "httpx", "beautifulsoup4"]
    mcp_used: "firecrawl (primary), fetch (fallback)"
    error_handling: "ConnectionError → try HTTP fallback; rate limit → log warning, skip URL; paywall detected → log warning, mark as 'inaccessible'"

  - name: "plan_content.py"
    purpose: "Generate content briefs for each post based on brand profile and weekly theme"
    catalog_pattern: "llm_prompt (catalog pattern)"
    inputs:
      - "brand_profile: dict — Brand voice and guardrails"
      - "weekly_theme: str — This week's content focus"
      - "post_plan: dict — Types and counts of posts to create"
      - "reference_data: list[dict] — Extracted reference content"
    outputs: "JSON array of content briefs with post_id, type, topic, hook_angle, target_audience, reference_data_refs"
    dependencies: ["anthropic or openai"]
    mcp_used: "anthropic"
    error_handling: "LLM API error → retry with backoff (3 attempts); if all fail, generate generic briefs based on post types only"

  - name: "generate_content.py"
    purpose: "Generate Instagram posts with captions, hashtags, creative briefs (uses Agent Teams for parallel execution if enabled)"
    catalog_pattern: "structured_extract (catalog pattern) + Agent Teams coordination"
    inputs:
      - "content_briefs: list[dict] — Content strategy for each post"
      - "brand_profile: dict — Brand voice guidelines"
      - "reference_data: list[dict] — Scraped reference content"
      - "enable_agent_teams: bool — Whether to use parallel generation (env var or config)"
    outputs: "JSON array of posts with hook, caption, cta, hashtags, creative_brief, image_prompt, alt_text"
    dependencies: ["anthropic or openai"]
    mcp_used: "anthropic"
    error_handling: "LLM timeout → retry; if Agent Teams fails, fall back to sequential; validate JSON schema for each post, retry if invalid (max 2 retries per post)"

  - name: "validate_hashtags.py"
    purpose: "Check hashtags against banned list, ensure count 10-30, replace banned tags with alternatives"
    catalog_pattern: "filter_sort (catalog pattern with custom validation)"
    inputs:
      - "posts: list[dict] — Generated posts with hashtags"
      - "banned_hashtags: list[str] — Known banned/flagged Instagram hashtags (from config or hardcoded list)"
      - "brand_strategy: dict — Brand hashtag strategy from brand_profile"
    outputs: "JSON array of posts with validated/corrected hashtags"
    dependencies: ["None (stdlib only)"]
    mcp_used: "none"
    error_handling: "If hashtag count < 10, generate additional relevant tags; if > 30, truncate to 30 with log warning"

  - name: "review_content.py"
    purpose: "Run quality gates on generated content: brand voice scoring, prohibited claims detection, format validation"
    catalog_pattern: "llm_prompt (for brand voice scoring) + custom validation logic"
    inputs:
      - "posts: list[dict] — All generated posts"
      - "brand_profile: dict — Brand guardrails (prohibited_claims, banned_topics, do/dont lists)"
    outputs: "JSON review report with per-post scores (brand_voice_score, compliance_status) + Markdown report for human review"
    dependencies: ["anthropic or openai"]
    mcp_used: "anthropic"
    error_handling: "If all posts fail, log detailed feedback and halt; if some fail, return approved posts only and log failed posts with reasons"

  - name: "publish_to_instagram.py"
    purpose: "Publish approved posts to Instagram via Graph API with rate limiting and retry logic"
    catalog_pattern: "rest_client (catalog pattern) with Instagram-specific logic"
    inputs:
      - "posts: list[dict] — Approved posts to publish"
      - "access_token: str — Instagram Graph API access token (env var INSTAGRAM_ACCESS_TOKEN)"
      - "ig_user_id: str — Instagram Business account user ID (env var INSTAGRAM_USER_ID)"
    outputs: "JSON publish log with per-post results (media_id, permalink, or error)"
    dependencies: ["httpx", "tenacity (for retry)"]
    mcp_used: "fetch"
    error_handling: "Rate limit (429) → exponential backoff, max 5 retries; auth error (401) → halt with clear token error; network error → retry 3 times; if all posts fail, return error log and recommend content_pack_only fallback"

  - name: "format_content_pack.py"
    purpose: "Format generated posts into human-readable Markdown content pack and manual upload checklist"
    catalog_pattern: "transform_map (catalog pattern) + Markdown templating"
    inputs:
      - "posts: list[dict] — Approved posts"
      - "weekly_theme: str"
      - "date: str — Generation date"
    outputs: "Markdown files: content_pack_{date}.md (formatted posts) and upload_checklist_{date}.md (step-by-step manual upload)"
    dependencies: ["jinja2 (templating)"]
    mcp_used: "filesystem"
    error_handling: "Template rendering error → use plain text fallback format; file write error → retry once, then fail with error"

  - name: "archive_content.py"
    purpose: "Copy all generated files to archive directory and update rolling latest.md index"
    catalog_pattern: "file I/O (stdlib)"
    inputs:
      - "content_pack_json: dict — Full content pack data"
      - "output_dir: str — Path to output/instagram/"
      - "date: str — Generation date"
    outputs: "Updated archive/latest.md with links to 10 most recent content packs"
    dependencies: ["pathlib (stdlib)", "json (stdlib)"]
    mcp_used: "filesystem"
    error_handling: "File write error → retry; if archive fails, continue (content is already in main output dir)"

  - name: "git_commit.sh"
    purpose: "Stage and commit all output files to the repo"
    catalog_pattern: "git_commit_push (catalog pattern)"
    inputs:
      - "file_paths: list[str] — Specific files to commit"
      - "commit_message: str — Commit message"
    outputs: "Git commit SHA"
    dependencies: ["git CLI"]
    mcp_used: "none (subprocess)"
    error_handling: "Push rejected → retry with rebase; if still fails, open PR instead of direct push"
```

### Per-Tool Pseudocode

```python
# read_config.py
def main():
    # PATTERN: json_read_write
    # Load config files from repo OR workflow inputs
    args = parse_args()  # --config-dir, --workflow-inputs (JSON string)
    
    # Try repo files first
    try:
        brand_profile = json.loads(Path(args.config_dir, "brand_profile.json").read_text())
        weekly_theme = Path(args.config_dir, "weekly_theme.txt").read_text().strip()
        post_plan = json.loads(Path(args.config_dir, "post_plan.json").read_text())
        reference_links = json.loads(Path(args.config_dir, "reference_links.json").read_text())
        publishing_mode = os.environ.get("PUBLISHING_MODE", "content_pack_only")
    except FileNotFoundError:
        # Fall back to workflow inputs
        if not args.workflow_inputs:
            raise ValueError("Config files missing and no workflow inputs provided")
        inputs = json.loads(args.workflow_inputs)
        brand_profile = inputs["brand_profile"]
        weekly_theme = inputs["weekly_theme"]
        # ... etc
    
    # Output
    print(json.dumps({
        "brand_profile": brand_profile,
        "weekly_theme": weekly_theme,
        "post_plan": post_plan,
        "reference_links": reference_links,
        "publishing_mode": publishing_mode
    }))

# scrape_references.py
def main():
    # PATTERN: firecrawl_scrape with HTTP fallback
    # CRITICAL: Firecrawl has usage limits — implement fallback
    args = parse_args()  # --reference-links (JSON string)
    reference_links = json.loads(args.reference_links)
    
    results = []
    for ref in reference_links:
        try:
            # Try Firecrawl first
            data = firecrawl_scrape(ref["url"], os.environ["FIRECRAWL_API_KEY"])
            results.append({
                "url": ref["url"],
                "context": ref["context"],
                "extracted_text": data["markdown"],
                "key_facts": extract_key_facts(data["markdown"]),  # LLM or regex
                "status": "success"
            })
        except RateLimitError:
            # Fall back to HTTP + BeautifulSoup
            data = http_scrape(ref["url"])
            results.append({..., "status": "fallback"})
        except Exception as e:
            # Log and continue
            results.append({..., "status": "failed", "error": str(e)})
    
    print(json.dumps(results))

# generate_content.py
def main():
    # PATTERN: structured_extract + Agent Teams
    # CRITICAL: Claude has 8k output token limit — batch posts to avoid hitting limit
    args = parse_args()  # --content-briefs, --brand-profile, --reference-data, --enable-agent-teams
    
    if args.enable_agent_teams and len(content_briefs) >= 3:
        # Use Agent Teams for parallel generation
        posts = generate_with_agent_teams(content_briefs, brand_profile, reference_data)
    else:
        # Sequential generation
        posts = []
        for brief in content_briefs:
            post = generate_single_post(brief, brand_profile, reference_data)
            posts.append(post)
    
    # Validate each post JSON schema
    for post in posts:
        validate_post_schema(post)  # raises if invalid
    
    print(json.dumps(posts))

def generate_single_post(brief, brand_profile, reference_data):
    # Use structured_extract pattern with JSON schema
    schema = {...}  # post schema with hook, caption, cta, hashtags, etc.
    prompt = build_post_prompt(brief, brand_profile, reference_data)
    result = structured_extract(prompt, schema, retries=2)
    return result["data"]

# review_content.py
def main():
    # PATTERN: LLM-based scoring + rule-based validation
    # Brand voice scoring uses Claude with reference examples
    # Prohibited claims uses keyword matching + Claude verification
    args = parse_args()  # --posts, --brand-profile
    
    review_report = {
        "overall_status": "PENDING",
        "per_post_results": [],
        "approved_posts": [],
        "failed_posts": []
    }
    
    for post in posts:
        score = score_brand_voice(post, brand_profile)  # 0-100% via LLM
        claims = detect_prohibited_claims(post, brand_profile)  # keyword scan
        topics = detect_banned_topics(post, brand_profile)  # keyword scan
        format_ok = validate_format(post)  # caption length, hashtag placement
        
        passed = (score >= 85 and not claims and not topics and format_ok)
        
        review_report["per_post_results"].append({
            "post_id": post["post_id"],
            "brand_voice_score": score,
            "prohibited_claims": claims,
            "banned_topics": topics,
            "format_compliance": format_ok,
            "status": "PASS" if passed else "FAIL"
        })
        
        if passed:
            review_report["approved_posts"].append(post)
        else:
            review_report["failed_posts"].append(post)
    
    review_report["overall_status"] = "PASS" if len(review_report["failed_posts"]) == 0 else "FAIL"
    
    print(json.dumps(review_report))

# publish_to_instagram.py
def main():
    # PATTERN: rest_client with Instagram Graph API
    # CRITICAL: Rate limit is 200 calls/hour — implement retry with backoff
    # CRITICAL: Instagram does NOT support scheduled posts via API — must be immediate
    args = parse_args()  # --posts, --access-token, --ig-user-id
    
    publish_log = {
        "published_at": datetime.utcnow().isoformat(),
        "mode": "auto_publish",
        "results": []
    }
    
    for post in posts:
        try:
            # Create media container
            result = create_ig_media(post, args.access_token, args.ig_user_id)
            publish_log["results"].append({
                "post_id": post["post_id"],
                "status": "success",
                "ig_media_id": result["id"],
                "permalink": result.get("permalink")
            })
        except RateLimitError as e:
            # Retry with exponential backoff
            time.sleep(60)  # wait 1 minute, then retry
            # ... retry logic
        except Exception as e:
            publish_log["results"].append({
                "post_id": post["post_id"],
                "status": "failed",
                "error": str(e)
            })
    
    print(json.dumps(publish_log))
```

### Integration Points

```yaml
SECRETS:
  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API for content generation and brand voice scoring"
    required: true

  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API for scraping reference URLs"
    required: false (has HTTP fallback)

  - name: "INSTAGRAM_ACCESS_TOKEN"
    purpose: "Instagram Graph API access token for publishing posts"
    required: true (if auto_publish mode)

  - name: "INSTAGRAM_USER_ID"
    purpose: "Instagram Business account user ID for media creation"
    required: true (if auto_publish mode)

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "ANTHROPIC_API_KEY=your_api_key_here  # Required: Claude API key"
      - "FIRECRAWL_API_KEY=your_api_key_here  # Optional: Firecrawl for reference scraping (has fallback)"
      - "INSTAGRAM_ACCESS_TOKEN=your_token_here  # Required if auto_publish: IG Graph API token"
      - "INSTAGRAM_USER_ID=your_user_id_here  # Required if auto_publish: IG Business account ID"
      - "PUBLISHING_MODE=content_pack_only  # auto_publish or content_pack_only"
      - "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=true  # Enable Agent Teams for parallel generation"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "anthropic>=0.40.0  # Claude API client"
      - "firecrawl-py>=0.0.20  # Firecrawl scraping API"
      - "httpx>=0.27.0  # HTTP client for Instagram API and fallback scraping"
      - "beautifulsoup4>=4.12.0  # HTML parsing for fallback scraping"
      - "tenacity>=8.0.0  # Retry logic with exponential backoff"
      - "jinja2>=3.1.0  # Templating for content pack markdown"
      - "jsonschema>=4.0.0  # JSON schema validation for post structure"

GITHUB_ACTIONS:
  - trigger: "schedule"
    config: "cron: '0 9 * * 1'  # Every Monday at 09:00 UTC"
  - trigger: "workflow_dispatch"
    config: "Inputs: weekly_theme (string, required), publishing_mode (choice, default content_pack_only), post_plan_json (string, optional)"
```

---

## Validation Loop

### Level 1: Syntax & Structure

```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/read_config.py').read())"
python -c "import ast; ast.parse(open('tools/scrape_references.py').read())"
python -c "import ast; ast.parse(open('tools/plan_content.py').read())"
python -c "import ast; ast.parse(open('tools/generate_content.py').read())"
python -c "import ast; ast.parse(open('tools/validate_hashtags.py').read())"
python -c "import ast; ast.parse(open('tools/review_content.py').read())"
python -c "import ast; ast.parse(open('tools/publish_to_instagram.py').read())"
python -c "import ast; ast.parse(open('tools/format_content_pack.py').read())"
python -c "import ast; ast.parse(open('tools/archive_content.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.read_config')"
python -c "import importlib; importlib.import_module('tools.scrape_references')"
# ... repeat for all tools

# Structure check — verify main() exists
python -c "from tools.read_config import main; assert callable(main)"
python -c "from tools.scrape_references import main; assert callable(main)"
# ... repeat for all tools

# Subagent file validation
python -c "import yaml; yaml.safe_load(open('.claude/agents/content-strategist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/reference-scraper-specialist.md').read().split('---')[1])"
# ... repeat for all subagent files

# YAML validation for GitHub Actions
python -c "import yaml; yaml.safe_load(open('.github/workflows/weekly_instagram_content.yml').read())"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests

```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test each tool independently with mock/sample data

# Test read_config
python tools/read_config.py --config-dir test_fixtures/config/
# Expected output: Valid JSON with brand_profile, weekly_theme, post_plan, reference_links, publishing_mode

# Test scrape_references (mock mode — no actual API calls)
python tools/scrape_references.py --reference-links '[{"url": "https://example.com/blog", "context": "test"}]' --mock
# Expected output: JSON array with extracted_text field (mocked content)

# Test plan_content (with sample brand profile)
python tools/plan_content.py --brand-profile-path test_fixtures/config/brand_profile.json --weekly-theme "Test Theme" --post-plan-path test_fixtures/config/post_plan.json
# Expected output: JSON array of content briefs with post_id, type, topic fields

# Test generate_content (mock LLM mode)
python tools/generate_content.py --content-briefs '[{"post_id": "test_001", "type": "reel_concept", "topic": "product spotlight"}]' --brand-profile-path test_fixtures/config/brand_profile.json --mock
# Expected output: JSON array of posts with hook, caption, cta, hashtags, creative_brief

# Test validate_hashtags
python tools/validate_hashtags.py --posts '[{"post_id": "test_001", "hashtags": ["#EcoStyle", "#Sustainable", "#BANNED_TAG"]}]'
# Expected output: JSON array with BANNED_TAG removed, validated count

# Test review_content (mock LLM scoring)
python tools/review_content.py --posts-path test_fixtures/generated_posts.json --brand-profile-path test_fixtures/config/brand_profile.json --mock
# Expected output: JSON review report with per-post scores, overall status

# Test format_content_pack
python tools/format_content_pack.py --posts-path test_fixtures/generated_posts.json --weekly-theme "Test Theme" --date "2026-02-17"
# Expected output: Markdown file written to output/instagram/content_pack_2026-02-17.md

# If any tool fails: Read the error, fix the root cause, re-run.
```

### Level 3: Integration Tests

```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with sample data

# Step 1: Load config
python tools/read_config.py --config-dir test_fixtures/config/ > /tmp/config.json

# Step 2: Scrape references (mock mode)
python tools/scrape_references.py --reference-links "$(jq -c '.reference_links' /tmp/config.json)" --mock > /tmp/reference_data.json

# Step 3: Plan content
python tools/plan_content.py \
  --brand-profile-path test_fixtures/config/brand_profile.json \
  --weekly-theme "$(jq -r '.weekly_theme' /tmp/config.json)" \
  --post-plan-path test_fixtures/config/post_plan.json \
  --reference-data-path /tmp/reference_data.json \
  > /tmp/content_briefs.json

# Step 4: Generate posts (mock LLM, no Agent Teams for integration test)
python tools/generate_content.py \
  --content-briefs-path /tmp/content_briefs.json \
  --brand-profile-path test_fixtures/config/brand_profile.json \
  --mock \
  --enable-agent-teams false \
  > /tmp/generated_posts.json

# Step 5: Validate hashtags
python tools/validate_hashtags.py --posts-path /tmp/generated_posts.json > /tmp/validated_posts.json

# Step 6: Review content
python tools/review_content.py \
  --posts-path /tmp/validated_posts.json \
  --brand-profile-path test_fixtures/config/brand_profile.json \
  --mock \
  > /tmp/review_report.json

# Step 7: Verify approved posts exist
python -c "
import json
report = json.load(open('/tmp/review_report.json'))
assert report['overall_status'] == 'PASS', 'Integration test failed: no approved posts'
assert len(report['approved_posts']) > 0, 'No posts approved'
print('Integration test passed: {} posts approved'.format(len(report['approved_posts'])))
"

# Verify workflow.md references match actual tool files
python -c "
import re, pathlib
workflow = pathlib.Path('workflow.md').read_text()
tool_refs = re.findall(r'tools/(\w+\.py)', workflow)
for tool in tool_refs:
    assert pathlib.Path(f'tools/{tool}').exists(), f'workflow.md references missing tool: {tool}'
print('All workflow tool references valid')
"

# Verify CLAUDE.md documents all subagents
python -c "
import pathlib
claude_md = pathlib.Path('CLAUDE.md').read_text()
subagents = [p.stem for p in pathlib.Path('.claude/agents/').glob('*.md')]
for subagent in subagents:
    assert subagent in claude_md, f'CLAUDE.md does not document subagent: {subagent}'
print('All subagents documented in CLAUDE.md')
"
```

---

## Final Validation Checklist

- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes and failure notifications
- [ ] .env.example lists all required environment variables
- [ ] .gitignore excludes .env, __pycache__/, credentials, output/ (except .gitkeep)
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies
- [ ] Instagram Graph API rate limiting (200 calls/hour) is handled with retry + backoff
- [ ] All caption lengths validated before API call (≤ 2200 chars)
- [ ] Brand voice scoring threshold is 85%+ for approval
- [ ] Fallback from auto_publish to content_pack_only on persistent failures

---

## Anti-Patterns to Avoid

- Do not hardcode Instagram access tokens — use GitHub Secrets or .env
- Do not skip quality review because "it should match brand voice" — always run review gates
- Do not fail the entire pipeline if one post generation fails — continue with successful posts
- Do not use Agent Teams when fewer than 3 posts are being generated — overhead not justified
- Do not call Instagram API without retry logic — rate limits WILL happen
- Do not generate captions longer than 2200 characters — validate before API call
- Do not use banned hashtags — maintain and check against banned list
- Do not skip the fallback to content_pack_only if auto_publish fails — always provide manual pack option
- Do not commit Instagram access tokens or API responses with sensitive data — sanitize logs
- Do not ignore Firecrawl rate limits — implement HTTP fallback for reference scraping
- Do not regenerate posts infinitely — max 2 retry cycles, then halt for manual review
- Do not use generic hashtags only — mix broad (100k+ posts) and niche (5k-50k) for better reach

---

## Confidence Score: 9/10

**Score rationale:**
- **Workflow clarity**: High confidence — Generate > Review > Publish pattern is well-established, all steps are clearly defined with failure modes
- **Tool implementations**: High confidence — All tools follow catalog patterns (firecrawl_scrape, structured_extract, rest_client), dependencies are known and documented
- **Instagram API integration**: Medium-high confidence — Instagram Graph API is well-documented, but access token management and rate limiting require careful implementation. Fallback to content_pack_only mitigates risk.
- **Brand voice scoring**: Medium-high confidence — LLM-based brand voice scoring is subjective, but 85% threshold with retry cycles provides reasonable quality control
- **Agent Teams parallelization**: High confidence — 6 independent post generation tasks with clear merge logic, proven pattern from previous builds (marketing-pipeline, blog-repurpose)
- **Subagent architecture**: High confidence — 6 specialist subagents with clear domains, sequential delegation, no circular dependencies

**Ambiguity flags** (areas requiring clarification before building):
- [ ] **Instagram API access token lifecycle**: How often does the token expire? Is there a refresh token mechanism, or manual rotation? This affects the publisher-specialist error handling.
  - **Recommendation**: Document token rotation instructions in README.md; if Graph API supports refresh tokens, implement auto-refresh in publish_to_instagram.py
- [ ] **Sample brand profile**: Does the user have a sample brand_profile.json with actual brand voice examples for brand voice scoring? The LLM needs reference posts to compare against.
  - **Recommendation**: Include a template brand_profile.json in test_fixtures/ with example fields; if user provides real examples, scoring will be more accurate
- [ ] **Image/video media**: The PRP mentions "image prompts" and "creative briefs" but does not specify whether the system should GENERATE actual images/videos (e.g., via DALL-E, Midjourney) or just provide prompts for manual creation.
  - **Recommendation**: Default to "prompts only" mode (creative_brief + image_prompt fields in JSON); add a future enhancement flag for AI image generation via Replicate/DALL-E if requested

**If any ambiguity flag is checked, clarify with the user before proceeding to build.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/weekly-instagram-content-publisher.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
