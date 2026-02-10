# Lead Gen Machine

An automated lead generation system built on the WAT framework (Workflows, Agents, Tools). Takes an ideal customer profile as input, searches the web for matching companies, scrapes their websites for contact info, scores each lead, and outputs a ranked CSV of qualified leads.

## How It Works

1. You provide an **ideal customer profile** (industry, company size, location, keywords)
2. The system **searches the web** for matching companies via Brave Search
3. It **scrapes company websites** for business details and contact information
4. **Claude extracts** structured data (emails, phones, descriptions) from scraped content
5. Each lead is **scored 0-100** based on how well it matches your criteria
6. Results are output as a **ranked CSV** committed back to the repo

## Quick Start

### Option A: Claude Code CLI

```bash
# 1. Clone the repo
git clone <repo-url> && cd lead-gen-machine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your actual API keys

# 4. Run with Claude Code
claude "Read CLAUDE.md, then execute workflow.md with input: {\"industry\": \"SaaS\", \"company_size\": \"50-200\", \"location\": \"United States\", \"keywords\": [\"AI\", \"machine learning\"]}"
```

### Option B: GitHub Actions (Manual Dispatch)

1. Push this repo to GitHub
2. Go to **Settings > Secrets and variables > Actions** and add:
   - `ANTHROPIC_API_KEY` (required)
   - `BRAVE_API_KEY` (required for best results)
   - `FIRECRAWL_API_KEY` (optional, improves scraping quality)
3. Go to **Actions > lead-gen-machine — WAT System**
4. Click **Run workflow** and paste your ideal customer profile JSON:
   ```json
   {"industry": "SaaS", "company_size": "50-200", "location": "United States", "keywords": ["AI", "machine learning"]}
   ```
5. Results will be committed to `output/` when complete

### Option C: GitHub Agent HQ

1. Push this repo to GitHub and configure secrets (same as Option B)
2. Create a new **Issue** with title: `Lead Gen: SaaS companies in United States`
3. In the issue body, paste the ideal customer profile as JSON
4. **Assign the issue** to `@claude`
5. The agent will:
   - Post an acknowledgment comment with progress checkboxes
   - Execute the full workflow
   - Open a **draft PR** with the results
6. Review the PR; comment with `@claude` for refinements

### Scheduled Runs

The system includes a weekly cron trigger (Mondays at 06:00 UTC). To use it:

1. Create `config/default_profile.json` with your default ideal customer profile
2. The system will automatically run weekly and commit new results

## Input Format

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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `industry` | string | Yes | Target industry |
| `company_size` | string | Yes | Employee count range |
| `location` | string | Yes | Geographic target |
| `keywords` | list[string] | Yes | Descriptive keywords |
| `max_results` | int | No | Max leads (default: 50) |
| `min_score` | float | No | Min score threshold 0-100 (default: 40) |

## Output

Results are written to `output/`:

- **`leads_{timestamp}.csv`** — Timestamped CSV with ranked leads
- **`latest_leads.csv`** — Always-current file with the most recent results
- **`run_summary.json`** — Execution metadata and statistics

### CSV Columns

| Column | Description |
|--------|-------------|
| `rank` | Position in ranked list (1 = best match) |
| `company_name` | Company name |
| `website` | Company website URL |
| `industry` | Detected industry |
| `company_size` | Estimated employee count |
| `location` | Company location |
| `match_score` | Match score 0-100 |
| `email` | Contact email (if found) |
| `phone` | Phone number (if found) |
| `description` | Company description |
| `scraped_at` | Timestamp of data collection |

## Required Secrets

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution and data extraction | Yes |
| `BRAVE_API_KEY` | Brave Search API for company discovery | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl for high-quality web scraping | No |
| `GITHUB_TOKEN` | Repo commits and issue management | Auto-provided |

## Scoring

Each lead is scored 0-100 across four dimensions:

| Criteria | Max Points | Description |
|----------|-----------|-------------|
| Industry match | 30 | How closely the company's industry matches the target |
| Company size | 25 | Whether employee count falls within the target range |
| Location | 20 | Geographic proximity to the target location |
| Keywords | 25 | How many target keywords appear in the company's data |

## Tools

| Tool | What It Does |
|------|-------------|
| `tools/search_companies.py` | Executes web searches and aggregates company results |
| `tools/scrape_websites.py` | Scrapes company websites with Firecrawl/HTTP fallback |
| `tools/extract_contacts.py` | Uses Claude to extract structured contact data |
| `tools/score_leads.py` | Computes match scores and ranks leads |
| `tools/generate_csv.py` | Formats output CSV and generates run summary |

## Privacy & Ethics

- This system only collects **publicly available business information** from company websites
- It does **not** scrape personal social media profiles or use data brokers
- Rate limiting is built in to respect website load (1-2 second delays between requests)
- The User-Agent header identifies the bot as a research tool
