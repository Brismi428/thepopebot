Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Execute the PRP at PRPs/website-uptime-checker.md to build the complete WAT system.

If the PRP doesn't exist, first create it with these requirements:
- Monitor https://google.com and https://github.com every 5 minutes
- Send Telegram alerts when sites go down
- Log all results with timestamps, status codes, response times
- Run via cron job every 5 minutes

Follow factory/workflow.md steps:
1. Load and validate the PRP (check confidence score >= 7)
2. Execute all factory steps: Design, Generate Workflow, Generate Tools, Generate Subagents, Generate GitHub Actions, Generate CLAUDE.md
3. Run 3-level validation (syntax, unit, integration)
4. Package the system into systems/website-uptime-checker/
5. Update library/patterns.md and library/tool_catalog.md with new learnings

Report: files generated, validation results, and next steps for the user.