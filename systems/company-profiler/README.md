# company-profiler

A WAT system that takes a company URL, scrapes the website, extracts key business information (what they do, team size signals, tech stack, pricing model, target market), and outputs a structured company profile as JSON.

## Quick Start

### Option A: Claude Code CLI (Local)

```bash
# Clone the repo
git clone <repo-url>
cd company-profiler

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here
export FIRECRAWL_API_KEY=your_key_here      # Optional — improves scraping quality
export BRAVE_SEARCH_API_KEY=your_key_here    # Optional — enables enrichment

# Install dependencies
pip install -r requirements.txt

# Profile a company
claude "Read CLAUDE.md for context, then execute workflow.md with company_url=https://anthropic.com"
```

### Option B: GitHub Actions (Automated)

1. Push this repo to GitHub
2. Go to **Settings > Secrets and variables > Actions**
3. Add the required secrets (see table below)
4. Go to **Actions > company-profiler** and click **Run workflow**
5. Enter the company URL and trigger

To trigger via API (e.g., from n8n or a script):
```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{"event_type": "company-profiler-run", "client_payload": {"company_url": "https://anthropic.com"}}'
```

### Option C: GitHub Agent HQ (Issue-Driven)

1. Create an issue titled: `Profile: Anthropic`
2. In the issue body:
   ```
   ## Task
   Profile the following company

   ## Input
   URL: https://anthropic.com

   ## Expected Output
   Structured JSON company profile committed to output/
   ```
3. Assign the issue to `@claude`
4. The agent scrapes the site, extracts data, and opens a draft PR with the profile

### Batch Mode (Cron)

The system automatically re-profiles all companies in `data/tracked_companies.json` every Monday at 9 AM UTC. Add companies to the list:

```json
{
  "companies": [
    {"url": "https://anthropic.com", "name": "Anthropic", "added": "2025-01-01"},
    {"url": "https://stripe.com", "name": "Stripe", "added": "2025-01-15"}
  ]
}
```

## Required Secrets

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl web scraping (better quality) | No — falls back to HTTP |
| `BRAVE_SEARCH_API_KEY` | Brave Search for profile enrichment | No — enrichment skipped |

## Output Format

Profiles are saved as JSON:

```json
{
  "url": "https://anthropic.com",
  "scraped_at": "2025-01-15T10:30:00Z",
  "company_name": "Anthropic",
  "description": "AI safety company building reliable AI systems",
  "industry": "Artificial Intelligence",
  "products_services": ["Claude", "Claude API", "Claude for Enterprise"],
  "target_market": "B2B, Enterprise, Developers",
  "pricing_model": "Usage-based API pricing, Enterprise plans",
  "team_size_signals": "500+ employees based on job postings and LinkedIn",
  "tech_stack": ["Python", "Rust", "Kubernetes", "JAX"],
  "founded": "2021",
  "location": "San Francisco, CA",
  "social_links": {"twitter": "...", "linkedin": "..."},
  "confidence": {"company_name": "high", "description": "high", ...},
  "enrichment_sources": ["https://..."]
}
```

## System Structure

```
company-profiler/
├── CLAUDE.md                       # Operating instructions
├── workflow.md                     # Step-by-step process
├── tools/
│   ├── scrape_website.py           # Scrapes company website
│   ├── extract_profile.py          # Extracts structured data via Claude
│   ├── enrich_profile.py           # Enriches with search data
│   └── output_profile.py           # Formats and writes output
├── .github/workflows/
│   ├── company-profiler.yml        # Main workflow (dispatch + cron)
│   └── agent_hq.yml               # Agent HQ (issue-driven)
├── data/
│   └── tracked_companies.json      # Companies for weekly batch re-profiling
├── output/                         # Results go here
├── requirements.txt
└── README.md
```

---
*Built by [WAT Systems Factory](https://github.com/your-org/wat-systems-factory)*
