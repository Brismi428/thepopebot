Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "invoice-generator".

Problem description:
Build an invoice generator system that takes JSON file input and generates professional PDF invoices. System takes client name, project description, line items with quantities and rates, payment terms, and due date. Generates a professional PDF invoice with company branding placeholders, itemized table, subtotal/tax/total calculation, and payment instructions. Saves invoices to output/ directory with filename format: {client-name}-{YYYY-MM-DD}-{invoice-number}.pdf. Uses sequential invoice numbering via counter file. Configurable tax rate and payment methods. Keep it simple - on-demand execution via command line.

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/invoice-generator.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.