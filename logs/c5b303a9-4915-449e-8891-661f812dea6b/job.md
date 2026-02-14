Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "weekly-instagram-content-publisher".

Problem description:
A weekly social media system that generates an Instagram-ready content pack (captions, hashtags, creative briefs, and optional image prompts) based on a brand voice and weekly theme, runs quality review checks, and then either publishes via the Instagram Graph API or prepares a "ready-to-post" pack for manual upload.

Inputs:
- brand_profile (JSON): Brand voice + guardrails (tone, do/don't list, target audience, products/services, banned topics, preferred CTA, emoji style)
- weekly_theme (string): The focus/topic for this week's posts (e.g., "spring launch", "behind the scenes", "customer stories")
- post_plan (JSON): Number and types of posts to create (e.g., 3 reels concepts + 2 carousels + 1 single image), plus any required series/templates
- reference_links (JSON array, optional): URLs to recent blog posts, announcements, or product pages to pull accurate details from
- publishing_mode (choice): "auto_publish" or "content_pack_only"

Desired Outputs:
- output/instagram/content_pack_{date}.md: A formatted weekly pack with post-by-post details (hook, caption, CTA, hashtags, alt text, posting time)
- output/instagram/content_pack_{date}.json: Structured data for each post
- output/instagram/review_report_{date}.md: Quality review results (brand-voice match, compliance checks, claims verification)
- If auto_publish: output/instagram/publish_log_{date}.json with IG media IDs or failure reasons
- If content_pack_only: output/instagram/upload_checklist_{date}.md for manual upload

Integrations: Firecrawl (reference content), Anthropic/OpenAI (generation), Instagram Graph API (publishing), Filesystem (storage)

Execution: Weekly cron (Monday 09:00 UTC), manual workflow_dispatch, Agent HQ issue-driven

Special Requirements:
- Two-pass process: Generate > Review > Publish
- Quality gates: brand voice alignment, prohibited claims check, banned topics scan, hashtag hygiene, IG format compliance
- Auto-publish gating with fallback to manual content packs
- Rolling archive with latest.md index
- Rate limiting and retry logic
- Suggested subagents: content-strategist, copywriter, hashtag-specialist, reviewer-specialist

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/weekly-instagram-content-publisher.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.