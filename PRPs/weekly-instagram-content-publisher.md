name: "weekly-instagram-content-publisher"
description: |
  Weekly Instagram Content Publisher — An AI-powered social media content generation system that creates Instagram-ready content packs (captions, hashtags, creative briefs, image prompts) based on brand voice and weekly themes, runs multi-dimensional quality review checks, and either auto-publishes via Instagram Graph API or prepares manual upload packages.

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
Build a weekly automated Instagram content generation system that produces on-brand, compliance-checked content packs with options for automatic publishing or manual review. The system takes brand voice parameters, weekly themes, and post plans as input, generates full content packs with captions/hashtags/creative briefs, runs quality gates (brand voice alignment, compliance, format validation), and either publishes to Instagram via Graph API or outputs ready-to-post packages for manual upload.

Success looks like: Marketing teams open an issue or trigger a workflow with a weekly theme, and 5-10 minutes later receive a complete content pack that's either auto-published or sitting in a ready-to-upload folder with all assets prepared.

## Why
- **Saves time**: Manual Instagram content creation takes 2-4 hours/week per channel. This reduces it to 10 minutes of setup + automated execution.
- **Ensures brand consistency**: Automated brand voice checks prevent off-brand content from being published.
- **Reduces compliance risk**: Automated scanning for prohibited claims, banned topics, and regulatory violations before publishing.
- **Scales content production**: One person can manage 5+ Instagram accounts with weekly content schedules.
- **Who benefits**: Marketing teams, social media managers, content creators, agencies managing multiple client accounts.
- **Frequency**: Weekly execution (Monday 9 AM UTC), with on-demand manual triggers for campaigns.

## What
From a user's perspective:
1. User opens a GitHub Issue or triggers a workflow with weekly theme + brand profile + post plan
2. System fetches reference content from provided URLs (blog posts, product pages, announcements)
3. System generates content for each post type (captions, hooks, CTAs, hashtags, alt text, creative brief)
4. System runs automated quality review (brand voice match, compliance checks, format validation)
5. If all quality gates pass AND auto_publish is enabled: Posts are published to Instagram with scheduling
6. If quality gates fail OR content_pack_only mode: A complete markdown + JSON content pack is committed to the repo with manual upload instructions
7. User receives notification (GitHub comment or Slack) with summary and links to outputs

### Success Criteria
- [ ] Generates complete content packs with 3-10 posts (captions, hashtags, creative briefs, alt text, posting times)
- [ ] Runs 5-dimensional quality review (brand voice, compliance, hashtag hygiene, format validation, claims verification)
- [ ] Auto-publishes to Instagram Graph API when quality gates pass and mode is "auto_publish"
- [ ] Falls back to manual content packs when quality gates fail or mode is "content_pack_only"
- [ ] Outputs structured JSON + human-readable Markdown for each content pack
- [ ] Maintains rolling archive of content packs with latest.md index
- [ ] System runs autonomously via GitHub Actions on schedule
- [ ] Results are committed back to repo with clear naming (content_pack_2026-02-14.md)
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs
[What goes into the system. Be specific about format, source, and any validation requirements.]

```yaml
- name: "brand_profile"
  type: "JSON"
  source: "workflow input or config file (config/brand_profile.json)"
  required: true
  description: "Brand voice + guardrails defining tone, do/don't lists, target audience, products/services, banned topics, preferred CTAs, emoji style"
  example: |
    {
      "brand_name": "EcoFlow Energy",
      "tone": "friendly, informative, eco-conscious",
      "target_audience": "environmentally conscious consumers, ages 25-45",
      "products": ["solar panels", "home batteries", "EV chargers"],
      "banned_topics": ["politics", "religion", "controversial social issues"],
      "prohibited_claims": ["guaranteed savings", "100% renewable", "cure", "proven"],
      "preferred_cta": ["Learn more", "Shop now", "Get started", "Join the movement"],
      "emoji_style": "minimal (1-2 per post)",
      "hashtag_preferences": {
        "count": "8-12 per post",
        "avoid": ["generic", "spammy", "banned"]
      }
    }

- name: "weekly_theme"
  type: "string"
  source: "workflow input"
  required: true
  description: "The focus/topic for this week's posts (e.g., 'spring launch', 'behind the scenes', 'customer stories', 'product tips')"
  example: "Spring 2026 Product Launch - New Solar Roof Tiles"

- name: "post_plan"
  type: "JSON"
  source: "workflow input"
  required: true
  description: "Number and types of posts to create (reels, carousels, single images), with any required series/templates"
  example: |
    {
      "reels": 3,
      "carousels": 2,
      "single_images": 2,
      "stories": 0,
      "series": [
        {"name": "Tip Tuesday", "count": 1, "format": "single_image"},
        {"name": "Behind the Scenes", "count": 1, "format": "reel"}
      ],
      "posting_schedule": "spread evenly across 7 days, starting Monday 10 AM local time"
    }

- name: "reference_links"
  type: "JSON array"
  source: "workflow input (optional)"
  required: false
  description: "URLs to recent blog posts, announcements, or product pages to pull accurate details from"
  example: |
    [
      {"url": "https://ecoflow.com/blog/solar-roof-launch", "purpose": "product details"},
      {"url": "https://ecoflow.com/products/solar-roof-tiles", "purpose": "specs and pricing"}
    ]

- name: "publishing_mode"
  type: "choice: auto_publish | content_pack_only"
  source: "workflow input"
  required: true
  description: "Whether to auto-publish to Instagram (if quality gates pass) or always output content packs for manual upload"
  example: "content_pack_only"
```

## Outputs
[What comes out of the system. Where do results go?]

