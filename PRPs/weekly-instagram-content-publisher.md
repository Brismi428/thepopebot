name: "Weekly Instagram Content Publisher"
description: |

## Purpose
A weekly social media automation system that generates Instagram-ready content packs (captions, hashtags, creative briefs, and optional image prompts) based on a brand voice and weekly theme, runs quality review checks, and either publishes via the Instagram Graph API or prepares a "ready-to-post" pack for manual upload.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a fully autonomous weekly Instagram content generation and publishing system that:
- Generates high-quality, brand-aligned Instagram posts (reels, carousels, single images)
- Runs comprehensive quality checks before publishing
- Publishes directly via Instagram Graph API OR outputs manual-upload packs
- Maintains a rolling archive of all generated content
- Runs reliably via GitHub Actions cron, manual dispatch, or Agent HQ

Success means: A marketing team can define a brand profile once, set a weekly schedule, and receive 5-10 fully-vetted, Instagram-optimized posts every Monday at 9 AM UTC — ready to publish with one click or automatically posted to their Instagram Business account.

## Why
- **Saves 8-12 hours/week** of content creation and scheduling work for small marketing teams
- **Ensures brand consistency** through automated voice/compliance checks
- **Reduces posting friction** by generating complete content packs with all metadata
- **Prevents brand damage** by catching prohibited claims, banned topics, and off-brand content before publishing
- **Scales content production** for agencies managing multiple client accounts

Target users: Small business marketing teams, social media managers, agencies with 3+ clients

## What
A scheduled content generation pipeline that:
1. Reads brand profile (voice, guardrails, target audience)
2. Fetches optional reference content from URLs (blogs, product pages)
3. Generates 3-7 Instagram posts per week based on weekly theme and post plan
4. Runs a two-pass quality review (brand voice, compliance, format validation)
5. Publishes to Instagram Graph API (if auto_publish enabled and secrets present) OR outputs manual upload pack
6. Commits all outputs to repo with rolling archive

### Success Criteria
- [ ] Generates complete content packs with captions, hashtags, CTAs, alt text, creative briefs
- [ ] Review pass catches 100% of banned topics, prohibited claims, and format violations
- [ ] Auto-publish succeeds when credentials are valid and mode is enabled
- [ ] Manual fallback outputs are complete and usable when auto-publish is disabled or fails
- [ ] System runs autonomously via GitHub Actions on schedule
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ
- [ ] Content pack quality is indistinguishable from human-written posts for the target brand

---

## Inputs
[What goes into the system. Be specific about format, source, and any validation requirements.]

```yaml
- name: "brand_profile"
  type: "JSON"
  source: "File at inputs/brand_profile.json"
  required: true
  description: "Complete brand voice definition with guardrails"
  example: |
    {
      "brand_name": "Acme Fitness Co.",
      "voice_description": "Motivational, authentic, science-backed. Speaks like a supportive coach, not a salesperson.",
      "tone": "Energetic but not pushy. Friendly, conversational, evidence-based.",
      "target_audience": "30-45 year old professionals seeking sustainable fitness habits",
      "products_services": ["Online coaching programs", "Meal planning app", "Fitness gear"],
      "do_list": ["Use data and research to back claims", "Share client success stories", "Use emojis sparingly (1-2 per post)", "End with clear CTA"],
      "dont_list": ["Make medical claims", "Use aggressive sales language", "Mention competitors", "Use excessive hashtags (>15)", "Promise unrealistic results"],
      "banned_topics": ["Weight loss drugs", "Extreme diets", "Body shaming", "Politics", "Religion"],
      "preferred_cta": ["Link in bio", "DM us to get started", "Save this for later", "Tag a friend who needs this"],
      "emoji_style": "Minimal (1-2 per post)",
      "hashtag_strategy": "Mix of 8-12 hashtags: 40% niche, 40% mid-tier, 20% broad"
    }

- name: "weekly_theme"
  type: "string"
  source: "Workflow input or config file"
  required: true
  description: "The focus/topic for this week's posts (e.g., 'spring launch', 'behind the scenes', 'customer stories')"
  example: "Myth-busting Monday: Debunking common fitness misconceptions"

- name: "post_plan"
  type: "JSON"
  source: "Workflow input or config file"
  required: true
  description: "Number and types of posts to create, plus any required series/templates"
  example: |
    {
      "posts": [
        {"type": "reel", "hook_style": "question", "length": "30-60s", "focus": "myth debunking"},
        {"type": "reel", "hook_style": "bold_statement", "length": "30-60s", "focus": "quick tip"},
        {"type": "carousel", "slides": 5, "focus": "educational breakdown"},
        {"type": "carousel", "slides": 3, "focus": "client transformation story"},
        {"type": "single_image", "focus": "motivational quote with brand tie-in"}
      ],
      "series_tags": ["MythBustingMonday"],
      "required_mentions": []
    }

- name: "reference_links"
  type: "JSON array"
  source: "Optional workflow input"
  required: false
  description: "URLs to recent blog posts, announcements, or product pages to pull accurate details from"
  example: |
    [
      {"url": "https://acmefitness.com/blog/cardio-myths", "context": "Use for myth-busting content"},
      {"url": "https://acmefitness.com/spring-launch", "context": "Mention new spring program"}
    ]

- name: "publishing_mode"
  type: "choice"
  source: "Workflow input or config file"
  required: true
  description: "Whether to auto-publish to Instagram or output manual upload pack"
  example: "auto_publish or content_pack_only"
  options: ["auto_publish", "content_pack_only"]
```

## Outputs
[What comes out of the system. Where do results go?]

