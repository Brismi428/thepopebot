# Company Profiler

A WAT system that takes a company URL, scrapes the website, extracts key business information, and outputs a structured company profile as JSON.

## System Overview

- **Type**: WAT System (Workflow, Agent, Tools)
- **Purpose**: Generate structured company profiles from website URLs
- **Pattern**: Scrape → Process → Output (with optional Intake → Enrich → Deliver)

## Execution

This system can be run three ways:

1. **Claude Code CLI**: Run `workflow.md` directly — `claude "Read CLAUDE.md, then execute workflow.md with company_url=https://example.com"`
2. **GitHub Actions**: Trigger via Actions UI with URL input, or cron schedule for batch re-profiling
3. **GitHub Agent HQ**: Assign an issue with a company URL in the body to @claude

## Inputs

- **company_url** (str): URL of the company website to profile
- **tracked_companies** (str): Path to JSON file listing URLs for batch mode (used by cron)

## Outputs

- **output/company_profile.json**: Structured JSON with company data (single URL mode)
- **output/batch_profiles/{domain}.json**: Individual profiles (batch mode)

## Workflow

Follow `workflow.md` for the step-by-step process:

1. **Validate Input** — Parse URL or batch file
2. **Scrape Website** — Fetch homepage + key subpages using best available tool
3. **Extract Business Info** — Use Claude to extract structured data from scraped content
4. **Enrich Profile** — Optionally supplement with search results
5. **Output Results** — Write JSON, commit to repo

## Tools

| Tool | Purpose |
|------|---------|
| `tools/scrape_website.py` | Scrapes a URL and returns clean text content |
| `tools/extract_profile.py` | Processes scraped content into structured profile data |
| `tools/enrich_profile.py` | Searches additional sources to enrich the profile |
| `tools/output_profile.py` | Formats and writes the final JSON profile |

## MCP Dependencies

This system uses web scraping and search MCPs. It selects the best available tool automatically.

| Capability | Primary MCP | Alternative | Fallback |
|-----------|-------------|-------------|----------|
| Web scraping | Firecrawl | Puppeteer | `requests` + `beautifulsoup4` |
| Web search | Brave Search | — | Google Custom Search API |
| File operations | Filesystem MCP | — | Python `pathlib` |

**Important**: No MCP is hardcoded. If Firecrawl is unavailable, the system falls back to Puppeteer or direct HTTP requests. If Brave Search is unavailable, enrichment is skipped gracefully.

## Required Secrets

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl web scraping | No — falls back to HTTP |
| `BRAVE_SEARCH_API_KEY` | Brave Search for enrichment | No — enrichment is skipped |

## Agent Teams

This system does not use Agent Teams for single-URL mode. For batch mode with 5+ URLs, Agent Teams could parallelize scraping (each URL as a sub-agent task). This is optional — batch mode works sequentially by default.

## Agent HQ Usage

To run via GitHub Agent HQ:

1. Create an issue titled: `Profile: {company name}`
2. In the issue body:
   ```
   ## Task
   Profile the following company

   ## Input
   URL: https://example.com

   ## Expected Output
   Structured JSON company profile committed to output/
   ```
3. Assign the issue to @claude
4. The agent scrapes the site, extracts data, and opens a draft PR with the profile JSON

## Troubleshooting

- **Scraping returns empty content**: The site may block automated requests. Try Puppeteer MCP or add a user-agent header.
- **Missing fields in profile**: Some fields (pricing, team size) may not be publicly available. Check confidence scores.
- **Batch mode timeout**: GitHub Actions has a timeout. For large batches (50+ URLs), split into multiple runs.
- **Rate limiting**: The system adds a 2-second delay between URLs in batch mode. Increase if needed.