```yaml
- name: "content_pack_markdown"
  type: "Markdown"
  destination: "output/instagram/content_pack_{YYYY-MM-DD}.md"
  description: "Human-readable content pack with post-by-post details (hook, caption, CTA, hashtags, alt text, posting time, creative brief)"
  example: "output/instagram/content_pack_2026-02-14.md"

- name: "content_pack_json"
  type: "JSON"
  destination: "output/instagram/content_pack_{YYYY-MM-DD}.json"
  description: "Structured data for each post (machine-readable, suitable for automation)"
  example: |
    {
      "metadata": {
        "generated_at": "2026-02-14T09:15:00Z",
        "theme": "Spring 2026 Product Launch",
        "brand": "EcoFlow Energy",
        "total_posts": 7
      },
      "posts": [
        {
          "post_id": 1,
          "type": "reel",
          "posting_time": "2026-02-17T10:00:00-08:00",
          "hook": "☀️ Introducing the future of home energy",
          "caption": "Our new Solar Roof Tiles seamlessly integrate...",
          "cta": "Learn more (link in bio)",
          "hashtags": ["#SolarRoof", "#CleanEnergy", "#EcoFlowEnergy"],
          "alt_text": "Animated reel showing solar roof tiles installation",
          "creative_brief": "15-30s reel: time-lapse of installation, cut to house powering at night",
          "image_prompt": "realistic photo: modern house with sleek black solar roof tiles, golden hour lighting"
        }
      ]
    }

- name: "review_report"
  type: "Markdown"
  destination: "output/instagram/review_report_{YYYY-MM-DD}.md"
  description: "Quality review results (brand voice match score, compliance checks, hashtag hygiene, format validation)"
  example: |
    # Quality Review Report - 2026-02-14
    
    ## Overall Score: 87/100 ✅ PASS
    
    ### Brand Voice Alignment: 90/100
    - Tone match: Excellent (friendly, informative)
    - Audience fit: Strong (eco-conscious messaging)
    - Minor issue: Post 3 uses slightly formal language
    
    ### Compliance Checks: 100/100
    - No banned topics detected
    - No prohibited claims found
    - All CTAs approved
    
    ### Hashtag Hygiene: 85/100
    - Count: 8-12 per post ✓
    - No banned hashtags ✓
    - 2 generic hashtags flagged (#love, #instagood) - consider alternatives
    
    ### Format Validation: 80/100
    - Caption lengths OK (all under 2200 chars)
    - Alt text present for all posts ✓
    - 1 creative brief lacks technical detail
    
    ### Claims Verification: 100/100
    - All factual claims sourced from reference links ✓
    - No unsupported statistics

- name: "publish_log"
  type: "JSON"
  destination: "output/instagram/publish_log_{YYYY-MM-DD}.json (only if auto_publish mode)"
  description: "Instagram Graph API response for each published post (media IDs, URLs, or failure reasons)"
  example: |
    {
      "published_at": "2026-02-14T09:20:00Z",
      "mode": "auto_publish",
      "results": [
        {
          "post_id": 1,
          "status": "success",
          "ig_media_id": "17895695668004550",
          "ig_permalink": "https://instagram.com/p/ABC123/",
          "scheduled_for": "2026-02-17T10:00:00-08:00"
        },
        {
          "post_id": 2,
          "status": "failed",
          "error": "Rate limit exceeded - retry in 3600s",
          "fallback": "content included in manual upload pack"
        }
      ]
    }

- name: "upload_checklist"
  type: "Markdown"
  destination: "output/instagram/upload_checklist_{YYYY-MM-DD}.md (only if content_pack_only mode)"
  description: "Manual upload instructions with copy-paste ready captions, hashtag lists, and posting times"
  example: "output/instagram/upload_checklist_2026-02-14.md"

- name: "latest_index"
  type: "Markdown"
  destination: "output/instagram/latest.md (updated each run)"
  description: "Rolling index pointing to the most recent content pack with quick links"
  example: |
    # Latest Instagram Content Pack
    
    **Generated:** 2026-02-14 09:15 UTC
    **Theme:** Spring 2026 Product Launch
    
    - [Content Pack (Markdown)](./content_pack_2026-02-14.md)
    - [Content Pack (JSON)](./content_pack_2026-02-14.json)
    - [Review Report](./review_report_2026-02-14.md)
    - [Upload Checklist](./upload_checklist_2026-02-14.md)
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://developers.facebook.com/docs/instagram-api/overview"
  why: "Instagram Graph API overview - authentication, endpoints, rate limits"

- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-user/media"
  why: "Creating Instagram posts via API - required fields, media types, error codes"

- url: "https://developers.facebook.com/docs/instagram-api/reference/ig-user/media_publish"
  why: "Publishing flow - container creation, media publish, scheduling"

- url: "https://developers.facebook.com/docs/instagram-api/guides/content-publishing"
  why: "Content publishing guide - image requirements, video specs, carousel format"

- url: "https://developers.facebook.com/docs/graph-api/overview/rate-limiting"
  why: "Rate limits - 200 API calls per hour per user, batch request limits"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide Firecrawl (reference content), Anthropic (generation), HTTP (Instagram API)"

- doc: "library/patterns.md"
  why: "Primary pattern: Generate > Review > Publish. Secondary: Fan-Out > Process > Merge for parallel post generation"

- doc: "library/tool_catalog.md"
  why: "Reusable patterns: llm_prompt, structured_extract, multi_dimension_scorer, rest_client, json_read_write"

- url: "https://help.instagram.com/478745558852297"
  why: "Instagram Community Guidelines - what content is prohibited"

- url: "https://business.instagram.com/blog/instagram-algorithm-ranking-system"
  why: "Best practices for captions, hashtags, engagement optimization"
```

### Workflow Pattern Selection
```yaml
# Reference library/patterns.md — select the best-fit pattern
pattern: "Generate > Review > Publish"
rationale: |
  This system follows the classic two-pass content creation flow:
  1. Generate: Claude produces draft content for all posts
  2. Review: Automated quality gates check brand voice, compliance, format
  3. Publish: Either auto-publish to IG API or output manual content packs
  
  The review step is critical - it prevents off-brand or non-compliant content from reaching production.

modifications: |
  - Add Fan-Out > Process > Merge (Agent Teams) for parallel post generation (3+ posts = independent tasks)
  - Add Sequential State Management for tracking published posts and preventing duplicates
  - Gate decision: Quality review score determines auto-publish vs manual fallback

secondary_pattern: "Fan-Out > Process > Merge (Agent Teams)"
rationale: |
  If post_plan specifies 3+ posts (e.g., "3 reels + 2 carousels + 2 singles" = 7 independent tasks),
  use Agent Teams to generate all posts in parallel. Each teammate generates one post type,
  team lead merges results and coordinates review.
  
  Sequential generation of 7 posts = ~70-90 seconds
  Parallel generation with Agent Teams = ~12-18 seconds (5x faster, same token cost)
```

### MCP & Tool Requirements
```yaml
# Reference config/mcp_registry.md — list capabilities needed
capabilities:
  - name: "Reference content extraction"
    primary_mcp: "firecrawl"
    alternative_mcp: "fetch"
    fallback: "Direct HTTP with requests + BeautifulSoup"
    secret_name: "FIRECRAWL_API_KEY"

  - name: "AI content generation"
    primary_mcp: "anthropic"
    alternative_mcp: "openai"
    fallback: "N/A - generation requires LLM"
    secret_name: "ANTHROPIC_API_KEY"

  - name: "Instagram Graph API"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "Direct HTTP API via rest_client tool pattern"
    secret_name: "INSTAGRAM_ACCESS_TOKEN"

  - name: "Structured data extraction"
    primary_mcp: "anthropic"
    alternative_mcp: "openai"
    fallback: "Regex + manual parsing"
    secret_name: "ANTHROPIC_API_KEY"

  - name: "Notifications"
    primary_mcp: "slack (optional)"
    alternative_mcp: "email (smtp)"
    fallback: "GitHub Issue comment"
    secret_name: "SLACK_WEBHOOK_URL or SMTP_PASSWORD"
```

