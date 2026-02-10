Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "competitor-pricing-monitor".

Problem description:
- Monitor 3 competitor SaaS pricing pages for pricing changes
- Track current price, plan names, and any discounts
- Send Slack summary to #pricing-alerts channel showing only changes since yesterday
- Check prices twice daily - morning (8 AM) and evening (6 PM)
- No login required for competitor sites (public SaaS pricing pages)
- Store historical pricing data to detect changes
- Include error handling for site changes or downtime

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/competitor-pricing-monitor.md
5. Log the confidence score and any ambiguity flags

After generating the PRP, report what was created.