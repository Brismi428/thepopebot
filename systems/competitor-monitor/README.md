# Competitor Monitor

Autonomous weekly competitor monitoring system that tracks changes to blog posts, pricing pages, and feature pages across multiple competitors. Generates digest reports and optional email notifications.

## What It Does

- **Crawls competitor websites** weekly (blog, pricing, features pages)
- **Detects changes** by comparing against last week's snapshot
- **Generates markdown reports** with all changes side-by-side
- **Commits everything to Git** (reports + historical snapshots)
- **Sends email digest** (optional) to your team

## Quick Start

### 1. Configure Competitors

Edit `config/competitors.json`:

```json
{
  "competitors": [
    {
      "name": "Competitor A",
      "slug": "competitor-a",
      "urls": {
        "blog": "https://competitora.com/blog",
        "pricing": "https://competitora.com/pricing",
        "features": "https://competitora.com/features"
      },
      "selectors": {
        "blog_items": "article.post",
        "price_value": ".price-amount",
        "feature_items": ".feature-card"
      }
    }
  ],
  "email": {
    "enabled": false,
    "recipients": ["team@example.com"]
  }
}
```

**Finding CSS selectors:**
1. Open competitor site in browser
2. Right-click element → Inspect
3. Note the CSS class or tag (e.g., `article.post`, `.pricing-card`)
4. Test: `document.querySelectorAll("article.post")`

**If selectors fail:** Leave them empty - system falls back to generic extraction.

### 2. Set Up Secrets

#### GitHub Actions (Production)

Go to **Settings → Secrets and variables → Actions → New repository secret**

**Required:**
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com

**Recommended:**
- `FIRECRAWL_API_KEY` - Get from https://firecrawl.dev (handles JS-heavy sites)

**Optional (only if email enabled):**
- `SMTP_HOST` (e.g., `smtp.gmail.com`)
- `SMTP_PORT` (usually `587`)
- `SMTP_USER`
- `SMTP_PASS`
- `EMAIL_FROM`

#### Local Testing

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the System

#### Option A: GitHub Actions (Automatic)

**Scheduled:** Runs every Monday at 8 AM UTC automatically.

**Manual trigger:**
1. Go to **Actions** tab
2. Select **Competitor Monitor** workflow
3. Click **Run workflow**
4. Check "Force run" if testing outside Monday

#### Option B: Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Run the workflow
claude -p workflow.md
```

Results will be created locally in `reports/` and `state/snapshots/`.

#### Option C: Agent HQ (Issue-Driven)

1. Create a GitHub issue
2. Assign to `@claude` or mention in comments
3. Issue body:
   ```
   Run the competitor monitor workflow and generate the weekly report.
   ```
4. Agent executes workflow and opens a draft PR with results

## How It Works

1. **Load config** - Read competitor list from `config/competitors.json`
2. **Crawl sites** - Scrape each competitor's blog, pricing, and features pages
3. **Compare snapshots** - Detect new blog posts, pricing changes, new features
4. **Generate report** - Create markdown digest in `reports/YYYY-MM-DD.md`
5. **Save snapshots** - Store current state in `state/snapshots/{slug}/`
6. **Send email** - (Optional) Email digest to team
7. **Commit to Git** - Push report and snapshots to repository

## What You Get

### Markdown Report (`reports/YYYY-MM-DD.md`)

```markdown
# Competitor Monitor Report - 2026-02-12

## Summary
- Competitors monitored: 3
- Total changes detected: 8
  - New blog posts: 5
  - Pricing changes: 2
  - New features: 1

## Competitor A

### 📝 New Blog Posts (2)
**Announcing Product 2.0**
- URL: https://competitora.com/blog/product-2.0
- Published: 2026-02-10
- Summary: We're excited to announce...

### 💰 Pricing Changes (1)
**Enterprise Plan**
- Old Price: $499/mo
- New Price: $599/mo
- Change: +$100 (+20%)
```

### Historical Snapshots (`state/snapshots/{slug}/`)

```
state/snapshots/
├── competitor-a/
│   ├── 2026-01-29.json
│   ├── 2026-02-05.json
│   ├── 2026-02-12.json
│   └── latest.json (copy of 2026-02-12.json)
└── competitor-b/
    └── ...