### Known Gotchas & Constraints
```
# CRITICAL: Instagram Graph API rate limit is 200 calls/hour per user
# CRITICAL: Media must be publicly accessible HTTPS URLs for Graph API upload
# CRITICAL: Carousel posts require 2-10 media items, all must be same type (all images or all videos)
# CRITICAL: Reels must be MP4, H.264 codec, 1080x1920 (9:16), max 90 seconds, max 100MB
# CRITICAL: Captions max 2200 characters, but optimal is 125-150 for full visibility before "more" button
# CRITICAL: Hashtags count toward caption character limit, optimal count is 8-12 (not 30)
# CRITICAL: Alt text (accessibility caption) is separate field, max 100 characters
# CRITICAL: Scheduled posts require Business or Creator account, max 75 scheduled posts at once
# CRITICAL: Access tokens expire - use long-lived tokens (60 days), implement refresh flow
# CRITICAL: Cannot publish to other users' accounts - must authenticate as account owner
# CRITICAL: Brand voice scoring requires examples of on-brand vs off-brand content in the prompt
# CRITICAL: Compliance checks must include FTC guidelines for sponsored/affiliate content if applicable
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: Image prompts for generative AI are guidance only - this system does NOT generate images
# CRITICAL: Creative briefs are instructions for manual content creation or briefing designers
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents:
  - name: "content-strategist"
    description: |
      Delegate when you need to plan the content strategy for the week:
      - Analyze brand profile and weekly theme
      - Determine post mix and sequencing
      - Create content pillars and messaging framework
      - Suggest optimal posting times
      - Coordinate with reference content extraction
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Parse brand_profile.json and weekly_theme input"
      - "Fetch and extract content from reference_links URLs (via Firecrawl)"
      - "Synthesize brand voice, theme, and reference material into content strategy"
      - "Generate posting schedule with optimal times"
      - "Create content brief for each post type (reels, carousels, singles)"
    inputs: "brand_profile (JSON), weekly_theme (string), post_plan (JSON), reference_links (array)"
    outputs: "content_strategy.json with post briefs, themes, posting schedule"

  - name: "copywriter-specialist"
    description: |
      Delegate when you need to generate Instagram copy (captions, hooks, CTAs):
      - Write engaging hooks (first 125 chars)
      - Craft full captions matching brand voice
      - Generate CTAs aligned with brand preferences
      - Write alt text for accessibility
      - Ensure tone, style, and emoji usage match brand guidelines
    tools: "Read, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read content brief from strategist"
      - "Generate hook (attention-grabbing first line)"
      - "Write full caption (125-300 words, brand voice matched)"
      - "Select appropriate CTA from brand preferences"
      - "Write descriptive alt text (max 100 chars)"
      - "Apply emoji style per brand guidelines"
    inputs: "content brief (JSON), brand_profile (JSON)"
    outputs: "post_copy.json with hook, caption, cta, alt_text for each post"

  - name: "hashtag-specialist"
    description: |
      Delegate when you need to generate hashtag sets:
      - Research trending hashtags relevant to theme
      - Generate mix of broad/niche hashtags (8-12 per post)
      - Avoid banned, generic, or spammy hashtags
      - Ensure hashtags match brand preferences
      - Validate hashtag hygiene
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Research hashtags relevant to weekly theme and brand"
      - "Generate 8-12 hashtags per post (mix of sizes)"
      - "Filter out banned, generic, spammy hashtags"
      - "Check against brand hashtag preferences"
      - "Validate total character count (hashtags count toward 2200 limit)"
    inputs: "weekly_theme (string), brand_profile (JSON), post_type (string)"
    outputs: "hashtags.json with 8-12 hashtags per post, size breakdown"

  - name: "creative-director"
    description: |
      Delegate when you need to create creative briefs and image prompts:
      - Write creative briefs for video/image production
      - Generate AI image prompts (for guidance, not generation)
      - Specify technical requirements (aspect ratio, format, duration)
      - Suggest visual themes and styling
      - Align creative direction with brand guidelines
    tools: "Read, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read content brief and copy"
      - "Write creative brief for each post (what to show, how to shoot/design)"
      - "Generate image prompt for AI guidance (style, composition, mood)"
      - "Specify technical requirements (1080x1080 for feed, 1080x1920 for reels, etc.)"
      - "Ensure visual direction matches brand aesthetic"
    inputs: "content brief (JSON), post_copy (JSON), brand_profile (JSON)"
    outputs: "creative_briefs.json with brief, image_prompt, technical_specs per post"

  - name: "reviewer-specialist"
    description: |
      Delegate when you need to run quality review and compliance checks:
      - Score brand voice alignment (0-100)
      - Check for banned topics and prohibited claims
      - Validate hashtag hygiene
      - Verify Instagram format compliance
      - Cross-check claims against reference content
      - Generate review report with pass/fail decision
    tools: "Read, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Load all generated content (copy, hashtags, creative briefs)"
      - "Score brand voice alignment across 5 dimensions"
      - "Scan for banned topics from brand_profile"
      - "Check for prohibited claims (guarantees, medical claims, etc.)"
      - "Validate hashtag count, banned hashtags, generic hashtags"
      - "Verify caption length, alt text presence, technical specs"
      - "Cross-reference factual claims with reference content"
      - "Calculate overall quality score"
      - "Generate detailed review report"
      - "Return pass/fail decision for auto-publish gate"
    inputs: "generated_content (JSON), brand_profile (JSON), reference_content (text)"
    outputs: "review_report.json with scores, issues, pass/fail decision"

  - name: "instagram-publisher"
    description: |
      Delegate when you need to publish to Instagram Graph API or prepare manual upload:
      - Format content for Instagram Graph API
      - Handle media container creation
      - Execute publish API calls with retry logic
      - Handle rate limiting (200 calls/hour)
      - Fall back to manual content pack on API failure
      - Generate publish log or upload checklist
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Check publishing_mode (auto_publish vs content_pack_only)"
      - "If auto_publish: Format posts for Instagram Graph API"
      - "Create media containers for each post (images/videos must be public URLs)"
      - "Execute publish API calls with exponential backoff retry"
      - "Handle rate limits (pause and resume)"
      - "Log publish results (media IDs, permalinks, errors)"
      - "If content_pack_only OR publish fails: Generate manual upload checklist"
      - "Format upload checklist with copy-paste ready captions, hashtags, times"
    inputs: "generated_content (JSON), review_report (JSON), publishing_mode (string)"
    outputs: "publish_log.json OR upload_checklist.md"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "Generate reel post 1 (hook, caption, CTA, hashtags, creative brief, image prompt)"
  - "Generate reel post 2 (independent of post 1)"
  - "Generate reel post 3 (independent of posts 1-2)"
  - "Generate carousel post 1 (independent of reels)"
  - "Generate carousel post 2 (independent of other posts)"
  - "Generate single image post 1 (independent of other posts)"
  - "Generate single image post 2 (independent of other posts)"

independent_task_count: "7 (for a typical post_plan with 3 reels + 2 carousels + 2 singles)"
recommendation: "Use Agent Teams for post generation phase"
rationale: |
  Each post is an independent unit of work - it doesn't depend on other posts being generated first.
  Sequential generation: ~10-15 seconds per post × 7 posts = 70-105 seconds
  Parallel with Agent Teams: ~12-18 seconds (all 7 posts generated simultaneously)
  
  Result: 5x wall-time speedup, same token cost, identical quality.
  
  Exception: If post_plan specifies fewer than 3 posts, use sequential (overhead not justified).

# Agent Teams structure for post generation
team_lead_responsibilities:
  - "Read content_strategy.json from content-strategist"
  - "Create post generation task list (one per post in post_plan)"
  - "Spawn 1 teammate per post (or batch into groups of 3-4 if >10 posts)"
  - "Each teammate generates: hook, caption, CTA, hashtags, alt_text, creative_brief, image_prompt"
  - "Merge all teammate results into unified generated_content.json"
  - "Run consistency check (ensure no duplicate hooks/captions across posts)"
  - "Pass to reviewer-specialist for quality gates"

teammates:
  - name: "post-generator-reel-1"
    task: "Generate complete content for Reel Post 1 per content brief"
    inputs: "content_strategy.json (brief for reel 1), brand_profile.json"
    outputs: "reel_1_content.json {hook, caption, cta, hashtags, alt_text, creative_brief, image_prompt}"

  - name: "post-generator-carousel-1"
    task: "Generate complete content for Carousel Post 1 per content brief"
    inputs: "content_strategy.json (brief for carousel 1), brand_profile.json"
    outputs: "carousel_1_content.json {hook, caption, cta, hashtags, alt_text, creative_brief, image_prompt}"

  # ... one teammate per post in post_plan

sequential_fallback: |
  If Agent Teams is not available OR post count < 3:
  - Main agent generates posts sequentially
  - Delegates to copywriter-specialist, hashtag-specialist, creative-director in sequence
  - Produces identical output structure
  - Takes longer wall time but requires no parallelization infrastructure
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "cron: '0 9 * * 1'  # Every Monday at 09:00 UTC"
    description: "Weekly automated content generation for standard posting schedule"

  - type: "workflow_dispatch"
    config: |
      inputs:
        brand_profile_path:
          description: 'Path to brand profile JSON file'
          required: true
          default: 'config/brand_profile.json'
        weekly_theme:
          description: 'Weekly theme or campaign focus'
          required: true
        post_plan:
          description: 'JSON post plan (reels, carousels, singles counts)'
          required: true
        reference_links:
          description: 'JSON array of reference URLs (optional)'
          required: false
          default: '[]'
        publishing_mode:
          description: 'Publishing mode'
          required: true
          type: choice
          options:
            - content_pack_only
            - auto_publish
          default: 'content_pack_only'
    description: "Manual trigger for ad-hoc campaigns or testing"

  - type: "issues"
    config: |
      types: [opened, labeled]
      # Trigger when issue is labeled 'instagram-content-request'
    description: "Agent HQ pattern - open issue with content request, system processes and comments with results"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "1. Input Validation & Setup"
    description: "Parse inputs, validate required fields, load brand profile, initialize output directory structure"
    subagent: "none (main agent)"
    tools: ["validate_inputs.py", "setup_output.py"]
    inputs: "brand_profile_path, weekly_theme, post_plan, reference_links, publishing_mode (all from workflow inputs)"
    outputs: "validated_inputs.json, output directory initialized (output/instagram/YYYY-MM-DD/)"
    failure_mode: "Missing required fields, invalid JSON, brand_profile.json not found"
    fallback: "Halt workflow with clear error message listing missing/invalid inputs. Do not proceed."

  - name: "2. Reference Content Extraction"
    description: "Fetch and extract clean content from reference URLs using Firecrawl, fall back to HTTP+BeautifulSoup if Firecrawl unavailable"
    subagent: "content-strategist"
    tools: ["fetch_reference_content.py"]
    inputs: "reference_links (array of URLs), validated_inputs.json"
    outputs: "reference_content.json with extracted text, metadata, links from each URL"
    failure_mode: "URL unreachable, paywall, timeout, invalid response"
    fallback: "Log failed URL, continue with available references. If ALL references fail, proceed without reference content (flag in strategy as 'no reference material')."

  - name: "3. Content Strategy Generation"
    description: "Analyze brand voice, weekly theme, post plan, and reference content. Generate content strategy with per-post briefs, themes, posting schedule."
    subagent: "content-strategist"
    tools: ["generate_content_strategy.py"]
    inputs: "validated_inputs.json, reference_content.json, brand_profile.json"
    outputs: "content_strategy.json with post briefs (one per post in post_plan), posting schedule, content themes"
    failure_mode: "LLM API failure, insufficient context, unclear theme"
    fallback: "Retry once with simplified prompt. If fails again, halt and open GitHub Issue requesting human clarification of theme."

  - name: "4. Post Generation (Parallel with Agent Teams)"
    description: "Generate all post content in parallel (if 3+ posts) using Agent Teams. Each teammate generates one post: hook, caption, CTA, hashtags, alt text, creative brief, image prompt."
    subagent: "Team lead (coordinates) + teammates (one per post)"
    tools: ["generate_post_content.py (parallelized via Agent Teams)"]
    inputs: "content_strategy.json, brand_profile.json"
    outputs: "generated_content.json with complete content for all posts"
    failure_mode: "LLM API failure, teammate timeout, incomplete generation"
    fallback: "If Agent Teams fails, fall back to sequential generation (main agent + copywriter/hashtag/creative subagents). Slower but produces identical output."

  - name: "5. Quality Review & Compliance Checks"
    description: "Run multi-dimensional quality review: brand voice alignment, compliance (banned topics, prohibited claims), hashtag hygiene, format validation, claims verification."
    subagent: "reviewer-specialist"
    tools: ["review_content.py"]
    inputs: "generated_content.json, brand_profile.json, reference_content.json"
    outputs: "review_report.json with scores (brand_voice, compliance, hashtags, format, claims), overall score, pass/fail decision, detailed issues list"
    failure_mode: "LLM API failure during review"
    fallback: "Retry review once. If fails, default to FAIL (conservative - do not auto-publish without review). Output content pack for manual review."

  - name: "6. Gate Decision: Auto-Publish vs Manual Content Pack"
    description: "Check review_report.json overall score and publishing_mode. If score >= 80/100 AND mode = auto_publish: proceed to publish. Otherwise: generate manual content pack."
    subagent: "none (main agent)"
    tools: ["gate_decision.py"]
    inputs: "review_report.json, publishing_mode (from inputs)"
    outputs: "publish_decision.json with action (publish | manual_pack), rationale"
    failure_mode: "N/A (deterministic logic)"
    fallback: "N/A"

  - name: "7a. Auto-Publish to Instagram (if gate passes)"
    description: "Format posts for Instagram Graph API, create media containers, execute publish API calls with retry logic, handle rate limiting, log results."
    subagent: "instagram-publisher"
    tools: ["publish_to_instagram.py"]
    inputs: "generated_content.json, publish_decision.json, INSTAGRAM_ACCESS_TOKEN"
    outputs: "publish_log.json with media IDs, permalinks, scheduled times, or error details"
    failure_mode: "Rate limit (200/hour), auth failure, media URL not accessible, API error"
    fallback: "On rate limit: pause, log next retry time. On auth/media failure: halt publish, fall back to step 7b (manual content pack), log specific error."

  - name: "7b. Generate Manual Content Pack (if gate fails OR auto-publish fails)"
    description: "Generate human-readable Markdown and JSON content packs, plus upload checklist with copy-paste ready captions, hashtags, posting times."
    subagent: "instagram-publisher"
    tools: ["generate_content_pack.py", "generate_upload_checklist.py"]
    inputs: "generated_content.json, review_report.json"
    outputs: "content_pack_YYYY-MM-DD.md, content_pack_YYYY-MM-DD.json, upload_checklist_YYYY-MM-DD.md"
    failure_mode: "File write failure"
    fallback: "Retry write once. If fails, log to stdout so GitHub Actions captures it in logs."

  - name: "8. Update Latest Index & Archive"
    description: "Update latest.md with links to current content pack. Commit all outputs to repo. Maintain rolling archive (keep last 12 weeks, delete older)."
    subagent: "none (main agent)"
    tools: ["update_latest_index.py", "archive_cleanup.py"]
    inputs: "All output files from step 7a/7b"
    outputs: "latest.md updated, old archives pruned (12-week retention)"
    failure_mode: "Git commit failure"
    fallback: "Retry commit once. If fails, outputs still exist locally (GitHub Actions artifacts can preserve them)."

  - name: "9. Notification & Summary"
    description: "Post summary to GitHub Issue (Agent HQ) or send Slack notification. Include links to outputs, review score, publish status."
    subagent: "none (main agent)"
    tools: ["send_notification.py"]
    inputs: "review_report.json, publish_log.json OR upload_checklist path, publish_decision.json"
    outputs: "GitHub comment OR Slack message with summary + links"
    failure_mode: "Notification delivery failure (Slack API, GitHub API)"
    fallback: "Log notification failure. Do not halt workflow - outputs are still committed to repo."
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "validate_inputs.py"
    purpose: "Parse and validate all workflow inputs (brand_profile, weekly_theme, post_plan, reference_links, publishing_mode)"
    catalog_pattern: "new"
    inputs:
      - "brand_profile_path: str — Path to brand profile JSON file"
      - "weekly_theme: str — Weekly content theme"
      - "post_plan: str — JSON string with post counts and types"
      - "reference_links: str — JSON array of URLs (optional)"
      - "publishing_mode: str — auto_publish or content_pack_only"
    outputs: "validated_inputs.json with parsed and validated data"
    dependencies: ["json", "pathlib", "jsonschema"]
    mcp_used: "none"
    error_handling: "Raises ValueError with specific field if validation fails. Main workflow catches and halts."

  - name: "setup_output.py"
    purpose: "Initialize output directory structure for this run (output/instagram/YYYY-MM-DD/)"
    catalog_pattern: "new"
    inputs:
      - "base_path: str — Base output path (default: output/instagram)"
    outputs: "Created directories, returns output_dir path"
    dependencies: ["pathlib"]
    mcp_used: "none"
    error_handling: "Creates directories if missing. Logs warning if directory exists (overwrite scenario)."

  - name: "fetch_reference_content.py"
    purpose: "Fetch and extract clean content from reference URLs using Firecrawl, fall back to HTTP+BeautifulSoup"
    catalog_pattern: "firecrawl_scrape + rest_client fallback"
    inputs:
      - "reference_links: list[dict] — Array of {url, purpose} objects"
    outputs: "reference_content.json with {url, content, metadata, success} per link"
    dependencies: ["firecrawl-py", "httpx", "beautifulsoup4"]
    mcp_used: "firecrawl (primary), none (fallback)"
    error_handling: "Try Firecrawl first. On failure, try HTTP GET + BeautifulSoup. Log failure and continue if both fail."

  - name: "generate_content_strategy.py"
    purpose: "Generate content strategy: post briefs, themes, posting schedule based on brand voice and weekly theme"
    catalog_pattern: "structured_extract"
    inputs:
      - "brand_profile: dict — Brand voice and guardrails"
      - "weekly_theme: str — Content theme"
      - "post_plan: dict — Post counts and types"
      - "reference_content: dict — Extracted reference material"
    outputs: "content_strategy.json with per-post briefs, themes, schedule"
    dependencies: ["anthropic"]
    mcp_used: "anthropic"
    error_handling: "Retry once with simplified prompt on LLM failure. Raise exception if both attempts fail."

  - name: "generate_post_content.py"
    purpose: "Generate complete post content (hook, caption, CTA, hashtags, alt text, creative brief, image prompt) for all posts. Supports both parallel (Agent Teams) and sequential execution."
    catalog_pattern: "llm_prompt + structured_extract (parallelized)"
    inputs:
      - "content_strategy: dict — Post briefs from strategist"
      - "brand_profile: dict — Brand voice guidelines"
      - "use_agent_teams: bool — True if 3+ posts, False otherwise"
    outputs: "generated_content.json with complete content for all posts"
    dependencies: ["anthropic", "json"]
    mcp_used: "anthropic"
    error_handling: "If Agent Teams fails, fall back to sequential generation. Log mode used (parallel vs sequential)."

  - name: "review_content.py"
    purpose: "Run multi-dimensional quality review: brand voice (0-100), compliance checks, hashtag hygiene, format validation, claims verification. Output pass/fail decision."
    catalog_pattern: "multi_dimension_scorer + structured_extract"
    inputs:
      - "generated_content: dict — All post content"
      - "brand_profile: dict — Brand voice and guardrails"
      - "reference_content: dict — For claims verification"
    outputs: "review_report.json with dimension scores, overall score, pass/fail, detailed issues"
    dependencies: ["anthropic", "json"]
    mcp_used: "anthropic"
    error_handling: "Retry once on LLM failure. If fails, return FAIL decision (conservative default)."

  - name: "gate_decision.py"
    purpose: "Evaluate review score and publishing_mode. Decide: auto-publish OR manual content pack."
    catalog_pattern: "new"
    inputs:
      - "review_report: dict — Review scores and pass/fail"
      - "publishing_mode: str — auto_publish or content_pack_only"
    outputs: "publish_decision.json with action (publish | manual_pack) and rationale"
    dependencies: ["json"]
    mcp_used: "none"
    error_handling: "Deterministic logic - no failure modes."

  - name: "publish_to_instagram.py"
    purpose: "Publish posts to Instagram via Graph API. Create media containers, execute publish calls, handle rate limiting, log results."
    catalog_pattern: "rest_client + oauth_token_refresh"
    inputs:
      - "generated_content: dict — Posts to publish"
      - "access_token: str — Instagram Graph API token (from env)"
      - "ig_user_id: str — Instagram Business Account ID (from env)"
    outputs: "publish_log.json with media IDs, permalinks, errors"
    dependencies: ["httpx", "tenacity"]
    mcp_used: "none (direct HTTP)"
    error_handling: "Retry with exponential backoff on transient errors. On rate limit (429), log and halt. On auth failure, halt and log error."

  - name: "generate_content_pack.py"
    purpose: "Generate human-readable Markdown content pack from generated_content.json"
    catalog_pattern: "json_read_write"
    inputs:
      - "generated_content: dict — All post content"
      - "review_report: dict — Review scores"
      - "output_dir: str — Where to write file"
    outputs: "content_pack_YYYY-MM-DD.md and content_pack_YYYY-MM-DD.json"
    dependencies: ["json", "pathlib"]
    mcp_used: "none"
    error_handling: "Retry write once on IOError. Log error if fails."

  - name: "generate_upload_checklist.py"
    purpose: "Generate manual upload checklist with copy-paste ready captions, hashtags, posting times"
    catalog_pattern: "new"
    inputs:
      - "generated_content: dict — All post content"
      - "output_dir: str — Where to write file"
    outputs: "upload_checklist_YYYY-MM-DD.md"
    dependencies: ["pathlib"]
    mcp_used: "none"
    error_handling: "Retry write once on IOError."

  - name: "update_latest_index.py"
    purpose: "Update latest.md with links to current content pack"
    catalog_pattern: "new"
    inputs:
      - "content_pack_path: str — Path to current content pack"
      - "review_report_path: str — Path to review report"
      - "latest_index_path: str — Path to latest.md (default: output/instagram/latest.md)"
    outputs: "Updated latest.md"
    dependencies: ["pathlib"]
    mcp_used: "none"
    error_handling: "Create latest.md if missing. Overwrite existing."

  - name: "archive_cleanup.py"
    purpose: "Prune old content packs (keep last 12 weeks, delete older)"
    catalog_pattern: "new"
    inputs:
      - "archive_dir: str — Path to archive directory (output/instagram/)"
      - "retention_weeks: int — How many weeks to keep (default: 12)"
    outputs: "List of deleted files"
    dependencies: ["pathlib", "datetime"]
    mcp_used: "none"
    error_handling: "Log deletion errors but continue (old archives are not critical)."

  - name: "send_notification.py"
    purpose: "Send summary notification to GitHub Issue comment or Slack"
    catalog_pattern: "slack_notify + github_create_issue"
    inputs:
      - "summary: dict — Workflow summary data"
      - "notification_target: str — github or slack"
      - "target_id: str — Issue number or Slack channel"
    outputs: "Notification sent confirmation"
    dependencies: ["httpx"]
    mcp_used: "slack (optional)"
    error_handling: "Log failure but do not halt workflow. Outputs are in repo regardless of notification success."
```

