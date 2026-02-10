Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "website-uptime-monitor".

Problem description:
Build a simple system that monitors a single website's uptime status. The system should check one configurable URL every 5 minutes, log the status code and response time to a local CSV file. No notifications needed - just logging for monitoring purposes.

Requirements:
- Monitor: Single URL (configurable)
- Frequency: Every 5 minutes
- Logging: Status code, response time, timestamp, up/down status
- Output: Local CSV log file
- Schedule: GitHub Actions cron job
- Keep it simple - no alerts or complex features

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/website-uptime-monitor.md
5. Log the confidence score and any ambiguity flags

After generating the PRP, report what was created.