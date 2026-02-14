Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "weekly-instagram-content-publisher".

Problem description:
A weekly social media system that generates an Instagram-ready content pack (captions, hashtags, creative briefs, and optional image prompts) based on a brand voice and weekly theme, runs quality review checks, and then either publishes via the Instagram Graph API or prepares a "ready-to-post" pack for manual upload.

**Inputs**:
- brand_profile (JSON): Brand voice + guardrails (tone, do/don't list, target audience, products/services, banned topics, preferred CTA, emoji style)
- weekly_theme (string): The focus/topic for this week's posts (e.g., "spring launch", "behind the scenes", "customer stories")
- post_plan (JSON): Number and types of posts to create (e.g., 3 reels concepts + 2 carousels + 1 single image), plus any required series/templates
- reference_links (JSON array, optional): URLs to recent blog posts, announcements, or product pages to pull accurate details from
- publishing_mode (choice): "auto_publish" or "content_pack_only"

**Desired Outputs**:
- output/instagram/content_pack_{date}.md: A formatted weekly pack with post-by-post hooks, captions, CTAs, hashtags, alt text, and suggested posting times, plus creative briefs for each post
- output/instagram/content_pack_{date}.json: Structured data for each post
- output/instagram/review_report_{date}.md: Quality review results (brand-voice match, compliance checks, claims verification notes, banned-topic scan)
- If publishing_mode="auto_publish": output/instagram/publish_log_{date}.json with posting results or failure reasons
- If publishing_mode="content_pack_only": output/instagram/upload_checklist_{date}.md with manual upload steps

**Integrations Needed**:
- Firecrawl: Fetch reference_links content for accuracy (fallback: direct HTTP with requests + BeautifulSoup)
- Anthropic (Claude): Generate captions/briefs + run review pass (fallback: OpenAI API if provided)
- Instagram (Meta Graph API): Publish posts when auto_publish is enabled (fallback: content_pack_only output with manual upload checklist)
- Filesystem: Store outputs and history in repo

**Execution Frequency**:
- Scheduled weekly cron (e.g., Monday 09:00 UTC)
- Manual trigger via workflow_dispatch to run on-demand with custom weekly_theme/post_plan
- Agent HQ: issue-driven requests

**Additional Requirements**:
- Pattern: Generate > Review > Publish
- Always run a two-pass process: 1) Generate draft content pack 2) Review + revise pass with explicit checks for brand voice alignment, prohibited claims, banned topics, hashtag hygiene, and Instagram format rules
- Auto-publish is optional and must be gated - only attempt if required secrets are present and publishing_mode="auto_publish"
- If publish fails, do NOT discard the content pack; write publish_log with errors and provide manual fallback outputs
- Maintain a rolling archive with content packs in output/instagram/ and generate lightweight index file output/instagram/latest.md
- Rate-limit external calls and include retry/backoff
- Subagents suggested: content-strategist-specialist, copywriter-specialist, hashtag-specialist, reviewer-specialist, publisher-specialist
- Secrets (referenced only, never hardcoded): ANTHROPIC_API_KEY, FIRECRAWL_API_KEY, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID, optional OPENAI_API_KEY as fallback

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/weekly-instagram-content-publisher.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.