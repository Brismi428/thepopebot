Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "rss-digest-monitor".

Problem description:
Monitor multiple RSS feeds and send daily email digest of new posts. Support multiple feeds, group posts by feed source, and include title, link, summary, and publish date in the digest. Use GitHub Actions for scheduling and SMTP for email delivery. Run daily at 8 AM UTC. Track new posts since last run using a local state file. HTML email format with nice formatting.

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/rss-digest-monitor.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.