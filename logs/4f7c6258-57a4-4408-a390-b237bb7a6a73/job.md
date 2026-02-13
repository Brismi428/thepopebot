Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "website-uptime-checker".

Problem description:
Monitor two specific websites (https://google.com and https://github.com) every 5 minutes to check if they're up or down. When a site goes down, send a Telegram message alert to the user. Log all check results (timestamps, status codes, response times) to a file for historical tracking.

Inputs: Pre-configured URLs (google.com, github.com)
Outputs: Telegram notifications on downtime, log file with check results
Schedule: Every 5 minutes via cron job
Services needed: Telegram Bot API for notifications

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/website-uptime-checker.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.