```yaml
- name: "content_pack_markdown"
  type: "Markdown"
  destination: "output/instagram/content_pack_{YYYY-MM-DD}.md"
  description: "Human-readable weekly content pack with all posts formatted for easy review"
  example: |
    # Instagram Content Pack — 2026-02-14
    ## Post 1: Reel — Myth-Busting Monday
    **Hook**: "Think cardio is the only way to lose weight? Think again 🤔"
    **Caption**: [Full caption with emojis, line breaks, CTA]
    **Hashtags**: #FitnessMythBusting #CardioMyths #StrengthTraining ...
    **Alt Text**: "Fitness coach debunking cardio myths on camera"
    **Creative Brief**: 30s reel, on-camera talking head, text overlays with myth vs reality...
    **Suggested Post Time**: Monday 6 PM EST

- name: "content_pack_json"
  type: "JSON"
  destination: "output/instagram/content_pack_{YYYY-MM-DD}.json"
  description: "Structured data for each post — machine-readable for automation or CMS ingestion"
  example: |
    {
      "generated_at": "2026-02-14T09:00:00Z",
      "brand": "Acme Fitness Co.",
      "theme": "Myth-busting Monday",
      "posts": [
        {
          "id": 1,
          "type": "reel",
          "hook": "...",
          "caption": "...",
          "hashtags": ["#FitnessMythBusting", ...],
          "alt_text": "...",
          "creative_brief": "...",
          "suggested_time": "Monday 6 PM EST",
          "character_count": 487
        }
      ]
    }

- name: "review_report"
  type: "Markdown"
  destination: "output/instagram/review_report_{YYYY-MM-DD}.md"
  description: "Quality review results with pass/fail status and detailed findings"
  example: |
    # Quality Review Report — 2026-02-14
    ## Brand Voice Match: PASS (92% confidence)
    ## Compliance Check: PASS
    - No banned topics detected
    - No prohibited claims detected
    - All CTAs match preferred list
    ## Format Validation: PASS
    - All captions under 2200 characters
    - Hashtag counts: 8-12 per post (within strategy)
    - Emoji counts: 1-2 per post (matches style guide)
    ## Flagged Items: None

- name: "publish_log"
  type: "JSON"
  destination: "output/instagram/publish_log_{YYYY-MM-DD}.json"
  description: "Publishing results or failure reasons (only when publishing_mode=auto_publish)"
  example: |
    {
      "mode": "auto_publish",
      "timestamp": "2026-02-14T09:15:23Z",
      "posts_attempted": 5,
      "posts_published": 5,
      "posts_failed": 0,
      "results": [
        {"post_id": 1, "instagram_media_id": "18234567890123456", "status": "published", "permalink": "https://instagram.com/p/..."},
        {"post_id": 2, "instagram_media_id": "18234567890123457", "status": "published", "permalink": "https://instagram.com/p/..."}
      ],
      "errors": []
    }

- name: "upload_checklist"
  type: "Markdown"
  destination: "output/instagram/upload_checklist_{YYYY-MM-DD}.md"
  description: "Manual upload steps with copy-paste ready content (only when publishing_mode=content_pack_only)"
  example: |
    # Instagram Upload Checklist — 2026-02-14
    ## Post 1: Reel — Myth-Busting Monday
    [ ] Record/edit video per creative brief
    [ ] Upload to Instagram as Reel
    [ ] Copy caption (below) and paste into Instagram
    [ ] Add hashtags (below)
    [ ] Set alt text (below)
    [ ] Schedule for Monday 6 PM EST or post immediately

- name: "latest_index"
  type: "Markdown"
  destination: "output/instagram/latest.md"
  description: "Lightweight index file pointing to most recent content pack"
  example: |
    # Latest Instagram Content Pack
    **Generated**: 2026-02-14 09:00 UTC
    **Theme**: Myth-busting Monday
    **Posts**: 5
    **View Pack**: [content_pack_2026-02-14.md](./content_pack_2026-02-14.md)
    **Review Report**: [review_report_2026-02-14.md](./review_report_2026-02-14.md)
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-user/media"
  why: "Instagram Graph API Media endpoint — POST method for publishing posts"

- url: "https://developers.facebook.com/docs/instagram-api/guides/content-publishing"
  why: "Content publishing guide with rate limits, image requirements, character limits"

- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-media"
  why: "IG Media object structure for tracking published posts"

- url: "https://docs.firecrawl.dev/api-reference/endpoint/scrape"
  why: "Firecrawl scraping endpoint for reference_links content extraction"

- url: "https://docs.anthropic.com/en/docs/agents-and-tools"
  why: "Claude API structured output for consistent JSON generation"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide the capabilities this system needs"

- doc: "library/patterns.md"
  why: "Select the best workflow pattern for this system"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns to adapt"
```

### Workflow Pattern Selection
```yaml
pattern: "Generate > Review > Publish"
rationale: "Perfect fit for content creation with quality gates. Two-pass generation ensures brand compliance before publishing. Matches proven pattern for AI-generated content."
modifications: |
  - Add reference content scraping step before generation (Intake > Enrich pattern)
  - Add dual output paths: auto-publish OR manual pack (conditional branching)
  - Add rolling archive management for content history
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "web scraping"
    primary_mcp: "firecrawl"
    alternative_mcp: "puppeteer"
    fallback: "Direct HTTP with requests + BeautifulSoup4"
    secret_name: "FIRECRAWL_API_KEY"

  - name: "llm_generation"
    primary_mcp: "none (direct API)"
    alternative_mcp: "none"
    fallback: "OpenAI API if ANTHROPIC_API_KEY unavailable"
    secret_name: "ANTHROPIC_API_KEY, OPENAI_API_KEY (fallback)"

  - name: "instagram_publishing"
    primary_mcp: "none (direct API)"
    alternative_mcp: "none"
    fallback: "Manual upload checklist output"
    secret_name: "INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID"
```

