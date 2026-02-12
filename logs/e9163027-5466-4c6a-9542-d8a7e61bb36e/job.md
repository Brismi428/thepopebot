Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "competitor-monitor".

Problem description:
Build a competitor monitoring system that takes a list of competitor URLs, crawls their sites weekly, detects content changes (new blog posts, pricing changes, new features), and generates a weekly digest report comparing what changed across all competitors. The system should be configurable for any URLs via a JSON config file, track blog posts/pricing/feature pages, run weekly crawls only, save reports as markdown files locally with optional email via SMTP, store historical snapshots for comparison, and auto-detect new pages without limiting to known URLs only.

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/competitor-monitor.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.