Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "content-repurposer".

Problem description:
Build a multi-channel content repurposing system that takes a blog post URL, extracts the content, and generates a Twitter thread, LinkedIn post, email newsletter section, and Instagram caption — each optimized for the platform's format and character limits. Include tone analysis of the source content and style matching per platform. Generate content only (no auto-posting). Analyze and match the source blog's tone automatically. Suggest hashtags and mentions per platform. Save all outputs to a single JSON file with one key per platform.

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/content-repurposer.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.