### Known Gotchas & Constraints
```
# CRITICAL: Instagram Graph API rate limit is 200 calls per hour per user. Each post = 2 calls (create container + publish). Budget 10 posts per run max.
# CRITICAL: Instagram captions have 2200 character limit. Hashtags count toward this limit. Must validate before attempting publish.
# CRITICAL: Instagram Graph API requires Facebook Page connected to Instagram Business Account. Personal accounts will NOT work.
# CRITICAL: Image URLs for Instagram must be publicly accessible HTTPS URLs. Local file paths will fail.
# CRITICAL: Reel videos must be H.264 codec, 9:16 aspect ratio, 3-60 seconds duration. Validate before publish attempt.
# CRITICAL: Instagram Graph API publish is async — creates container, then publishes. Must poll for completion or use webhook.
# CRITICAL: Firecrawl has 5-second timeout on scrapes. Reference links must be fast-loading or they'll fail.
# CRITICAL: Anthropic API claude-sonnet-4 has 200K token context limit. Batch large brand profiles + reference content carefully.
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: Auto-publish is OPTIONAL. System must work with content_pack_only mode (no Instagram secrets required).
# CRITICAL: If publish fails, do NOT discard content pack. Write publish_log with errors and provide manual fallback.
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents:
  - name: "content-strategist-specialist"
    description: "Delegate to this subagent for analyzing brand profile, weekly theme, and reference content to create a content strategy brief before generation"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read and parse brand_profile.json"
      - "Scrape reference_links via Firecrawl or HTTP fallback"
      - "Extract key themes, product mentions, and messaging angles from references"
      - "Create content strategy brief: key messages, angles, do/don't reminders, reference facts"
    inputs: "brand_profile.json, weekly_theme, reference_links (optional), post_plan"
    outputs: "strategy_brief.json with extracted facts, messaging angles, and strategic guidance"

  - name: "copywriter-specialist"
    description: "Delegate to this subagent for generating draft captions, hooks, and CTAs for each post in the plan"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read strategy_brief.json and brand_profile.json"
      - "Generate hooks, captions, and CTAs for each post in post_plan"
      - "Match brand voice and tone from profile"
      - "Ensure captions are under 2200 characters"
      - "Output draft content for review"
    inputs: "strategy_brief.json, brand_profile.json, post_plan"
    outputs: "draft_content.json with hooks, captions, CTAs per post"

  - name: "hashtag-specialist"
    description: "Delegate to this subagent for generating Instagram hashtag sets that match the brand's hashtag strategy"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read brand hashtag strategy from brand_profile.json"
      - "Generate 8-12 hashtags per post following strategy mix (niche/mid-tier/broad)"
      - "Avoid banned/spammy hashtags"
      - "Ensure hashtags are Instagram-valid (no spaces, alphanumeric + underscore only)"
      - "Output hashtag sets per post"
    inputs: "brand_profile.json, draft_content.json (for context)"
    outputs: "hashtags.json with hashtag lists per post"

  - name: "creative-brief-specialist"
    description: "Delegate to this subagent for generating visual creative briefs describing how to produce the image/video for each post"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read post_plan and draft_content.json"
      - "Generate creative brief for each post: visual style, composition, text overlays, duration (for reels), aspect ratio"
      - "Include alt text for accessibility"
      - "Provide suggested posting times based on audience and content type"
      - "Output creative briefs per post"
    inputs: "post_plan, draft_content.json, brand_profile.json"
    outputs: "creative_briefs.json with briefs, alt text, suggested times per post"

  - name: "reviewer-specialist"
    description: "Delegate to this subagent for running comprehensive quality checks on all generated content before publishing"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read brand_profile.json and assembled_content.json"
      - "Check brand voice alignment (tone, style, vocabulary match)"
      - "Scan for banned topics from brand profile"
      - "Check for prohibited claims or aggressive sales language"
      - "Validate Instagram format rules (caption length, hashtag count, emoji count)"
      - "Validate hashtag hygiene (no spaces, valid characters)"
      - "Output review report with pass/fail per check and flagged issues"
    inputs: "brand_profile.json, assembled_content.json"
    outputs: "review_report.json with pass/fail status, confidence scores, and flagged items"

  - name: "publisher-specialist"
    description: "Delegate to this subagent for handling Instagram Graph API publishing or generating manual upload checklists"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Check publishing_mode (auto_publish or content_pack_only)"
      - "If auto_publish: call Instagram Graph API to publish each post, handle rate limits, log results"
      - "If content_pack_only: generate manual upload checklist markdown"
      - "Handle publish failures gracefully (log error, continue with manual fallback)"
      - "Output publish_log.json or upload_checklist.md"
    inputs: "publishing_mode, assembled_content.json (review-approved), Instagram secrets (if auto_publish)"
    outputs: "publish_log.json (if auto_publish) or upload_checklist.md (if content_pack_only)"

  - name: "archive-manager-specialist"
    description: "Delegate to this subagent for managing the rolling archive of content packs and updating the latest.md index"
    tools: "Read, Write, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Write all outputs (content_pack markdown/json, review_report, publish_log or checklist) to output/instagram/"
      - "Update latest.md with pointer to most recent pack"
      - "Clean up old content packs if rolling archive limit is hit (keep last 52 weeks)"
      - "Ensure all files are committed"
    inputs: "All generated outputs"
    outputs: "Files written to output/instagram/, latest.md updated, old packs archived"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "Generate captions/hooks (copywriter)"
  - "Generate hashtags (hashtag specialist)"
  - "Generate creative briefs (creative-brief specialist)"

independent_task_count: 3
recommendation: "Use Agent Teams for parallel generation phase"
rationale: "Three content generation tasks have NO data dependencies. All three need strategy_brief and brand_profile as input, but do not depend on each other's output. Sequential: 3 x 15s = 45s. Parallel: 15s. 3x speedup with identical token cost."

# If Agent Teams recommended:
team_lead_responsibilities:
  - "Create shared task list with 3 generation tasks"
  - "Spawn teammates for copywriter, hashtag, and creative-brief generation"
  - "Wait for all three to complete"
  - "Merge results into assembled_content.json"
  - "Pass to reviewer-specialist for quality checks"

teammates:
  - name: "copywriter-teammate"
    task: "Generate hooks, captions, and CTAs for all posts in post_plan following brand voice from strategy brief"
    inputs: "strategy_brief.json, brand_profile.json, post_plan"
    outputs: "captions.json with hook, caption, CTA per post"

  - name: "hashtag-teammate"
    task: "Generate 8-12 hashtags per post following brand hashtag strategy"
    inputs: "brand_profile.json (hashtag strategy), post_plan, weekly_theme"
    outputs: "hashtags.json with hashtag lists per post"

  - name: "creative-brief-teammate"
    task: "Generate visual creative briefs, alt text, and suggested posting times for all posts"
    inputs: "post_plan, weekly_theme, brand_profile.json"
    outputs: "creative_briefs.json with brief, alt text, suggested time per post"

# Sequential fallback:
sequential_rationale: "If Agent Teams is disabled, run copywriter → hashtag → creative-brief sequentially. Total time ~45s vs 15s parallel, but functionally identical output."
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "0 9 * * 1  # Every Monday at 9 AM UTC"
    description: "Weekly automated content generation and publishing run"

  - type: "workflow_dispatch"
    config: |
      inputs:
        weekly_theme:
          description: 'Weekly theme for content (e.g., "Myth-busting Monday")'
          required: true
        publishing_mode:
          description: 'auto_publish or content_pack_only'
          required: false
          default: 'content_pack_only'
        post_count:
          description: 'Number of posts to generate (3-7)'
          required: false
          default: '5'
    description: "Manual trigger for on-demand content generation with custom theme"

  - type: "repository_dispatch"
    config: "event_type: instagram_content_request"
    description: "Agent HQ trigger for issue-driven content requests"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "Load Inputs"
    description: "Read brand_profile.json, weekly_theme, post_plan, reference_links (optional), publishing_mode from inputs"
    subagent: "none (main agent)"
    tools: ["load_inputs.py"]
    inputs: "brand_profile.json, workflow inputs"
    outputs: "Validated input data in memory"
    failure_mode: "brand_profile.json missing or invalid JSON"
    fallback: "Halt with clear error message listing missing/invalid fields"

  - name: "Fetch Reference Content"
    description: "Scrape reference_links (if provided) via Firecrawl to extract accurate product details, blog content, announcements"
    subagent: "content-strategist-specialist"
    tools: ["scrape_references.py"]
    inputs: "reference_links array"
    outputs: "reference_content.json with scraped markdown per URL"
    failure_mode: "URL unreachable, paywall, or timeout"
    fallback: "Log failed URL, continue with remaining references. If all fail, proceed with brand_profile only."

  - name: "Generate Strategy Brief"
    description: "Analyze brand profile, weekly theme, and reference content to create content strategy brief"
    subagent: "content-strategist-specialist"
    tools: ["generate_strategy_brief.py"]
    inputs: "brand_profile.json, weekly_theme, reference_content.json (optional), post_plan"
    outputs: "strategy_brief.json with key messages, angles, do/don't reminders, extracted facts"
    failure_mode: "LLM API failure or invalid output structure"
    fallback: "Retry once with simplified prompt. If still fails, halt with error."

  - name: "Generate Content (Parallel)"
    description: "Generate captions, hashtags, and creative briefs in parallel using Agent Teams"
    subagent: "Team lead coordinates copywriter, hashtag, creative-brief specialists"
    tools: ["generate_captions.py", "generate_hashtags.py", "generate_creative_briefs.py"]
    inputs: "strategy_brief.json, brand_profile.json, post_plan"
    outputs: "captions.json, hashtags.json, creative_briefs.json"
    failure_mode: "One or more generation tasks fail"
    fallback: "Sequential fallback: run tasks one by one. If any still fails, halt with error."

  - name: "Assemble Content Pack"
    description: "Merge captions, hashtags, creative briefs into unified content pack structure"
    subagent: "none (main agent)"
    tools: ["assemble_content.py"]
    inputs: "captions.json, hashtags.json, creative_briefs.json, post_plan"
    outputs: "assembled_content.json with all posts fully structured"
    failure_mode: "Mismatched post counts or missing fields"
    fallback: "Log validation errors, fill missing fields with placeholders, continue (reviewer will flag)"

  - name: "Quality Review"
    description: "Run comprehensive quality checks on assembled content"
    subagent: "reviewer-specialist"
    tools: ["review_content.py"]
    inputs: "brand_profile.json, assembled_content.json"
    outputs: "review_report.json with pass/fail status and flagged items"
    failure_mode: "Review fails (banned topics, prohibited claims, format violations)"
    fallback: "Regenerate flagged posts with corrective feedback. Max 2 retries. If still failing, output content pack with REVIEW_FAILED flag and halt publish."

  - name: "Publish or Output"
    description: "Publish to Instagram Graph API OR generate manual upload pack based on publishing_mode"
    subagent: "publisher-specialist"
    tools: ["publish_instagram.py"]
    inputs: "publishing_mode, assembled_content.json (review-approved), Instagram secrets (if auto_publish)"
    outputs: "publish_log.json (if auto_publish) OR upload_checklist.md (if content_pack_only)"
    failure_mode: "Instagram API error (auth, rate limit, format issue)"
    fallback: "Log publish error, do NOT discard content pack. Generate upload_checklist.md as manual fallback."

  - name: "Archive and Commit"
    description: "Write all outputs to output/instagram/, update latest.md, commit to repo"
    subagent: "archive-manager-specialist"
    tools: ["archive_outputs.py"]
    inputs: "All generated files"
    outputs: "Files written to output/instagram/, latest.md updated, repo committed"
    failure_mode: "Git commit failure or file write error"
    fallback: "Retry commit once. If fails, log error but do NOT delete generated files."
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "load_inputs.py"
    purpose: "Load and validate brand_profile.json, workflow inputs, and post_plan"
    catalog_pattern: "json_read_write (tool_catalog.md)"
    inputs:
      - "brand_profile_path: str — Path to brand profile JSON"
      - "weekly_theme: str — Weekly theme from workflow input"
      - "post_plan: str — JSON string or path to post plan"
      - "reference_links: str — Optional JSON array of reference URLs"
      - "publishing_mode: str — auto_publish or content_pack_only"
    outputs: "JSON object with validated inputs"
    dependencies: ["json (stdlib)", "pathlib (stdlib)"]
    mcp_used: "none"
    error_handling: "Validate all required fields exist. Raise ValueError with clear message if missing/invalid."

  - name: "scrape_references.py"
    purpose: "Scrape reference URLs via Firecrawl or HTTP fallback, return markdown content"
    catalog_pattern: "firecrawl_scrape (tool_catalog.md)"
    inputs:
      - "reference_links: list[dict] — URLs with context"
    outputs: "JSON object with scraped content per URL"
    dependencies: ["firecrawl-py", "httpx", "beautifulsoup4 (fallback)"]
    mcp_used: "firecrawl (primary), none (fallback)"
    error_handling: "Try Firecrawl first. If fails, fallback to requests + BeautifulSoup. If URL fails, log error and continue with remaining URLs."

  - name: "generate_strategy_brief.py"
    purpose: "Use Claude to analyze inputs and generate content strategy brief"
    catalog_pattern: "llm_prompt (tool_catalog.md)"
    inputs:
      - "brand_profile: dict — Brand voice and guardrails"
      - "weekly_theme: str — Weekly theme"
      - "reference_content: dict — Scraped reference content (optional)"
      - "post_plan: dict — Post types and counts"
    outputs: "JSON object with strategy brief (key messages, angles, do/don't reminders, facts)"
    dependencies: ["anthropic"]
    mcp_used: "none (direct API)"
    error_handling: "Retry once on API failure. If fails, raise exception with full error context."

  - name: "generate_captions.py"
    purpose: "Generate hooks, captions, and CTAs for all posts using Claude"
    catalog_pattern: "structured_extract (tool_catalog.md)"
    inputs:
      - "strategy_brief: dict — Content strategy guidance"
      - "brand_profile: dict — Brand voice"
      - "post_plan: dict — Post types and counts"
    outputs: "JSON object with hook, caption, CTA per post"
    dependencies: ["anthropic"]
    mcp_used: "none"
    error_handling: "Validate caption length (<2200 chars). Retry once if output invalid. Raise exception if fails after retry."

  - name: "generate_hashtags.py"
    purpose: "Generate Instagram hashtag sets following brand strategy"
    catalog_pattern: "structured_extract (tool_catalog.md)"
    inputs:
      - "brand_profile: dict — Hashtag strategy from profile"
      - "post_plan: dict — Post types"
      - "weekly_theme: str — Theme for hashtag relevance"
    outputs: "JSON object with hashtag lists per post (8-12 hashtags)"
    dependencies: ["anthropic"]
    mcp_used: "none"
    error_handling: "Validate hashtag format (no spaces, alphanumeric + underscore). Retry once if invalid. Raise exception if fails."

  - name: "generate_creative_briefs.py"
    purpose: "Generate visual creative briefs, alt text, and suggested posting times"
    catalog_pattern: "structured_extract (tool_catalog.md)"
    inputs:
      - "post_plan: dict — Post types and focus"
      - "weekly_theme: str — Content theme"
      - "brand_profile: dict — Brand context"
    outputs: "JSON object with creative brief, alt text, suggested time per post"
    dependencies: ["anthropic"]
    mcp_used: "none"
    error_handling: "Retry once on API failure. Raise exception if fails."

  - name: "assemble_content.py"
    purpose: "Merge captions, hashtags, creative briefs into unified content pack structure"
    catalog_pattern: "transform_map (tool_catalog.md)"
    inputs:
      - "captions: dict — Generated captions per post"
      - "hashtags: dict — Generated hashtags per post"
      - "creative_briefs: dict — Generated briefs per post"
      - "post_plan: dict — Original post plan"
    outputs: "JSON object with fully assembled content pack (all fields per post)"
    dependencies: ["json (stdlib)"]
    mcp_used: "none"
    error_handling: "Validate all posts have required fields. Fill missing fields with placeholders and log warnings."

  - name: "review_content.py"
    purpose: "Run comprehensive quality checks on assembled content"
    catalog_pattern: "llm_prompt + structured_extract (tool_catalog.md)"
    inputs:
      - "brand_profile: dict — Brand voice and guardrails"
      - "assembled_content: dict — Full content pack"
    outputs: "JSON object with review report (pass/fail per check, confidence scores, flagged items)"
    dependencies: ["anthropic"]
    mcp_used: "none"
    error_handling: "Return review report even if some checks fail. Never raise exception. Report format validation failures separately from content failures."

  - name: "publish_instagram.py"
    purpose: "Publish posts to Instagram Graph API OR generate manual upload checklist"
    catalog_pattern: "rest_client (tool_catalog.md)"
    inputs:
      - "publishing_mode: str — auto_publish or content_pack_only"
      - "assembled_content: dict — Review-approved content"
      - "instagram_access_token: str — From env (optional)"
      - "instagram_account_id: str — From env (optional)"
    outputs: "JSON publish log (if auto_publish) OR markdown upload checklist (if content_pack_only)"
    dependencies: ["httpx"]
    mcp_used: "none"
    error_handling: "If auto_publish: try to publish each post, log success/failure. On API error, generate manual checklist as fallback. If content_pack_only: generate checklist directly."

  - name: "archive_outputs.py"
    purpose: "Write all outputs to output/instagram/, update latest.md, maintain rolling archive"
    catalog_pattern: "json_read_write + git_commit_push (tool_catalog.md)"
    inputs:
      - "content_pack_markdown: str — Generated markdown"
      - "content_pack_json: dict — Generated JSON"
      - "review_report: dict — Review results"
      - "publish_log_or_checklist: dict/str — Publish results or checklist"
      - "generation_date: str — YYYY-MM-DD"
    outputs: "Files written to output/instagram/, latest.md updated"
    dependencies: ["pathlib (stdlib)", "json (stdlib)"]
    mcp_used: "none"
    error_handling: "Ensure output directory exists. If file write fails, log error and retry once. Never delete generated content."
```

