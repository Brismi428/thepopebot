Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "instagram-publisher".

Problem description:
Automated Instagram content publishing system with IG Graph API integration and intelligent fallback handling for failed posts.

Inputs: Content (text/images), publishing schedule/triggers, post metadata
Outputs: Published Instagram posts, publishing status reports, error logs with fallback actions
Key components: publisher-specialist agent for Graph API operations, fallback handling for failed publications, secure secrets management
APIs/Services: Instagram Graph API (primary), Firecrawl API (optional), Anthropic Claude, OpenAI (fallback)

Required secrets (referenced only, never hardcoded):
- ANTHROPIC_API_KEY
- FIRECRAWL_API_KEY (if using Firecrawl)
- INSTAGRAM_ACCESS_TOKEN (Graph API)
- INSTAGRAM_BUSINESS_ACCOUNT_ID
- OPENAI_API_KEY (optional fallback)

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/instagram-publisher.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.