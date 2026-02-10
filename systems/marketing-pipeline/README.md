# Marketing Pipeline

A WAT system that transforms raw lead lists into a segmented, enriched, actionable marketing pipeline with personalized outreach content.

## What It Does

1. **Ingests** a CSV of company leads
2. **Enriches** each lead with company data, tech stack, decision-maker contacts, and pain signals (via Apollo.io, Hunter.io, Brave Search, Claude)
3. **Deep-scores** each lead 0-100 across 5 dimensions: size fit, tech stack compatibility, budget signals, decision maker accessibility, pain signal detection
4. **Segments** into tiers: Hot (80+), Warm (50-79), Cold (<50)
5. **Generates outreach**: Personalized 3-email cold sequences for Hot leads
6. **Generates nurture**: 5-email educational drip for Warm leads
7. **Outputs**: Enriched CSVs, email sequences, and a pipeline summary

## Setup

### Required Secrets

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code, email generation, pain analysis | Yes |
| `APOLLO_API_KEY` | Company enrichment and contact discovery | No (fallback available) |
| `HUNTER_API_KEY` | Email verification and discovery | No (fallback available) |
| `BRAVE_API_KEY` | Company research via web search | No (reduced quality) |

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd marketing-pipeline

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Path A: Claude Code CLI

Run directly from the terminal:

```bash
# With a specific CSV
claude "Read CLAUDE.md, then execute workflow.md with input: input/leads.csv"

# Or place a CSV in input/ and run without specifying
claude "Read CLAUDE.md, then execute workflow.md"
```

### Path B: GitHub Actions

1. Push the repo to GitHub
2. Add required secrets in Settings > Secrets > Actions
3. Trigger manually:
   - Go to Actions > "marketing-pipeline -- WAT System" > Run workflow
   - Enter the path to your CSV (e.g., `input/leads.csv`)
4. Or let it run on schedule (weekly, Mondays 09:00 UTC)
5. Or trigger via API:
   ```bash
   curl -X POST \
     -H "Authorization: token YOUR_PAT" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/OWNER/REPO/dispatches \
     -d '{"event_type":"marketing-pipeline-run","client_payload":{"task_input":"input/leads.csv"}}'
   ```

### Path C: GitHub Agent HQ

1. Create an issue with title: `Pipeline: Process Q1 leads`
2. In the issue body, provide:
   ```
   input/leads.csv
   ```
   Or paste CSV content directly.
3. Assign the issue to @claude
4. The agent processes the leads and opens a draft PR with results
5. Review the PR. Comment with @claude for changes.

## Input Format

CSV with at minimum a `company_name` column:

```csv
company_name,website,industry,location,company_size
Acme Corp,https://acme.com,SaaS,San Francisco CA,50-200
WidgetCo,https://widgetco.io,Fintech,New York NY,200-500
DataFlow Inc,https://dataflow.dev,AI,Austin TX,20-50
```

Optional columns that improve enrichment accuracy: `website`, `industry`, `location`, `company_size`, `notes`.

## Output Files

| File | Description |
|------|-------------|
| `output/enriched_leads_{timestamp}.csv` | All leads with full enrichment data |
| `output/hot_leads.csv` | Hot tier leads (score 80+) |
| `output/warm_leads.csv` | Warm tier leads (score 50-79) |
| `output/outreach/emails_{company}.md` | 3-email outreach sequence per hot lead |
| `output/nurture/sequence.md` | 5-email nurture drip for warm leads |
| `output/pipeline_summary.json` | Run stats, scores, segment breakdown |

## Scoring Dimensions

| Dimension | Max Points | What It Measures |
|-----------|-----------|------------------|
| Company Size Fit | 20 | Target range match |
| Tech Stack Compatibility | 25 | Automation tool usage (n8n, Zapier, Make, etc) |
| Budget Signals | 20 | Ops hiring, funding, growth indicators |
| Decision Maker Accessibility | 15 | Emails, LinkedIn, multiple contacts |
| Pain Signal Detection | 20 | Manual process pain, automation-seeking signals |

## Project Structure

```
marketing-pipeline/
├── CLAUDE.md              # Operating instructions for Claude Code
├── workflow.md            # Step-by-step pipeline process
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Excludes .env, caches, credentials
├── input/                 # Place input CSVs here
├── output/                # Pipeline outputs
│   ├── outreach/          # Per-company outreach email sequences
│   └── nurture/           # Nurture drip sequence
├── tools/                 # Python tool implementations
│   ├── ingest_leads.py    # CSV ingestion and validation
│   ├── enrich_leads.py    # Multi-API enrichment
│   ├── score_leads.py     # 5-dimension scoring
│   ├── segment_leads.py   # Hot/Warm/Cold segmentation
│   ├── generate_outreach.py  # Cold email sequence generation
│   ├── generate_nurture.py   # Nurture drip generation
│   └── output_pipeline.py    # CSV and summary generation
├── .claude/agents/        # Specialist subagent definitions
│   ├── enrichment-specialist.md
│   ├── scoring-specialist.md
│   ├── outreach-specialist.md
│   ├── nurture-specialist.md
│   └── pipeline-reviewer.md
└── .github/workflows/     # GitHub Actions
    ├── main.yml           # Manual/cron/API trigger
    └── agent_hq.yml       # Issue/PR-driven execution
```

## API Fallback Chain

The system degrades gracefully when APIs are unavailable:

1. **Apollo.io** (primary enrichment) -> falls back to Brave Search + Claude
2. **Hunter.io** (email verification) -> falls back to Apollo contacts only
3. **Brave Search** (company research) -> reduced research quality, enrichment still works
4. **Claude** (email generation, pain analysis) -> required, no fallback

The only hard requirement is `ANTHROPIC_API_KEY`. All other APIs enhance quality but are optional.