### Per-Tool Pseudocode
```python
# load_inputs.py
def main():
    # PATTERN: json_read_write
    # Step 1: Parse inputs from CLI args or env vars
    args = parse_args()

    # Step 2: Load brand_profile.json
    # GOTCHA: File may have BOM, use utf-8-sig encoding
    brand_profile = json.loads(Path(args.brand_profile_path).read_text(encoding="utf-8-sig"))

    # Step 3: Validate required fields
    required = ["brand_name", "voice_description", "tone", "target_audience", "do_list", "dont_list", "banned_topics"]
    for field in required:
        if field not in brand_profile:
            raise ValueError(f"Missing required field in brand_profile: {field}")

    # Step 4: Parse post_plan (JSON string or file path)
    post_plan = json.loads(args.post_plan) if args.post_plan.startswith("{") else json.loads(Path(args.post_plan).read_text())

    # Step 5: Output validated inputs
    result = {
        "brand_profile": brand_profile,
        "weekly_theme": args.weekly_theme,
        "post_plan": post_plan,
        "reference_links": json.loads(args.reference_links) if args.reference_links else [],
        "publishing_mode": args.publishing_mode
    }
    print(json.dumps(result))

# scrape_references.py
def main():
    # PATTERN: firecrawl_scrape with fallback
    # CRITICAL: Firecrawl has 5-second timeout. Handle gracefully.
    args = parse_args()
    reference_links = json.loads(args.reference_links)
    
    results = []
    for ref in reference_links:
        try:
            # Try Firecrawl first
            app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
            scraped = app.scrape_url(ref["url"], params={"formats": ["markdown"]})
            results.append({"url": ref["url"], "context": ref["context"], "content": scraped["markdown"]})
        except Exception as e:
            # Fallback to requests + BeautifulSoup
            try:
                resp = httpx.get(ref["url"], timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                content = soup.get_text()
                results.append({"url": ref["url"], "context": ref["context"], "content": content})
            except Exception as e2:
                logging.error(f"Failed to scrape {ref['url']}: {e2}")
                results.append({"url": ref["url"], "context": ref["context"], "content": "", "error": str(e2)})
    
    print(json.dumps({"reference_content": results}))

# generate_strategy_brief.py
def main():
    # PATTERN: llm_prompt with structured output
    args = parse_args()
    brand_profile = json.loads(args.brand_profile)
    weekly_theme = args.weekly_theme
    reference_content = json.loads(args.reference_content) if args.reference_content else []
    post_plan = json.loads(args.post_plan)
    
    # Build system prompt
    system_prompt = f"""You are a content strategist specializing in Instagram marketing.
Analyze the brand profile, weekly theme, and optional reference content to create a content strategy brief.

Brand: {brand_profile['brand_name']}
Voice: {brand_profile['voice_description']}
Tone: {brand_profile['tone']}
Target Audience: {brand_profile['target_audience']}

Weekly Theme: {weekly_theme}

Reference Content:
{json.dumps(reference_content, indent=2) if reference_content else "None provided"}

Post Plan:
{json.dumps(post_plan, indent=2)}

Output a JSON object with:
- key_messages: list of 3-5 key messages to communicate this week
- messaging_angles: list of 3-5 angles/hooks that align with theme and brand voice
- do_reminders: list of do's from brand profile most relevant to this theme
- dont_reminders: list of don'ts from brand profile most relevant to this theme
- extracted_facts: list of facts/details from reference content to use (if any)
"""
    
    # Call Claude
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": "Generate the content strategy brief."}]
    )
    
    # Parse and validate JSON response
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    strategy_brief = json.loads(raw)
    
    print(json.dumps(strategy_brief))

# review_content.py
def main():
    # PATTERN: structured_extract with multi-pass checks
    # CRITICAL: Review must check brand voice, banned topics, prohibited claims, format rules
    args = parse_args()
    brand_profile = json.loads(args.brand_profile)
    assembled_content = json.loads(args.assembled_content)
    
    system_prompt = f"""You are a brand compliance reviewer for Instagram content.
Review the generated content pack against the brand profile and output a comprehensive review report.

Brand Profile:
{json.dumps(brand_profile, indent=2)}

Content Pack:
{json.dumps(assembled_content, indent=2)}

Run the following checks:
1. Brand Voice Match: Does each post match the brand voice, tone, and style?
2. Banned Topics: Scan for any banned topics from brand profile
3. Prohibited Claims: Check for prohibited language from brand profile's dont_list
4. Format Validation: Captions under 2200 chars, hashtag counts 8-12, emoji counts per style guide
5. Hashtag Hygiene: All hashtags valid Instagram format (no spaces, alphanumeric + underscore)

Output JSON with:
- brand_voice_match: {pass: bool, confidence: float, notes: str}
- banned_topics_check: {pass: bool, flagged: list[str], notes: str}
- prohibited_claims_check: {pass: bool, flagged: list[str], notes: str}
- format_validation: {pass: bool, issues: list[str]}
- hashtag_hygiene: {pass: bool, issues: list[str]}
- overall_pass: bool
"""
    
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        temperature=0.0,
        system=system_prompt,
        messages=[{"role": "user", "content": "Run all quality checks and output the review report."}]
    )
    
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    review_report = json.loads(raw)
    
    print(json.dumps(review_report))

# publish_instagram.py
def main():
    # PATTERN: rest_client with conditional logic
    # CRITICAL: Instagram Graph API requires 2 steps: create container, then publish
    # CRITICAL: Rate limit is 200 calls/hour. Each post = 2 calls.
    args = parse_args()
    publishing_mode = args.publishing_mode
    assembled_content = json.loads(args.assembled_content)
    
    if publishing_mode == "content_pack_only":
        # Generate manual upload checklist
        checklist = generate_upload_checklist(assembled_content)
        print(checklist)
        return
    
    # Auto-publish mode
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    
    if not access_token or not account_id:
        logging.error("Instagram credentials not found. Falling back to manual checklist.")
        checklist = generate_upload_checklist(assembled_content)
        print(checklist)
        return
    
    publish_results = []
    for post in assembled_content["posts"]:
        try:
            # Step 1: Create media container
            # Step 2: Publish container
            # Step 3: Log result
            # GOTCHA: This is simplified pseudocode. Real implementation needs full API workflow.
            result = publish_post_to_instagram(post, access_token, account_id)
            publish_results.append(result)
        except Exception as e:
            logging.error(f"Failed to publish post {post['id']}: {e}")
            publish_results.append({"post_id": post["id"], "status": "failed", "error": str(e)})
    
    publish_log = {
        "mode": "auto_publish",
        "timestamp": datetime.utcnow().isoformat(),
        "posts_attempted": len(assembled_content["posts"]),
        "posts_published": sum(1 for r in publish_results if r["status"] == "published"),
        "posts_failed": sum(1 for r in publish_results if r["status"] == "failed"),
        "results": publish_results
    }
    
    print(json.dumps(publish_log))
```