### Per-Tool Pseudocode
```python
# validate_inputs.py
def main():
    # PATTERN: Input validation with JSON schema
    # Step 1: Parse inputs from args or env
    args = parse_args()  # brand_profile_path, weekly_theme, post_plan, reference_links, publishing_mode

    # Step 2: Load brand_profile.json
    # GOTCHA: Path might be relative or absolute
    brand_profile = json.loads(Path(args.brand_profile_path).read_text())

    # Step 3: Validate required fields in brand_profile
    required = ["brand_name", "tone", "target_audience", "products", "banned_topics", "preferred_cta"]
    for field in required:
        if field not in brand_profile:
            raise ValueError(f"Missing required field in brand_profile: {field}")

    # Step 4: Parse and validate post_plan JSON
    post_plan = json.loads(args.post_plan)
    if not any(k in post_plan for k in ["reels", "carousels", "single_images"]):
        raise ValueError("post_plan must specify at least one post type")

    # Step 5: Parse reference_links (optional)
    reference_links = json.loads(args.reference_links) if args.reference_links else []

    # Step 6: Validate publishing_mode
    if args.publishing_mode not in ["auto_publish", "content_pack_only"]:
        raise ValueError(f"Invalid publishing_mode: {args.publishing_mode}")

    # Step 7: Output validated inputs
    output = {
        "brand_profile": brand_profile,
        "weekly_theme": args.weekly_theme,
        "post_plan": post_plan,
        "reference_links": reference_links,
        "publishing_mode": args.publishing_mode
    }
    print(json.dumps(output, indent=2))

# fetch_reference_content.py
def main():
    # PATTERN: firecrawl_scrape with HTTP fallback
    # CRITICAL: Firecrawl requires API key, HTTP fallback does not
    args = parse_args()  # reference_links (JSON array)
    results = []

    for link in json.loads(args.reference_links):
        url = link["url"]
        try:
            # Try Firecrawl first
            from firecrawl import FirecrawlApp
            app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
            scraped = app.scrape_url(url, params={"formats": ["markdown"]})
            results.append({
                "url": url,
                "content": scraped.get("markdown", ""),
                "metadata": scraped.get("metadata", {}),
                "success": True,
                "method": "firecrawl"
            })
        except Exception as e:
            logging.warning(f"Firecrawl failed for {url}: {e}, trying HTTP fallback")
            try:
                # HTTP + BeautifulSoup fallback
                import httpx
                from bs4 import BeautifulSoup
                resp = httpx.get(url, timeout=15, follow_redirects=True)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                # Extract main content (heuristic: get all <p> tags)
                content = "\n\n".join(p.get_text() for p in soup.find_all("p"))
                results.append({
                    "url": url,
                    "content": content,
                    "metadata": {"title": soup.title.string if soup.title else ""},
                    "success": True,
                    "method": "http_fallback"
                })
            except Exception as e2:
                logging.error(f"Both Firecrawl and HTTP failed for {url}: {e2}")
                results.append({
                    "url": url,
                    "content": "",
                    "metadata": {},
                    "success": False,
                    "error": str(e2)
                })

    print(json.dumps({"reference_content": results}, indent=2))

# generate_content_strategy.py
def main():
    # PATTERN: structured_extract
    # CRITICAL: Prompt must include brand voice examples, weekly theme context, reference material
    args = parse_args()
    brand_profile = json.loads(args.brand_profile)
    weekly_theme = args.weekly_theme
    post_plan = json.loads(args.post_plan)
    reference_content = json.loads(args.reference_content)

    # Build context for LLM
    context = f"""
    Brand: {brand_profile['brand_name']}
    Tone: {brand_profile['tone']}
    Target Audience: {brand_profile['target_audience']}
    Weekly Theme: {weekly_theme}

    Post Plan:
    - Reels: {post_plan.get('reels', 0)}
    - Carousels: {post_plan.get('carousels', 0)}
    - Single Images: {post_plan.get('single_images', 0)}

    Reference Material:
    {reference_content}

    Generate a content strategy with per-post briefs.
    """

    schema = {
        "type": "object",
        "properties": {
            "post_briefs": {"type": "array", "items": {"type": "object"}},
            "posting_schedule": {"type": "array"},
            "content_themes": {"type": "array"}
        },
        "required": ["post_briefs", "posting_schedule"]
    }

    # Call structured_extract (uses Anthropic with JSON schema validation)
    result = structured_extract(context, schema, retries=2)
    print(json.dumps(result["data"], indent=2))

# generate_post_content.py
def main():
    # PATTERN: llm_prompt + structured_extract (parallelized with Agent Teams if 3+ posts)
    # CRITICAL: Check post count to decide parallel vs sequential
    args = parse_args()
    content_strategy = json.loads(args.content_strategy)
    brand_profile = json.loads(args.brand_profile)
    post_briefs = content_strategy["post_briefs"]

    if len(post_briefs) >= 3 and args.use_agent_teams:
        # Parallel generation with Agent Teams
        logging.info("Using Agent Teams for parallel generation")
        # Team lead creates task list, spawns teammates
        # Each teammate generates one post
        # Merge results
        generated_posts = agent_teams_generate(post_briefs, brand_profile)
    else:
        # Sequential generation
        logging.info("Using sequential generation")
        generated_posts = []
        for brief in post_briefs:
            post = generate_single_post(brief, brand_profile)
            generated_posts.append(post)

    print(json.dumps({"posts": generated_posts}, indent=2))

# review_content.py
def main():
    # PATTERN: multi_dimension_scorer + structured_extract
    # CRITICAL: 5 dimensions - brand_voice, compliance, hashtags, format, claims
    args = parse_args()
    generated_content = json.loads(args.generated_content)
    brand_profile = json.loads(args.brand_profile)
    reference_content = json.loads(args.reference_content)

    dimensions = [
        {"name": "brand_voice", "max_points": 100, "scorer": score_brand_voice},
        {"name": "compliance", "max_points": 100, "scorer": score_compliance},
        {"name": "hashtags", "max_points": 100, "scorer": score_hashtags},
        {"name": "format", "max_points": 100, "scorer": score_format},
        {"name": "claims", "max_points": 100, "scorer": score_claims}
    ]

    scores = {}
    for dim in dimensions:
        scores[dim["name"]] = dim["scorer"](generated_content, brand_profile, reference_content)

    overall = sum(scores.values()) / len(scores)
    pass_fail = "PASS" if overall >= 80 else "FAIL"

    report = {
        "scores": scores,
        "overall_score": overall,
        "pass_fail": pass_fail,
        "issues": []  # Detailed issues list from scorers
    }

    print(json.dumps(report, indent=2))

# publish_to_instagram.py
def main():
    # PATTERN: rest_client + exponential backoff retry
    # CRITICAL: Instagram Graph API requires public HTTPS URLs for media
    # CRITICAL: Rate limit is 200 calls/hour
    args = parse_args()
    generated_content = json.loads(args.generated_content)
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    ig_user_id = os.environ["INSTAGRAM_USER_ID"]

    results = []
    for post in generated_content["posts"]:
        try:
            # Step 1: Create media container (requires media URL)
            # GOTCHA: Media must be publicly accessible HTTPS URL
            container_resp = create_media_container(post, ig_user_id, access_token)
            container_id = container_resp["id"]

            # Step 2: Publish media container
            publish_resp = publish_media(container_id, ig_user_id, access_token)

            results.append({
                "post_id": post["post_id"],
                "status": "success",
                "ig_media_id": publish_resp["id"],
                "ig_permalink": f"https://instagram.com/p/{publish_resp['id']}"
            })
        except HTTPError as e:
            if e.response.status_code == 429:
                # Rate limit hit
                logging.error("Rate limit exceeded, halting publish")
                results.append({
                    "post_id": post["post_id"],
                    "status": "failed",
                    "error": "Rate limit exceeded"
                })
                break
            else:
                results.append({
                    "post_id": post["post_id"],
                    "status": "failed",
                    "error": str(e)
                })

    print(json.dumps({"results": results}, indent=2))

# generate_content_pack.py
def main():
    # PATTERN: json_read_write
    args = parse_args()
    generated_content = json.loads(args.generated_content)
    review_report = json.loads(args.review_report)
    output_dir = Path(args.output_dir)

    # Write JSON
    json_path = output_dir / f"content_pack_{datetime.now().strftime('%Y-%m-%d')}.json"
    json_path.write_text(json.dumps(generated_content, indent=2))

    # Write Markdown
    md_path = output_dir / f"content_pack_{datetime.now().strftime('%Y-%m-%d')}.md"
    md_content = format_content_pack_markdown(generated_content, review_report)
    md_path.write_text(md_content)

    print(json.dumps({"json_path": str(json_path), "md_path": str(md_path)}, indent=2))
```