```

Each snapshot contains:
- Blog posts (title, URL, published date, excerpt)
- Pricing plans (name, price, features)
- Feature items (title, description, URL)

## Configuration Reference

### Competitor Object

```json
{
  "name": "Display Name",
  "slug": "lowercase-with-hyphens",
  "urls": {
    "blog": "https://...",
    "pricing": "https://...",
    "features": "https://..."
  },
  "selectors": {
    "blog_items": "CSS selector",
    "price_value": "CSS selector",
    "feature_items": "CSS selector"
  }
}
```

**Notes:**
- `slug` is used for file paths - must be unique
- `urls` can have any page types (not just blog/pricing/features)
- `selectors` are optional - tool falls back to generic extraction

### Email Configuration

```json
{
  "email": {
    "enabled": true,
    "recipients": ["person1@example.com", "person2@example.com"]
  }
}
```

Set to `"enabled": false` to disable email delivery.

## Architecture

This is a **WAT (Workflows, Agents, Tools)** system:

### Workflows
- `workflow.md` - Main process definition (7 steps from config load to Git commit)

### Agents (Subagents)
- `crawl-specialist` - Web scraping with fallback strategies
- `change-detector-specialist` - Snapshot comparison and diff logic
- `report-generator-specialist` - Markdown report generation
- `snapshot-manager-specialist` - State persistence and pruning

### Tools (Python)
- `crawl_competitor.py` - Scrape website pages
- `detect_changes.py` - Compare snapshots
- `generate_digest.py` - Generate markdown report
- `save_snapshot.py` - Save snapshots with atomic writes
- `send_email.py` - Send email via SMTP

### Agent Teams (Optional)
For 3+ competitors, the system uses parallel crawling via Agent Teams:
- **Sequential:** 5 competitors × 15s = 75 seconds
- **Parallel:** Max ~20 seconds (3-4x speedup)

## Troubleshooting

### "All crawling methods failed"
**Cause:** Site is down or blocking scrapers  
**Fix:**
- Verify site is reachable: `curl -I https://competitor.com`
- Check if Firecrawl API key is set (fallback is HTTP-only)
- Try manual crawl: `python tools/crawl_competitor.py --config config/competitors.json`

### "No changes detected every week"
**Cause:** Selectors broken (site redesign) or competitors are inactive  
**Fix:**
- Check crawl output: `cat state/snapshots/competitor-a/latest.json`
- Update selectors to match current site structure
- Verify pages actually have new content

### "Snapshot too large (>10MB)"
**Cause:** Competitor site has massive content  
**Fix:**
- Remove page types (e.g., drop `blog` or `features`)
- Make selectors more specific (fewer items)
- Adjust compression logic in `save_snapshot.py`

### "Email send fails"
**Cause:** SMTP credentials incorrect  
**Fix:**
- Test manually: `python tools/send_email.py --subject "Test" --body-text "Test" --recipients "you@example.com"`
- Verify all SMTP secrets are set
- Check if provider requires app-specific password

## Performance & Cost

### Execution Time
- **1-2 competitors (sequential):** ~30-45 seconds
- **3+ competitors (parallel):** ~30-60 seconds

### GitHub Actions Minutes
- **Per run:** ~5 minutes
- **Weekly:** 5 min/week × 4 weeks = ~20 minutes/month
- **Well within free tier:** 2,000 minutes/month (private repos)

### API Costs (3 competitors)
- **Firecrawl:** ~$0.03-0.06 per run (3 pages × 3 competitors)
- **Claude:** ~$0.05-0.15 per run
- **Total:** ~$0.08-0.21 per run
- **Monthly:** ~$0.32-0.84 (4 runs)

## Maintenance

### Weekly
- Review generated reports for accuracy
- Check GitHub Actions logs for crawl failures

### Monthly
- Verify CSS selectors still work (sites change)
- Check snapshot size: `du -sh state/snapshots/`

### Quarterly
- Update competitor list as needed
- Update Python dependencies: `pip install --upgrade -r requirements.txt`

### Annually
- Prune old reports: `rm reports/2025-*.md` (Git keeps history)
- Review API costs and optimize if needed

## Files & Directories

```
competitor-monitor/
├── .github/workflows/
│   └── monitor.yml          # GitHub Actions workflow
├── .claude/agents/
│   ├── crawl-specialist.md
│   ├── change-detector-specialist.md
│   ├── report-generator-specialist.md
│   └── snapshot-manager-specialist.md
├── config/
│   └── competitors.json     # Competitor configuration
├── tools/
│   ├── crawl_competitor.py
│   ├── detect_changes.py
│   ├── generate_digest.py
│   ├── save_snapshot.py
│   └── send_email.py
├── reports/                 # Generated weekly reports
├── state/snapshots/         # Historical snapshots (Git-tracked)
├── CLAUDE.md                # Operating instructions for AI
├── workflow.md              # Main process workflow
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
└── README.md                # This file
```

## Security

- **Secrets never hardcoded** - All credentials via GitHub Secrets or `.env`
- **Secrets filtered from logs** - GitHub Actions redacts secrets
- **Atomic commits** - Prevents partial state corruption
- **Rate limit protection** - 2-second delay between API requests

## License

[Add your license here]

## Support

- **Issues:** Open a GitHub issue
- **Logs:** Check GitHub Actions workflow runs
- **Debugging:** Run locally with `claude -p workflow.md`

---

**Built with [WAT Systems Factory](https://github.com/stephengpope/thepopebot)** - Autonomous AI-powered systems for GitHub
