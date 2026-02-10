# Lead Gen Machine

An automated lead generation system that finds, scrapes, scores, and ranks companies matching an ideal customer profile, delivering qualified leads as a ranked CSV.

## System Overview

- **Type**: WAT System (Workflow, Agent, Tools)
- **Purpose**: Generate qualified B2B leads by searching the web, scraping company websites, extracting contact info, and scoring against target criteria
- **Pattern**: Intake > Enrich > Deliver (with Scrape > Process > Output elements)

## Execution

This system can be run three ways:

1. **Claude Code CLI**: Run `workflow.md` directly in the terminal
2. **GitHub Actions**: Trigger via Actions UI, API, or weekly cron schedule
3. **GitHub Agent HQ**: Assign an issue to @claude with the ideal customer profile in the body

## Inputs

- **ideal_customer_profile** (JSON): Object with the following fields:
  - `industry` (string, required): Target industry (e.g., "SaaS", "Healthcare")
  - `company_size` (string, required): Employee range (e.g., "50-200", "1000+")
  - `location` (string, required): Geographic target (e.g., "United States", "San Francisco, CA")
  - `keywords` (list[string], required): Descriptive keywords (e.g., ["AI", "enterprise", "cloud"])
  - `max_results` (int, optional): Max leads to return (default: 50)
  - `min_score` (float, optional): Minimum match score 0-100 (default: 40)

Example input:
```json
{
  "industry": "SaaS",
  "company_size": "50-200",
  "location": "United States",
  "keywords": ["AI", "machine learning", "enterprise"],
  "max_results": 50,
  "min_score": 40
}
```

## Outputs

- **output/leads_{timestamp}.csv** — Ranked CSV of qualified leads
- **output/latest_leads.csv** — Always-current file with the most recent results
- **output/run_summary.json** — Run metadata, profile used, and score statistics

## Workflow

Follow `workflow.md` for the step-by-step process. Key phases:

1. **Parse Input** — Validate the ideal customer profile
2. **Search** — Build and execute web search queries to find matching companies
3. **Scrape** — Visit company websites to extract raw content
4. **Extract** — Use Claude to pull structured contact info from scraped content
5. **Score** — Rate each lead 0-100 based on profile match
6. **Output** — Generate ranked CSV and commit results

## Tools

| Tool | Purpose |
|------|---------|
| `tools/search_companies.py` | Searches the web for companies matching the profile |
| `tools/scrape_websites.py` | Scrapes company websites for raw content |
| `tools/extract_contacts.py` | Extracts structured contact info using Claude |
| `tools/score_leads.py` | Scores and ranks leads against the profile |
| `tools/generate_csv.py` | Formats output as CSV and generates run summary |

## Subagents

This system uses specialist subagents defined in `.claude/agents/`. Subagents are the DEFAULT delegation mechanism — when the workflow reaches a phase, delegate to the appropriate subagent instead of running tools directly.

### Available Subagents

| Subagent | Description | Tools | When to Use |
|----------|-------------|-------|-------------|
| `search-specialist` | Web search for finding companies matching the ICP | Read, Bash, Grep | Step 2-3: Building queries and executing searches |
| `scrape-specialist` | Website content retrieval with rate limiting | Read, Bash | Step 4: Scraping company homepages and subpages |
| `extraction-specialist` | Structured data extraction from raw content | Read, Bash | Step 5: Extracting contact info using Claude API |
| `scoring-specialist` | Lead scoring, ranking, and output generation | Read, Write, Bash | Step 6-7: Scoring leads and generating CSV output |

### How to Delegate

Subagents are invoked automatically based on their `description` field, or explicitly:
```
Use the search-specialist subagent to find companies matching this profile
Use the scrape-specialist subagent to scrape the discovered company websites
Use the extraction-specialist subagent to extract contact info from the scraped content
Use the scoring-specialist subagent to score and rank the extracted leads
```

### Subagent Chaining

The lead generation pipeline chains subagents sequentially:

1. **search-specialist** produces `output/search_results.json` → feeds into
2. **scrape-specialist** produces `output/scraped_data.json` → feeds into
3. **extraction-specialist** produces `output/enriched_data.json` → feeds into
4. **scoring-specialist** produces `output/scored_leads.json` and final CSV

The main agent coordinates this chain, passing each subagent's output file path to the next.

### Delegation Hierarchy

- **Subagents are the default** for all task delegation in this system. Each workflow phase has a specialist.
- **Agent Teams is NOT used** by default — the pipeline is sequential (each step depends on the previous).
- **Parallelization opportunity**: If processing many companies, Steps 4-5 (scraping + extraction) can be parallelized per-company with Agent Teams. This requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.

## MCP Dependencies

This system uses the following MCPs. Alternatives are listed for flexibility.

| Capability | Primary MCP | Alternative | Fallback |
|-----------|-------------|-------------|----------|
| Web search | Brave Search MCP | Google Custom Search | Direct HTTP (limited) |
| Web scraping | Firecrawl MCP | Puppeteer MCP | requests + BeautifulSoup |
| Data extraction | Claude (built-in) | — | Regex-based extraction |
| File I/O | Filesystem MCP | — | Python pathlib/open |

**Important**: No MCP is hardcoded. If a listed MCP is unavailable, the system falls back to the alternative or direct API calls. Configure your preferred MCPs in your Claude Code settings.

## Required Secrets

These must be set as GitHub Secrets (for Actions) or environment variables (for CLI):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution and contact extraction | Yes |
| `BRAVE_API_KEY` | Brave Search API for company discovery | Yes (for best results) |
| `FIRECRAWL_API_KEY` | Firecrawl for high-quality web scraping | No (HTTP fallback available) |
| `GITHUB_TOKEN` | Committing results and issue management | Yes (auto-provided in Actions) |

### Local Environment Setup

For CLI execution, copy `.env.example` to `.env` and fill in your actual API keys:

```bash
cp .env.example .env
# Edit .env with your real values
```

**NEVER commit `.env` to version control.** The `.gitignore` already excludes it.

## Agent Teams

- This system does not use Agent Teams by default (steps are sequential)
- **Parallelization opportunity**: Steps 3-4 (scraping + extraction) can be parallelized per-company
- Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` to enable parallel scraping
- Without Agent Teams, the system processes companies one at a time (same results, slower)

## Agent HQ Usage

To run via GitHub Agent HQ:

1. Create an issue with the title: `Lead Gen: {industry} companies in {location}`
2. In the issue body, provide the ideal customer profile as JSON:
   ```json
   {
     "industry": "SaaS",
     "company_size": "50-200",
     "location": "United States",
     "keywords": ["AI", "machine learning", "enterprise"]
   }
   ```
3. Assign the issue to @claude
4. The agent will process the request and open a draft PR with the results CSV
5. Review the PR and leave comments with @claude for changes

## Scoring Logic

Leads are scored 0-100 based on four criteria:

| Criteria | Max Points | How It's Scored |
|----------|-----------|-----------------|
| Industry match | 30 | Exact match = 30, related = 15-20, no match = 0 |
| Company size | 25 | Within range = 25, adjacent = 12, no match = 0 |
| Location match | 20 | Exact = 20, same country = 10, no match = 0 |
| Keyword match | 25 | Proportional to keywords found in company data |

## Troubleshooting

- **No results found**: Broaden your keywords or location. Very niche searches may return few results.
- **Low scores across the board**: Your criteria may be too specific. Try lowering `min_score` to 30.
- **Scraping failures**: Some sites block automated access. The system will continue with available data and mark failures.
- **BRAVE_API_KEY not set**: The system needs Brave Search for company discovery. Set this secret for best results.
- **Tool fails with missing dependency**: Run `pip install -r requirements.txt`
- **MCP not available**: Check your Claude Code MCP configuration or use the HTTP fallback (automatic)