### Integration Points
```yaml
SECRETS:
  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API for reference content extraction"
    required: true

  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API for content generation and review"
    required: true

  - name: "INSTAGRAM_ACCESS_TOKEN"
    purpose: "Instagram Graph API long-lived access token"
    required: true (only for auto_publish mode)

  - name: "INSTAGRAM_USER_ID"
    purpose: "Instagram Business Account ID for Graph API"
    required: true (only for auto_publish mode)

  - name: "SLACK_WEBHOOK_URL"
    purpose: "Slack notifications (optional)"
    required: false

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "FIRECRAWL_API_KEY=your_firecrawl_key_here  # Get from firecrawl.dev"
      - "ANTHROPIC_API_KEY=your_anthropic_key_here  # Claude API key"
      - "INSTAGRAM_ACCESS_TOKEN=your_ig_token_here  # Long-lived token (60 days)"
      - "INSTAGRAM_USER_ID=your_ig_user_id_here  # Business account ID"
      - "SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # Optional"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "anthropic>=0.28.0  # Claude API client"
      - "firecrawl-py>=0.0.16  # Firecrawl scraping"
      - "httpx>=0.27.0  # HTTP client with retry logic"
      - "beautifulsoup4>=4.12.0  # HTML parsing (fallback)"
      - "tenacity>=8.2.0  # Retry logic"
      - "jsonschema>=4.20.0  # JSON validation"
      - "python-dateutil>=2.8.2  # Date parsing"

GITHUB_ACTIONS:
  - trigger: "schedule (cron: 0 9 * * 1)"
    config: "Weekly Monday 09:00 UTC"
  - trigger: "workflow_dispatch"
    config: "Manual with inputs: brand_profile_path, weekly_theme, post_plan, reference_links, publishing_mode"
  - trigger: "issues (labeled: instagram-content-request)"
    config: "Agent HQ pattern - parse issue body for inputs"
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/validate_inputs.py').read())"
python -c "import ast; ast.parse(open('tools/setup_output.py').read())"
python -c "import ast; ast.parse(open('tools/fetch_reference_content.py').read())"
python -c "import ast; ast.parse(open('tools/generate_content_strategy.py').read())"
python -c "import ast; ast.parse(open('tools/generate_post_content.py').read())"
python -c "import ast; ast.parse(open('tools/review_content.py').read())"
python -c "import ast; ast.parse(open('tools/gate_decision.py').read())"
python -c "import ast; ast.parse(open('tools/publish_to_instagram.py').read())"
python -c "import ast; ast.parse(open('tools/generate_content_pack.py').read())"
python -c "import ast; ast.parse(open('tools/generate_upload_checklist.py').read())"
python -c "import ast; ast.parse(open('tools/update_latest_index.py').read())"
python -c "import ast; ast.parse(open('tools/archive_cleanup.py').read())"
python -c "import ast; ast.parse(open('tools/send_notification.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.validate_inputs')"
python -c "import importlib; importlib.import_module('tools.setup_output')"
# ... repeat for all tools

# Structure check — verify main() exists
python -c "from tools.validate_inputs import main; assert callable(main)"
python -c "from tools.setup_output import main; assert callable(main)"
# ... repeat for all tools

# Subagent file validation — verify YAML frontmatter
python -c "import yaml; yaml.safe_load(open('.claude/agents/content-strategist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/copywriter-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/hashtag-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/creative-director.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/reviewer-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/instagram-publisher.md').read().split('---')[1])"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test validate_inputs with sample data
echo '{"brand_name": "TestBrand", "tone": "friendly", "target_audience": "test", "products": ["test"], "banned_topics": [], "preferred_cta": ["test"]}' > /tmp/brand_profile.json
python tools/validate_inputs.py \
  --brand_profile_path /tmp/brand_profile.json \
  --weekly_theme "Test Theme" \
  --post_plan '{"reels": 2, "carousels": 1}' \
  --reference_links '[]' \
  --publishing_mode "content_pack_only"
# Expected: Valid JSON output with parsed inputs

# Test setup_output
python tools/setup_output.py --base_path /tmp/test_output
# Expected: Directories created, no errors

# Test fetch_reference_content with mock URL
python tools/fetch_reference_content.py \
  --reference_links '[{"url": "https://example.com", "purpose": "test"}]'
# Expected: JSON with success/failure per URL (might fail due to network, but should not crash)

# Test generate_content_strategy with sample inputs
python tools/generate_content_strategy.py \
  --brand_profile "$(cat /tmp/brand_profile.json)" \
  --weekly_theme "Test Theme" \
  --post_plan '{"reels": 2}' \
  --reference_content '{}'
# Expected: JSON with post_briefs array

# Test review_content with sample generated content
echo '{"posts": [{"post_id": 1, "caption": "Test", "hashtags": ["#test"]}]}' > /tmp/generated.json
python tools/review_content.py \
  --generated_content "$(cat /tmp/generated.json)" \
  --brand_profile "$(cat /tmp/brand_profile.json)" \
  --reference_content '{}'
# Expected: JSON with scores and pass/fail decision

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with sample data

# Step 1: Validate inputs
python tools/validate_inputs.py \
  --brand_profile_path config/brand_profile.json \
  --weekly_theme "Integration Test" \
  --post_plan '{"reels": 3, "carousels": 2}' \
  --reference_links '[]' \
  --publishing_mode "content_pack_only" > /tmp/validated.json

# Step 2: Setup output directory
python tools/setup_output.py --base_path /tmp/integration_test > /tmp/output_dir.json

# Step 3: Generate content strategy
python tools/generate_content_strategy.py \
  --brand_profile "$(jq -r '.brand_profile' /tmp/validated.json)" \
  --weekly_theme "$(jq -r '.weekly_theme' /tmp/validated.json)" \
  --post_plan "$(jq -c '.post_plan' /tmp/validated.json)" \
  --reference_content '{}' > /tmp/strategy.json

# Step 4: Generate post content (sequential mode for testing)
python tools/generate_post_content.py \
  --content_strategy "$(cat /tmp/strategy.json)" \
  --brand_profile "$(jq -r '.brand_profile' /tmp/validated.json)" \
  --use_agent_teams false > /tmp/generated.json

# Step 5: Review content
python tools/review_content.py \
  --generated_content "$(cat /tmp/generated.json)" \
  --brand_profile "$(jq -r '.brand_profile' /tmp/validated.json)" \
  --reference_content '{}' > /tmp/review.json

# Step 6: Gate decision
python tools/gate_decision.py \
  --review_report "$(cat /tmp/review.json)" \
  --publishing_mode "content_pack_only" > /tmp/decision.json

# Step 7: Generate content pack
python tools/generate_content_pack.py \
  --generated_content "$(cat /tmp/generated.json)" \
  --review_report "$(cat /tmp/review.json)" \
  --output_dir /tmp/integration_test

# Step 8: Verify outputs exist
test -f /tmp/integration_test/content_pack_*.md || echo "ERROR: Markdown content pack missing"
test -f /tmp/integration_test/content_pack_*.json || echo "ERROR: JSON content pack missing"

# Verify workflow.md references match actual tool files
grep -q "validate_inputs.py" workflow.md || echo "ERROR: validate_inputs.py not in workflow.md"
grep -q "generate_post_content.py" workflow.md || echo "ERROR: generate_post_content.py not in workflow.md"

# Verify CLAUDE.md documents all tools and subagents
grep -q "content-strategist" CLAUDE.md || echo "ERROR: content-strategist subagent not in CLAUDE.md"
grep -q "review_content.py" CLAUDE.md || echo "ERROR: review_content.py not in CLAUDE.md"

# Verify .github/workflows/ YAML is valid
python -c "import yaml; yaml.safe_load(open('.github/workflows/weekly-instagram.yml'))"

echo "Integration test complete. Check for any ERROR messages above."
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
- [ ] .gitignore excludes .env, __pycache__/, credentials, temp files
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files (.claude/agents/*.md) have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies with versions
- [ ] config/brand_profile.json example exists with all required fields
- [ ] All API rate limits documented in CLAUDE.md (Instagram: 200/hour, Firecrawl: varies by plan)
- [ ] Auto-publish gate decision is clearly documented (score >= 80/100 AND mode = auto_publish)

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only output files explicitly
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks (Firecrawl → HTTP+BeautifulSoup)
- Do not design subagents that call other subagents — only the main agent delegates
- Do not use Agent Teams when fewer than 3 independent tasks exist — sequential is sufficient
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not assume Instagram Graph API media URLs are accessible — must be public HTTPS
- Do not exceed Instagram rate limits (200 calls/hour) — implement rate limit detection and pausing
- Do not auto-publish without quality review passing — this is a critical safety gate
- Do not generate more than 12 hashtags per post — Instagram optimal is 8-12, not 30
- Do not exceed 2200 character caption limit — optimal is 125-150 for full visibility

---

## Confidence Score: 8/10

**Score rationale:**
- **Workflow pattern match**: High confidence. This is a textbook Generate > Review > Publish pattern with clear two-pass process and quality gates. The pattern is proven in similar systems (lead-gen-machine, marketing-pipeline, content-tone-repurposer). Confidence: **high**

- **Instagram Graph API integration**: Medium-high confidence. The API is well-documented, but has specific requirements (public HTTPS URLs for media, rate limits, auth token lifecycle). The PRP accounts for these, but first-time implementation may encounter edge cases. Fallback to manual content packs mitigates risk. Confidence: **medium-high**

- **Multi-dimensional quality review**: High confidence. The 5-dimension scoring (brand voice, compliance, hashtags, format, claims) is based on proven multi_dimension_scorer pattern from marketing-pipeline. Claude excels at brand voice analysis. The pattern is proven. Confidence: **high**

- **Agent Teams parallelization**: High confidence. Post generation is perfectly suited for Agent Teams (3-7 independent tasks, no data dependencies). The pattern is proven in content-tone-repurposer. Sequential fallback ensures the system works regardless. Confidence: **high**

- **Subagent architecture**: High confidence. 6 specialist subagents (strategist, copywriter, hashtag, creative-director, reviewer, publisher) with clear scopes. Follows the "one subagent per domain" rule. No cross-subagent calls. Proven pattern. Confidence: **high**

- **Brand voice matching**: Medium confidence. Brand voice alignment requires examples of on-brand vs off-brand content in the prompt. The PRP includes brand_profile with tone/style, but first run may require prompt tuning. The review step catches mismatches. Confidence: **medium**

- **Reference content extraction**: High confidence. Firecrawl + HTTP fallback pattern is proven (lead-gen-machine, marketing-pipeline). Graceful degradation handles missing references. Confidence: **high**

- **Compliance checks**: Medium confidence. Banned topics and prohibited claims scanning is straightforward keyword/phrase matching + Claude analysis. However, regulatory compliance (FTC guidelines) may require domain expertise. The PRP flags this but doesn't implement full legal review. Confidence: **medium**

**Ambiguity flags** (areas requiring clarification before building):
- [ ] **Instagram media handling**: The PRP assumes this system does NOT generate images/videos (it generates captions/hashtags/creative briefs only). Image prompts and creative briefs are guidance for manual content creation or briefing designers. Confirm this is correct. If images must be generated, add image generation tools (Replicate, DALL-E) and update workflow.

- [ ] **Instagram authentication flow**: The PRP requires a long-lived Instagram access token (60 days). Does the user already have this token, or does the system need to implement the OAuth flow to obtain it? If OAuth is required, add auth flow tools and documentation.

- [ ] **Scheduled posting**: The PRP mentions "scheduled posts" in the Instagram API section. Does the user want immediate publishing or scheduled future publishing? Scheduled publishing has additional API requirements (Business/Creator account, max 75 scheduled posts). Clarify and document in workflow.

**If any ambiguity flag is checked, ask the user to clarify before proceeding. Otherwise, confidence is 8/10 — ready to build.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/weekly-instagram-content-publisher.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