### Integration Points
```yaml
SECRETS:
  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API for content generation and quality review"
    required: true

  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API for scraping reference links"
    required: false

  - name: "OPENAI_API_KEY"
    purpose: "OpenAI API fallback if Anthropic unavailable"
    required: false

  - name: "INSTAGRAM_ACCESS_TOKEN"
    purpose: "Instagram Graph API authentication for publishing"
    required: false (only for auto_publish mode)

  - name: "INSTAGRAM_BUSINESS_ACCOUNT_ID"
    purpose: "Instagram Business Account ID for API calls"
    required: false (only for auto_publish mode)

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "ANTHROPIC_API_KEY=your_anthropic_key_here  # Required for content generation"
      - "FIRECRAWL_API_KEY=your_firecrawl_key_here  # Optional for reference scraping"
      - "OPENAI_API_KEY=your_openai_key_here  # Optional fallback for generation"
      - "INSTAGRAM_ACCESS_TOKEN=your_instagram_token_here  # Required for auto_publish mode"
      - "INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id_here  # Required for auto_publish mode"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "anthropic>=0.18.0  # Claude API client"
      - "openai>=1.0.0  # OpenAI API fallback"
      - "firecrawl-py>=0.0.5  # Firecrawl scraping"
      - "httpx>=0.24.0  # HTTP client for APIs"
      - "beautifulsoup4>=4.12.0  # HTML parsing fallback"
      - "tenacity>=8.2.0  # Retry logic for API calls"
      - "python-dateutil>=2.8.0  # Date parsing"

GITHUB_ACTIONS:
  - trigger: "schedule"
    config: |
      on:
        schedule:
          - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
        workflow_dispatch:
          inputs:
            weekly_theme:
              description: 'Weekly theme for content'
              required: true
            publishing_mode:
              description: 'auto_publish or content_pack_only'
              required: false
              default: 'content_pack_only'
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/load_inputs.py').read())"
python -c "import ast; ast.parse(open('tools/scrape_references.py').read())"
python -c "import ast; ast.parse(open('tools/generate_strategy_brief.py').read())"
python -c "import ast; ast.parse(open('tools/generate_captions.py').read())"
python -c "import ast; ast.parse(open('tools/generate_hashtags.py').read())"
python -c "import ast; ast.parse(open('tools/generate_creative_briefs.py').read())"
python -c "import ast; ast.parse(open('tools/assemble_content.py').read())"
python -c "import ast; ast.parse(open('tools/review_content.py').read())"
python -c "import ast; ast.parse(open('tools/publish_instagram.py').read())"
python -c "import ast; ast.parse(open('tools/archive_outputs.py').read())"

# Import check — verify no missing dependencies
python -c "from tools.load_inputs import main; assert callable(main)"
python -c "from tools.scrape_references import main; assert callable(main)"
python -c "from tools.generate_strategy_brief import main; assert callable(main)"
python -c "from tools.generate_captions import main; assert callable(main)"
python -c "from tools.generate_hashtags import main; assert callable(main)"
python -c "from tools.generate_creative_briefs import main; assert callable(main)"
python -c "from tools.assemble_content import main; assert callable(main)"
python -c "from tools.review_content import main; assert callable(main)"
python -c "from tools.publish_instagram import main; assert callable(main)"
python -c "from tools.archive_outputs import main; assert callable(main)"

# Verify subagent files have valid YAML frontmatter
python -c "
import yaml
from pathlib import Path

subagents = Path('.claude/agents/').glob('*.md')
for f in subagents:
    content = f.read_text()
    if not content.startswith('---'):
        raise ValueError(f'{f} missing frontmatter')
    _, frontmatter, body = content.split('---', 2)
    metadata = yaml.safe_load(frontmatter)
    assert 'name' in metadata, f'{f} missing name'
    assert 'description' in metadata, f'{f} missing description'
    print(f'{f.name} validated')
"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Test load_inputs.py with sample brand profile
cat > /tmp/test_brand_profile.json <<EOF
{
  "brand_name": "Test Brand",
  "voice_description": "Friendly and professional",
  "tone": "Conversational",
  "target_audience": "Young professionals",
  "products_services": ["Consulting"],
  "do_list": ["Be authentic"],
  "dont_list": ["Don't oversell"],
  "banned_topics": ["Politics"],
  "preferred_cta": ["Link in bio"],
  "emoji_style": "Minimal",
  "hashtag_strategy": "Mix of niche and broad"
}
EOF

python tools/load_inputs.py \
  --brand_profile_path /tmp/test_brand_profile.json \
  --weekly_theme "Test Theme" \
  --post_plan '{"posts": [{"type": "single_image"}]}' \
  --publishing_mode "content_pack_only"
# Expected output: JSON object with validated inputs

# Test scrape_references.py with sample URL (without actual API call)
# Create mock for testing
echo '{"reference_content": [{"url": "https://example.com", "content": "Sample content"}]}' > /tmp/expected_scrape.json
# Verify output structure matches expected

# Test generate_strategy_brief.py (requires ANTHROPIC_API_KEY)
# Skip if key not available, log warning
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "WARNING: ANTHROPIC_API_KEY not set, skipping LLM tool tests"
else
  python tools/generate_strategy_brief.py \
    --brand_profile "$(cat /tmp/test_brand_profile.json)" \
    --weekly_theme "Test Theme" \
    --post_plan '{"posts": [{"type": "single_image"}]}'
  # Expected: JSON with key_messages, messaging_angles, etc.
fi

# Test assemble_content.py with mock inputs
cat > /tmp/test_captions.json <<EOF
{"posts": [{"id": 1, "hook": "Test hook", "caption": "Test caption", "cta": "Link in bio"}]}
EOF
cat > /tmp/test_hashtags.json <<EOF
{"posts": [{"id": 1, "hashtags": ["#test", "#sample"]}]}
EOF
cat > /tmp/test_briefs.json <<EOF
{"posts": [{"id": 1, "brief": "Test brief", "alt_text": "Test alt"}]}
EOF

python tools/assemble_content.py \
  --captions "$(cat /tmp/test_captions.json)" \
  --hashtags "$(cat /tmp/test_hashtags.json)" \
  --creative_briefs "$(cat /tmp/test_briefs.json)" \
  --post_plan '{"posts": [{"type": "single_image"}]}'
# Expected: JSON with fully assembled content pack

# Test publish_instagram.py in content_pack_only mode (no API call)
python tools/publish_instagram.py \
  --publishing_mode "content_pack_only" \
  --assembled_content '{"posts": [{"id": 1, "caption": "Test", "hashtags": ["#test"]}]}'
# Expected: Markdown upload checklist

# If any tool fails: Read the error, fix the root cause, re-run.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline

# Full pipeline test with sample data
echo "=== Running integration test ==="

# Step 1: Load inputs
INPUTS=$(python tools/load_inputs.py \
  --brand_profile_path /tmp/test_brand_profile.json \
  --weekly_theme "Integration Test Theme" \
  --post_plan '{"posts": [{"type": "single_image", "focus": "test"}]}' \
  --publishing_mode "content_pack_only")

echo "✓ Step 1: Inputs loaded"

# Step 2: Skip scraping (no reference links)
REFERENCE_CONTENT='{"reference_content": []}'
echo "✓ Step 2: Reference scraping skipped (no links)"

# Step 3: Generate strategy brief (requires API key)
if [ -n "$ANTHROPIC_API_KEY" ]; then
  STRATEGY_BRIEF=$(python tools/generate_strategy_brief.py \
    --brand_profile "$(echo $INPUTS | jq -r '.brand_profile | @json')" \
    --weekly_theme "Integration Test Theme" \
    --post_plan '{"posts": [{"type": "single_image"}]}')
  echo "✓ Step 3: Strategy brief generated"
else
  # Use mock for testing without API key
  STRATEGY_BRIEF='{"key_messages": ["Test"], "messaging_angles": ["Test"]}'
  echo "⚠ Step 3: Using mock strategy brief (no API key)"
fi

# Step 4-6: Content generation (would use Agent Teams in production)
# For integration test, use mocks
CAPTIONS='{"posts": [{"id": 1, "hook": "Test hook", "caption": "Test caption", "cta": "Link in bio"}]}'
HASHTAGS='{"posts": [{"id": 1, "hashtags": ["#IntegrationTest", "#Sample"]}]}'
BRIEFS='{"posts": [{"id": 1, "brief": "Test visual brief", "alt_text": "Test image", "suggested_time": "Monday 6 PM"}]}'
echo "✓ Steps 4-6: Content generation (mock)"

# Step 7: Assemble content pack
ASSEMBLED=$(python tools/assemble_content.py \
  --captions "$CAPTIONS" \
  --hashtags "$HASHTAGS" \
  --creative_briefs "$BRIEFS" \
  --post_plan '{"posts": [{"type": "single_image"}]}')
echo "✓ Step 7: Content pack assembled"

# Step 8: Review content (requires API key)
if [ -n "$ANTHROPIC_API_KEY" ]; then
  REVIEW=$(python tools/review_content.py \
    --brand_profile "$(echo $INPUTS | jq -r '.brand_profile | @json')" \
    --assembled_content "$ASSEMBLED")
  echo "✓ Step 8: Content reviewed"
  
  # Verify review passed
  REVIEW_PASS=$(echo $REVIEW | jq -r '.overall_pass')
  if [ "$REVIEW_PASS" != "true" ]; then
    echo "✗ Integration test failed: Review did not pass"
    exit 1
  fi
else
  echo "⚠ Step 8: Skipping review (no API key)"
fi

# Step 9: Publish (content_pack_only mode)
CHECKLIST=$(python tools/publish_instagram.py \
  --publishing_mode "content_pack_only" \
  --assembled_content "$ASSEMBLED")
echo "✓ Step 9: Upload checklist generated"

# Step 10: Verify outputs exist and are valid
echo "$ASSEMBLED" | jq empty || { echo "✗ Assembled content is not valid JSON"; exit 1; }
[ -n "$CHECKLIST" ] || { echo "✗ Checklist is empty"; exit 1; }

echo "=== Integration test passed ==="

# Verify workflow.md references match actual tool files
echo "=== Verifying workflow.md references ==="
WORKFLOW_TOOLS=$(grep -o 'tools/[a-z_]*.py' workflow.md | sort -u)
for tool in $WORKFLOW_TOOLS; do
  if [ ! -f "$tool" ]; then
    echo "✗ workflow.md references missing tool: $tool"
    exit 1
  fi
done
echo "✓ All workflow.md tool references valid"

# Verify CLAUDE.md documents all tools and subagents
echo "=== Verifying CLAUDE.md completeness ==="
for tool_file in tools/*.py; do
  tool_name=$(basename $tool_file)
  if ! grep -q "$tool_name" CLAUDE.md; then
    echo "✗ CLAUDE.md missing documentation for $tool_name"
    exit 1
  fi
done
echo "✓ CLAUDE.md documents all tools"

# Verify .env.example lists all required secrets
echo "=== Verifying .env.example ==="
REQUIRED_SECRETS=("ANTHROPIC_API_KEY" "FIRECRAWL_API_KEY" "INSTAGRAM_ACCESS_TOKEN" "INSTAGRAM_BUSINESS_ACCOUNT_ID")
for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! grep -q "$secret" .env.example; then
    echo "✗ .env.example missing $secret"
    exit 1
  fi
done
echo "✓ .env.example complete"

echo "=== All validation checks passed ==="
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes (30 minutes for full run) and failure notifications
- [ ] .env.example lists all required environment variables
- [ ] .gitignore excludes .env, __pycache__/, credentials, output/instagram/*.json (keep .md files)
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files (.claude/agents/*.md) have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies with version pins

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only output/instagram/* files
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types (httpx.HTTPError, json.JSONDecodeError, etc.)
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks — Firecrawl must have requests + BeautifulSoup fallback
- Do not design subagents that call other subagents — only the main agent delegates to specialists
- Do not use Agent Teams when fewer than 3 independent tasks exist — but this system HAS 3 independent tasks (captions, hashtags, briefs)
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass validation
- Do not generate workflow steps without failure modes and fallback actions — every step has try/except and fallback
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not discard content packs when publish fails — always output manual checklist as fallback
- Do not attempt to publish to Instagram Graph API when secrets are missing — gracefully fall back to content_pack_only mode

---

## Confidence Score: 9/10

**Score rationale:**
- **Requirements clarity**: High confidence — Problem description is detailed with clear inputs/outputs, integrations, and success criteria. All necessary context provided.
- **Technical feasibility**: High confidence — All integrations (Firecrawl, Anthropic, Instagram Graph API) are proven and well-documented. Fallback strategies are clear.
- **Workflow pattern fit**: High confidence — Generate > Review > Publish pattern is proven for content generation systems. Two-pass review ensures quality.
- **Tool specifications**: High confidence — All tools have clear inputs/outputs and map to proven catalog patterns. Pseudocode is executable.
- **Validation loops**: High confidence — Three-level validation gates are comprehensive and executable. Integration test covers full pipeline.
- **Ambiguity**: Low — One minor ambiguity around Instagram Graph API container creation workflow (clarified below).

**Ambiguity flags** (areas requiring clarification before building):
- [ ] Instagram Graph API publish workflow requires 2-step process (create container → publish container). Full API workflow details needed for publish_instagram.py implementation. Recommendation: Reference official Meta documentation for complete flow with media type handling (photo vs reel vs carousel).

**Recommendation**: Proceed to build. The single ambiguity flag can be resolved during tool implementation by referencing official Instagram Graph API documentation. The PRP provides sufficient context for the factory to build a working system.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/weekly-instagram-content-publisher.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
