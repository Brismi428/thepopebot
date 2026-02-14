# Site Intelligence Pack

Automated website analysis system that produces comprehensive, evidence-backed business intelligence reports.

## What It Does

Crawls target websites, ranks pages by business relevance, extracts structured data from top pages, and synthesizes findings into a complete intelligence pack with full evidence provenance.

## Features

- ✅ Crawls up to 200 pages per domain with robots.txt compliance
- ✅ Ranks pages by business intelligence relevance
- ✅ Deep extracts structured data (offers, pricing, policies, testimonials, etc.)
- ✅ Evidence tracking: every claim mapped to source excerpts
- ✅ Parallel processing via Agent Teams (2-5x faster)
- ✅ Automatic de-duplication
- ✅ Fallback strategies (Firecrawl → HTTP crawl)
- ✅ Git-native output (versioned, auditable)

## Setup

### Prerequisites

- Python 3.12+
- GitHub repository access
- API keys: Firecrawl, Anthropic

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Secrets

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

### 3. Set GitHub Secrets (for Actions)

Add these secrets to your GitHub repository:

- `FIRECRAWL_API_KEY` -- Get from [firecrawl.dev](https://firecrawl.dev)
- `ANTHROPIC_API_KEY` -- Get from [console.anthropic.com](https://console.anthropic.com)
- `GITHUB_TOKEN` -- Auto-provided by GitHub Actions

## Usage

### Option 1: GitHub Actions (Recommended)

1. Go to **Actions** tab in your repository
2. Select **Site Intelligence Pack** workflow
3. Click **Run workflow**
4. Enter target domain (e.g., "stripe.com")
5. Optionally adjust max_pages and deep_extract_count
6. Results will be committed to `outputs/{domain}/{timestamp}/`

### Option 2: Local CLI

```bash
export FIRECRAWL_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export GITHUB_TOKEN=your_token_here

# Run workflow via Claude Code
claude --prompt "Read workflow.md and execute for domain: stripe.com"
```

### Option 3: Agent HQ (Issue-driven)

1. Open a GitHub Issue with title: "Site Intelligence Pack: stripe.com"
2. In the issue body, write: "Analyze stripe.com with max_pages=150"
3. Assign the issue to @claude
4. The agent will execute the workflow and deliver results as a PR

## Output Structure

All outputs are committed to `outputs/{domain}/{timestamp}/`:

```
outputs/
  stripe.com/
    2026-02-14T143000/
      inventory.json           # All discovered pages (200)
      ranked_pages.json        # Pages sorted by relevance
      deep_extract.json        # Structured data from top 15 pages
      site_intelligence_pack.json  # Final report with evidence
      README.md                # Human-readable summary
```

### Example Intelligence Pack Structure

```json
{
  "site": {
    "target_url": "https://stripe.com",
    "domain": "stripe.com",
    "crawled_at_iso": "2026-02-14T14:30:00Z",
    "robots": {...}
  },
  "synthesized_findings": {
    "positioning": {
      "claims": [
        {
          "id": "POS_001",
          "claim": "Targets online businesses and platforms",
          "evidence": ["EV_015", "EV_022"]
        }
      ]
    },
    "offers_and_pricing": {...},
    "customer_journey": {...},
    "trust_signals": {...},
    "compliance_and_policies": {...}
  },
  "evidence_index": {
    "EV_001": {
      "url": "https://stripe.com/pricing",
      "excerpt": "Pay-as-you-go pricing with no setup fees",
      "page_title": "Pricing",
      "extracted_at_iso": "2026-02-14T14:35:12Z"
    }
  }
}
```

## Cost Estimates

Per domain (average 200 pages, 15 deep extractions):
- **Firecrawl API**: $0.02-0.10
- **Claude API**: $0.50-1.50
- **Total**: ~$0.52-1.60 per domain

Execution time:
- **Sequential**: 5-8 minutes
- **With Agent Teams**: 3-5 minutes

## Architecture

### Subagents

1. **relevance-ranker-specialist** -- Ranks pages by business value
2. **deep-extract-specialist** -- Coordinates page extraction (can use Agent Teams)
3. **synthesis-validator-specialist** -- Synthesizes findings, validates output

### Agent Teams

Used for parallel deep extraction when processing 3+ pages:
- Sequential: 15 pages × 20s = ~5 minutes
- Parallel: 15 pages / 5 teammates = ~1 minute
- Same token cost, faster wall time

## Troubleshooting

### Issue: Firecrawl timeouts
**Fix:** Reduce `max_pages` or site has slow response times

### Issue: < 5 pages crawled
**Fix:** Check robots.txt (may block most paths), verify domain is accessible

### Issue: Deep extraction fails
**Fix:** Verify ANTHROPIC_API_KEY is set, check content isn't paywalled

### Issue: Git push fails
**Fix:** Verify GITHUB_TOKEN has repo write permissions

### Issue: Empty outputs
**Fix:** Check logs for API errors, verify secrets are configured

## Development

### Testing Individual Tools

```bash
# Test robots.txt fetch
python tools/fetch_robots.py --domain example.com

# Test crawl (requires API key)
python tools/firecrawl_crawl.py --domain example.com --max-pages 10

# Test inventory build
python tools/build_inventory.py --input raw_pages.json --output inventory.json

# Test ranking
python tools/rank_pages.py --input inventory.json --output ranked.json

# Test deep extraction
python tools/deep_extract_page.py --url "https://example.com/pricing" --content-file page.md
```

### Running Validation

```bash
# Validate schema
python tools/validate_schema.py --input site_intelligence_pack.json

# Generate README
python tools/generate_readme.py --input site_intelligence_pack.json --output README.md
```

## Security

- **Never commit .env files** -- Secrets are in GitHub Secrets only
- **Git discipline** -- Stage only `outputs/` directory (`git add outputs/`)
- **Rate limiting** -- Enforced at 1-2 req/sec to respect target servers
- **robots.txt** -- Always fetched and respected

## License

MIT

## Support

- Read `CLAUDE.md` for detailed operating instructions
- Read `workflow.md` for step-by-step process
- Check logs in workflow runs for debugging
- Open GitHub Issue for questions or bug reports
