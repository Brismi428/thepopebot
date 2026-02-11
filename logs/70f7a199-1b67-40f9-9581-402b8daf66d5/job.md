Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Execute the PRP at PRPs/rss-digest-monitor.md to build the complete WAT system.

Follow factory/workflow.md steps:
1. Load and validate the PRP (check confidence score >= 7)
2. Execute all factory steps: Design, Generate Workflow, Generate Tools, Generate Subagents, Generate GitHub Actions, Generate CLAUDE.md
3. Run 3-level validation (syntax, unit, integration)
4. Package the system into systems/rss-digest-monitor/
5. Update library/patterns.md and library/tool_catalog.md with new learnings

Report: files generated, validation results, and next steps for the user.