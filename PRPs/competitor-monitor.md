name: "competitor-monitor"
description: |
  Weekly competitor monitoring system that crawls competitor websites, detects content changes across blog posts, pricing pages, and feature pages, and generates a comparative weekly digest report with optional email delivery.

## Purpose
WAT System PRP (Product Requirements Prompt) — a structured blueprint that gives the factory enough context to build a complete, working system in one pass.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build an autonomous competitor monitoring system that tracks multiple competitors' websites weekly, detecting changes to blog posts, pricing pages, and feature announcements. The system crawls configured URLs, compares snapshots against historical data, identifies meaningful changes (new content, price updates, feature additions), and generates a unified weekly digest report as a markdown file. Reports are committed to the repository with optional email delivery via SMTP.

## Why
- **Business value**: Competitive intelligence without manual weekly checks of competitor sites
- **Automation**: Eliminates 2-4 hours/week of manual competitor research across marketing and product teams
- **Detection**: Catches new blog posts, pricing changes, and feature launches within 7 days instead of months
- **Historical tracking**: Git-native snapshot storage provides version-controlled audit trail of all competitor activity

## What
A scheduled GitHub Actions workflow that runs every Monday at 8 AM UTC, reads a JSON config file listing competitor URLs, crawls each site to extract blog/pricing/feature content, compares against last week's snapshot, detects changes, generates a markdown digest showing what changed across all competitors, commits the report to `reports/YYYY-MM-DD.md`, and optionally emails the report to a distribution list.

### Success Criteria
- [ ] Crawls 3+ competitor websites weekly without manual intervention
- [ ] Detects new blog posts (identifies posts not in previous snapshot)
- [ ] Detects pricing changes (compares price values or pricing page structure)
- [ ] Detects new feature pages (identifies pages not previously seen)
- [ ] Generates markdown report comparing all competitors side-by-side
- [ ] Stores historical snapshots in Git for version control
- [ ] System runs autonomously via GitHub Actions on schedule (weekly)
- [ ] Results are committed back to repo in `reports/` directory
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ
- [ ] No hardcoded competitor URLs (all configured via JSON file)
- [ ] Handles site unavailability gracefully (skip that competitor, continue with others)

---

## Inputs

```yaml
- name: "config/competitors.json"
  type: "JSON file"
  source: "Repository file committed to Git"
  required: true
  description: "Configuration file listing competitor URLs and page types to monitor"
  example: |
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
            "blog_posts": "article.post",
            "price_value": ".price-amount",
            "feature_items": ".feature-card"
          }
        },
        {
          "name": "Competitor B",
          "slug": "competitor-b",
          "urls": {
            "blog": "https://competitorb.com/blog",
            "pricing": "https://competitorb.com/plans",
            "features": "https://competitorb.com/product"
          },
          "selectors": {
            "blog_posts": ".blog-entry",
            "price_value": "span.amount",
            "feature_items": "div.feature"
          }
        }
      ],
      "email": {
        "enabled": false,
        "recipients": ["team@example.com"]
      }
    }

- name: "force_run"
  type: "boolean"
  source: "GitHub Actions workflow_dispatch input (optional)"
  required: false
  description: "Force a crawl even if it's not Monday at 8 AM UTC"
  example: "true"
```

## Outputs

```yaml
- name: "reports/YYYY-MM-DD.md"
  type: "Markdown file"
  destination: "Repository commit to main branch"
  description: "Weekly digest report showing all detected changes across competitors"
  example: |
    # Competitor Monitor Report - 2026-02-10
    
    ## Summary
    - 3 competitors monitored
    - 5 new blog posts detected
    - 1 pricing change detected
    - 2 new feature pages detected
    
    ## Competitor A
    ### New Blog Posts (3)
    - **Title**: Announcing Product Launch
      - URL: https://competitora.com/blog/product-launch
      - Published: 2026-02-08
      - Summary: First 200 words of post...
    
    ### Pricing Changes (1)
    - **Plan**: Enterprise
      - Old Price: $499/mo
      - New Price: $599/mo
      - Change: +$100/mo (+20%)
    
    ## Competitor B
    ### New Blog Posts (2)
    ...

- name: "state/snapshots/{competitor_slug}/YYYY-MM-DD.json"
  type: "JSON file"
  destination: "Repository commit to main branch"
  description: "Historical snapshot of crawled content for each competitor"
  example: |
    {
      "competitor": "competitor-a",
      "timestamp": "2026-02-10T08:00:00Z",
      "pages": {
        "blog": {
          "url": "https://competitora.com/blog",
          "posts": [
            {
              "title": "Announcing Product Launch",
              "url": "https://competitora.com/blog/product-launch",
              "published": "2026-02-08",
              "excerpt": "First 200 words..."
            }
          ]
        },
        "pricing": {
          "url": "https://competitora.com/pricing",
          "plans": [
            {"name": "Enterprise", "price": "$599/mo"}
          ]
        },
        "features": {
          "url": "https://competitora.com/features",
          "features": ["Feature 1", "Feature 2"]
        }
      }
    }

- name: "Email digest (optional)"
  type: "HTML + plain text email"
  destination: "SMTP to configured recipients"
  description: "Weekly digest email with same content as markdown report"
  example: "HTML-formatted email with markdown report content"
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://docs.firecrawl.dev/api-reference/scrape"
  why: "Primary web scraping method - understand scrape vs crawl modes, selector usage, markdown output format"

- url: "https://playwright.dev/python/docs/api/class-page"
  why: "Fallback for JS-heavy sites - page navigation, selectors, content extraction"

- url: "https://docs.python.org/3/library/difflib.html"
  why: "Content diffing for change detection - SequenceMatcher for text comparison"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide web scraping capabilities (Firecrawl, Puppeteer, Fetch)"

- doc: "library/patterns.md"
  why: "This system combines Monitor > Detect > Alert + Scrape > Process > Output + Collect > Transform > Store"

- doc: "library/tool_catalog.md"
  why: "Reuse firecrawl_scrape, filter_sort, json_read_write patterns"
```

### Workflow Pattern Selection
```yaml
pattern: "Monitor > Detect > Alert + Scrape > Process > Output + Collect > Transform > Store"
rationale: |
  This system combines multiple patterns:
  - **Monitor > Detect > Alert**: Weekly scheduled check for changes with digest generation
  - **Scrape > Process > Output**: Web scraping with content extraction and structured output
  - **Collect > Transform > Store**: Historical snapshot storage with Git versioning
  
  The system follows Monitor's state-comparison logic, Scrape's multi-source extraction, and Store's versioned data pattern.

modifications: |
  - State stored in Git rather than external database
  - Alert mechanism is digest generation + optional email, not real-time alerts
  - Scraping phase can be parallelized via Agent Teams if 3+ competitors configured
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "Web scraping with JS rendering"
    primary_mcp: "firecrawl"
    alternative_mcp: "puppeteer"
    fallback: "HTTP + BeautifulSoup (no JS support)"
    secret_name: "FIRECRAWL_API_KEY"

  - name: "Email delivery"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "SMTP via smtplib (stdlib)"
    secret_name: "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM"

  - name: "Content extraction and parsing"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "BeautifulSoup4 + lxml"
    secret_name: "none"

  - name: "Change detection"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "difflib (stdlib) + custom logic"
    secret_name: "none"
```

### Known Gotchas & Constraints
```
# CRITICAL: Firecrawl has rate limits - batch crawls with delay between requests
# CRITICAL: Some competitor sites may block scrapers - use Firecrawl's stealth mode
# CRITICAL: Git has 100MB file size limit - keep snapshots under 10MB per competitor
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: Site structure changes can break selectors - fallback to full-page markdown if selectors fail
# CRITICAL: Per-competitor error isolation - one failed crawl should not stop the entire run
# CRITICAL: Historical snapshots must be committed atomically (all or nothing) to prevent partial state
# CRITICAL: Auto-detecting "new pages" requires comparing against known_pages index or crawling all linked pages
```

---

## System Design

### Subagent Architecture

```yaml
subagents:
  - name: "crawl-specialist"
    description: "Delegate when the workflow needs to scrape competitor websites, extract structured content (blog posts, pricing, features), and handle site-specific selectors. Use for all web scraping tasks."
    tools: "Bash, Read"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read competitor config from config/competitors.json"
      - "For each competitor, crawl configured URLs (blog, pricing, features)"
      - "Extract content using configured selectors"
      - "Fall back to full-page markdown if selectors fail"
      - "Handle site unavailability (timeout, 404, 503) gracefully"
      - "Return structured JSON snapshot for each competitor"
    inputs: "Competitor config object with URLs and selectors"
    outputs: "JSON snapshot with extracted blog posts, pricing, features"

  - name: "change-detector-specialist"
    description: "Delegate when the workflow needs to compare current vs previous snapshots, identify new blog posts, detect pricing changes, and find new feature pages. Use after crawling is complete."
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Load previous snapshot from state/snapshots/{slug}/latest.json"
      - "Compare current snapshot against previous snapshot"
      - "Detect new blog posts (posts in current not in previous)"
      - "Detect pricing changes (price value differences)"
      - "Detect new feature pages (features in current not in previous)"
      - "Calculate change statistics (count new posts, pricing deltas)"
      - "Return structured changes object for digest generation"
    inputs: "Current snapshot JSON, previous snapshot JSON"
    outputs: "Changes object with new_posts, pricing_changes, new_features arrays"

  - name: "report-generator-specialist"
    description: "Delegate when the workflow needs to generate the markdown digest report from detected changes. Use after change detection is complete."
    tools: "Write, Read"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Aggregate changes from all competitors"
      - "Generate markdown report with summary and per-competitor sections"
      - "Format blog posts with title, URL, date, excerpt"
      - "Format pricing changes with old/new values and deltas"
      - "Format feature changes with descriptions"
      - "Write report to reports/YYYY-MM-DD.md"
      - "Generate plain-text version for email body"
    inputs: "Array of changes objects (one per competitor)"
    outputs: "Markdown report file path, plain-text email body"

  - name: "snapshot-manager-specialist"
    description: "Delegate when the workflow needs to store or retrieve historical snapshots. Use before change detection (to load previous) and after crawling (to save current)."
    tools: "Read, Write, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Load previous snapshot from state/snapshots/{slug}/latest.json"
      - "Save current snapshot to state/snapshots/{slug}/YYYY-MM-DD.json"
      - "Update state/snapshots/{slug}/latest.json symlink or copy"
      - "Prune old snapshots (keep last 12 weeks only)"
      - "Handle missing previous snapshot (first run initialization)"
      - "Validate snapshot structure before saving"
    inputs: "Competitor slug, snapshot JSON"
    outputs: "File paths of saved snapshots, success/failure status"
```

### Agent Teams Analysis
```yaml
independent_tasks:
  - "Crawl Competitor A (blog, pricing, features)"
  - "Crawl Competitor B (blog, pricing, features)"
  - "Crawl Competitor C (blog, pricing, features)"

independent_task_count: "N (where N = number of competitors in config)"

recommendation: "Use Agent Teams IF 3+ competitors configured"

rationale: |
  Each competitor crawl is fully independent - no shared state, no data dependencies.
  Sequential: If 5 competitors at 15s each = 75s total
  Parallel: If 5 competitors with Agent Teams = 20s total (3-4x speedup)
  
  The merge logic is simple - collect all snapshots and pass to change-detector-specialist.
  
  Since most competitor configs will have 3-5 competitors, Agent Teams provides meaningful benefit.

# Agent Teams configuration
team_lead_responsibilities:
  - "Read config/competitors.json and create competitor list"
  - "Create shared task list with one task per competitor"
  - "Spawn crawl-specialist teammates (one per competitor)"
  - "Collect all snapshots from teammates"
  - "Pass snapshots to change-detector-specialist for analysis"
  - "Coordinate snapshot-manager-specialist to save all snapshots"

teammates:
  - name: "Competitor Crawler 1"
    task: "Crawl competitor {name} using crawl-specialist subagent. Extract blog posts, pricing, features. Return JSON snapshot."
    inputs: "Competitor config object (name, slug, urls, selectors)"
    outputs: "JSON snapshot for this competitor"

  - name: "Competitor Crawler 2"
    task: "Crawl competitor {name} using crawl-specialist subagent. Extract blog posts, pricing, features. Return JSON snapshot."
    inputs: "Competitor config object"
    outputs: "JSON snapshot for this competitor"

  # Note: Number of teammates = number of competitors (dynamic)

sequential_fallback: |
  If Agent Teams is disabled or fails, execute crawl-specialist sequentially for each competitor.
  Results are identical, just slower (linear time vs parallel time).
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "0 8 * * 1  # Every Monday at 8 AM UTC"
    description: "Weekly automated competitor monitoring"

  - type: "workflow_dispatch"
    config: |
      inputs:
        force_run:
          description: 'Force crawl even if not scheduled time'
          type: boolean
          default: false
    description: "Manual trigger for testing or ad-hoc competitor checks"
```

---

## Implementation Blueprint

### Workflow Steps

```yaml
steps:
  - name: "Load Configuration"
    description: "Read config/competitors.json and validate structure"
    subagent: "none (main agent)"
    tools: ["Read"]
    inputs: "config/competitors.json file path"
    outputs: "Parsed competitor config object"
    failure_mode: "Config file missing or invalid JSON"
    fallback: "Halt with clear error - cannot proceed without competitor list"

  - name: "Crawl Competitors (Parallel if 3+)"
    description: "Scrape each competitor's blog, pricing, and feature pages"
    subagent: "crawl-specialist (via Agent Teams if 3+ competitors, else sequential)"
    tools: ["crawl_competitor.py"]
    inputs: "Competitor config objects (one per competitor)"
    outputs: "Array of JSON snapshots (one per competitor)"
    failure_mode: "Competitor site unreachable, selectors fail, Firecrawl API error"
    fallback: "Skip failed competitor, log error, continue with others. Partial results are acceptable."

  - name: "Detect Changes"
    description: "Compare current snapshots against previous week's snapshots"
    subagent: "change-detector-specialist"
    tools: ["detect_changes.py"]
    inputs: "Current snapshots array, previous snapshots (from state/snapshots/)"
    outputs: "Changes object with new_posts, pricing_changes, new_features per competitor"
    failure_mode: "Previous snapshot missing (first run), snapshot format mismatch"
    fallback: "If first run, treat all content as 'new'. If format mismatch, fall back to full-text diff."

  - name: "Generate Digest Report"
    description: "Create markdown report summarizing all changes"
    subagent: "report-generator-specialist"
    tools: ["generate_digest.py"]
    inputs: "Changes objects array (one per competitor)"
    outputs: "reports/YYYY-MM-DD.md, plain-text email body"
    failure_mode: "No changes detected across any competitor"
    fallback: "Generate report saying 'No changes detected this week' and skip email"

  - name: "Save Snapshots"
    description: "Store current snapshots for next week's comparison"
    subagent: "snapshot-manager-specialist"
    tools: ["save_snapshot.py"]
    inputs: "Current snapshots array"
    outputs: "state/snapshots/{slug}/YYYY-MM-DD.json files, updated latest.json"
    failure_mode: "Disk space full, snapshot too large (>10MB)"
    fallback: "Compress snapshot (drop excerpts, keep only titles/URLs). If still fails, skip snapshot save but commit report."

  - name: "Send Email (Optional)"
    description: "Email digest to configured recipients if enabled"
    subagent: "none (main agent)"
    tools: ["send_email.py"]
    inputs: "Plain-text email body, config.email settings"
    outputs: "Email delivery status"
    failure_mode: "SMTP credentials missing, SMTP server unreachable, recipients list empty"
    fallback: "Log error but do NOT fail the workflow - report is already committed to repo"

  - name: "Commit Results"
    description: "Git commit report and snapshots to repository"
    subagent: "none (main agent)"
    tools: ["Bash (git commands)"]
    inputs: "Report file path, snapshot file paths"
    outputs: "Git commit SHA"
    failure_mode: "Git push fails (network error, conflict)"
    fallback: "Retry git push once after 10s delay. If still fails, job fails (results not persisted)."
```

### Tool Specifications

```yaml
tools:
  - name: "crawl_competitor.py"
    purpose: "Scrape a single competitor's blog, pricing, and feature pages"
    catalog_pattern: "firecrawl_scrape (tool_catalog.md) + custom content extraction"
    inputs:
      - "competitor_config: dict — Config object with name, slug, urls, selectors"
      - "api_key: str — Firecrawl API key from environment"
    outputs: |
      JSON object:
      {
        "competitor": "slug",
        "timestamp": "ISO8601",
        "pages": {
          "blog": {"url": "...", "posts": [...]},
          "pricing": {"url": "...", "plans": [...]},
          "features": {"url": "...", "features": [...]}
        }
      }
    dependencies: ["firecrawl-py", "httpx", "beautifulsoup4", "lxml"]
    mcp_used: "firecrawl"
    error_handling: "Try Firecrawl first, fall back to Puppeteer, then HTTP+BeautifulSoup. If all fail, return empty snapshot with error flag."

  - name: "detect_changes.py"
    purpose: "Compare current vs previous snapshots and identify changes"
    catalog_pattern: "filter_sort (catalog) + custom diff logic with difflib"
    inputs:
      - "current_snapshot: dict — Current week's snapshot"
      - "previous_snapshot: dict — Last week's snapshot (or None if first run)"
    outputs: |
      JSON object:
      {
        "competitor": "slug",
        "new_posts": [{title, url, published, excerpt}],
        "pricing_changes": [{plan, old_price, new_price, delta_pct}],
        "new_features": [{title, description, url}],
        "summary": {new_posts_count, pricing_changes_count, new_features_count}
      }
    dependencies: ["None (stdlib only - difflib, json, pathlib)"]
    mcp_used: "none"
    error_handling: "If previous snapshot missing, treat all content as new. If snapshot format differs, fall back to string diff on JSON dumps."

  - name: "generate_digest.py"
    purpose: "Generate markdown report from changes data"
    catalog_pattern: "transform_map (catalog) + custom markdown generation"
    inputs:
      - "changes_array: list[dict] — Array of changes objects (one per competitor)"
      - "report_date: str — YYYY-MM-DD format"
    outputs: |
      - Markdown file at reports/YYYY-MM-DD.md
      - Plain text string for email body
    dependencies: ["None (stdlib only - pathlib, datetime)"]
    mcp_used: "none"
    error_handling: "If no changes detected, generate minimal report saying 'No changes this week'. Never fail."

  - name: "save_snapshot.py"
    purpose: "Store current snapshot to state/snapshots/{slug}/"
    catalog_pattern: "json_read_write (catalog)"
    inputs:
      - "snapshot: dict — Snapshot object to save"
      - "competitor_slug: str — Directory name"
      - "date: str — YYYY-MM-DD format"
    outputs: |
      - File paths: state/snapshots/{slug}/YYYY-MM-DD.json, state/snapshots/{slug}/latest.json
      - Success status boolean
    dependencies: ["None (stdlib only - json, pathlib, shutil)"]
    mcp_used: "none"
    error_handling: "If snapshot size > 10MB, compress by dropping excerpts. If disk full, log error and return False but don't crash."

  - name: "send_email.py"
    purpose: "Send digest report via SMTP"
    catalog_pattern: "email_send (catalog) - SMTP variant"
    inputs:
      - "subject: str — Email subject line"
      - "body_html: str — HTML email body"
      - "body_text: str — Plain text email body"
      - "recipients: list[str] — Email addresses"
      - "smtp_config: dict — SMTP credentials from environment"
    outputs: |
      - Success status boolean
      - Error message if failed
    dependencies: ["None (stdlib only - smtplib, email.mime)"]
    mcp_used: "none"
    error_handling: "Retry once after 10s on transient failures (network, auth). If still fails, log error and return False. Never crash."
```

### Per-Tool Pseudocode

```python
# crawl_competitor.py
def main():
    # PATTERN: firecrawl_scrape with fallback chain
    # Step 1: Parse inputs
    args = parse_args()  # competitor config JSON path
    config = json.load(open(args.config))
    
    # Step 2: Scrape each page type (blog, pricing, features)
    # CRITICAL: Firecrawl rate limit - add 2s delay between requests
    snapshot = {"competitor": config["slug"], "timestamp": now(), "pages": {}}
    for page_type, url in config["urls"].items():
        try:
            # Try Firecrawl first
            content = firecrawl_scrape(url, config["selectors"][page_type])
        except FirecrawlError:
            # Fallback to Puppeteer
            try:
                content = puppeteer_scrape(url, config["selectors"][page_type])
            except:
                # Fallback to HTTP + BeautifulSoup
                content = http_scrape(url)
        
        snapshot["pages"][page_type] = extract_content(content, page_type, config["selectors"])
    
    # Step 3: Output snapshot
    print(json.dumps(snapshot))

# detect_changes.py
def main():
    # PATTERN: Custom diff logic with difflib
    # CRITICAL: Handle first run (no previous snapshot)
    args = parse_args()
    current = json.load(open(args.current))
    previous = json.load(open(args.previous)) if args.previous and Path(args.previous).exists() else None
    
    changes = {
        "competitor": current["competitor"],
        "new_posts": [],
        "pricing_changes": [],
        "new_features": []
    }
    
    if previous is None:
        # First run - treat all as new
        changes["new_posts"] = current["pages"]["blog"]["posts"]
        changes["new_features"] = current["pages"]["features"]["features"]
    else:
        # Compare blog posts by URL
        prev_urls = {p["url"] for p in previous["pages"]["blog"]["posts"]}
        changes["new_posts"] = [p for p in current["pages"]["blog"]["posts"] if p["url"] not in prev_urls]
        
        # Compare pricing by plan name and price value
        # ... (diff logic)
    
    print(json.dumps(changes))

# generate_digest.py
def main():
    # PATTERN: Markdown generation from structured data
    args = parse_args()
    changes_list = [json.load(open(f)) for f in args.changes_files]
    
    # Generate markdown
    md = f"# Competitor Monitor Report - {args.date}\n\n"
    md += generate_summary(changes_list)
    for changes in changes_list:
        md += generate_competitor_section(changes)
    
    # Write to file
    Path(f"reports/{args.date}.md").write_text(md)
    
    # Generate plain text for email
    text = strip_markdown_formatting(md)
    print(json.dumps({"report_path": f"reports/{args.date}.md", "email_body": text}))

# save_snapshot.py
def main():
    # PATTERN: json_read_write
    # CRITICAL: Atomic write (tmp file + rename) to prevent corruption
    args = parse_args()
    snapshot = json.load(open(args.snapshot))
    
    output_dir = Path(f"state/snapshots/{args.slug}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save dated snapshot
    dated_path = output_dir / f"{args.date}.json"
    tmp_path = dated_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(snapshot, indent=2))
    tmp_path.rename(dated_path)
    
    # Update latest.json
    latest_path = output_dir / "latest.json"
    tmp_path = latest_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(snapshot, indent=2))
    tmp_path.rename(latest_path)
    
    print(json.dumps({"success": True, "paths": [str(dated_path), str(latest_path)]}))

# send_email.py
def main():
    # PATTERN: email_send (SMTP variant)
    # CRITICAL: SMTP credentials from environment only
    args = parse_args()
    
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = args.subject
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = ", ".join(args.recipients)
    
    msg.attach(MIMEText(args.body_text, "plain"))
    msg.attach(MIMEText(args.body_html, "html"))
    
    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            server.send_message(msg)
        print(json.dumps({"success": True}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)
```

### Integration Points

```yaml
SECRETS:
  - name: "FIRECRAWL_API_KEY"
    purpose: "Authenticate with Firecrawl web scraping API"
    required: true

  - name: "SMTP_HOST"
    purpose: "SMTP server hostname for email delivery"
    required: false (only if email enabled)

  - name: "SMTP_PORT"
    purpose: "SMTP server port (usually 587 for TLS)"
    required: false (only if email enabled)

  - name: "SMTP_USER"
    purpose: "SMTP authentication username"
    required: false (only if email enabled)

  - name: "SMTP_PASS"
    purpose: "SMTP authentication password"
    required: false (only if email enabled)

  - name: "EMAIL_FROM"
    purpose: "From address for outgoing emails"
    required: false (only if email enabled)

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "FIRECRAWL_API_KEY=fc_sk_xxx  # Get from https://firecrawl.dev"
      - "SMTP_HOST=smtp.gmail.com  # Optional: only needed if email enabled"
      - "SMTP_PORT=587  # Optional"
      - "SMTP_USER=your-email@gmail.com  # Optional"
      - "SMTP_PASS=your-app-password  # Optional"
      - "EMAIL_FROM=noreply@example.com  # Optional"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "firecrawl-py==0.1.0  # Primary web scraping"
      - "httpx==0.27.0  # HTTP client for fallback"
      - "beautifulsoup4==4.12.3  # HTML parsing for fallback"
      - "lxml==5.1.0  # Fast HTML parser"
      - "playwright==1.41.0  # Optional: advanced JS rendering fallback"

GITHUB_ACTIONS:
  - trigger: "schedule: 0 8 * * 1  # Every Monday 8 AM UTC"
    config: "Weekly automated run"
  - trigger: "workflow_dispatch with force_run input"
    config: "Manual testing and ad-hoc checks"
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# Verify Python syntax for all tools
python -c "import ast; ast.parse(open('tools/crawl_competitor.py').read())"
python -c "import ast; ast.parse(open('tools/detect_changes.py').read())"
python -c "import ast; ast.parse(open('tools/generate_digest.py').read())"
python -c "import ast; ast.parse(open('tools/save_snapshot.py').read())"
python -c "import ast; ast.parse(open('tools/send_email.py').read())"

# Verify imports work
python -c "import importlib; importlib.import_module('tools.crawl_competitor')"
python -c "import importlib; importlib.import_module('tools.detect_changes')"
python -c "import importlib; importlib.import_module('tools.generate_digest')"
python -c "import importlib; importlib.import_module('tools.save_snapshot')"
python -c "import importlib; importlib.import_module('tools.send_email')"

# Verify main() exists
python -c "from tools.crawl_competitor import main; assert callable(main)"
python -c "from tools.detect_changes import main; assert callable(main)"
python -c "from tools.generate_digest import main; assert callable(main)"
python -c "from tools.save_snapshot import main; assert callable(main)"
python -c "from tools.send_email import main; assert callable(main)"

# Verify subagent files
python -c "import yaml; yaml.safe_load(open('.claude/agents/crawl-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/change-detector-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/report-generator-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/snapshot-manager-specialist.md').read().split('---')[1])"

# Expected: All pass with exit code 0. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Test crawl_competitor.py with mock competitor config
echo '{"name":"Test Co","slug":"test-co","urls":{"blog":"https://example.com"},"selectors":{"blog_posts":"article"}}' > /tmp/test_competitor.json
python tools/crawl_competitor.py --config /tmp/test_competitor.json > /tmp/crawl_output.json
# Expected: Valid JSON with competitor, timestamp, pages keys

# Test detect_changes.py with sample snapshots
python tools/detect_changes.py --current /tmp/crawl_output.json --previous /tmp/crawl_output.json > /tmp/changes.json
# Expected: Valid JSON with new_posts, pricing_changes, new_features (all empty since same snapshot)

# Test detect_changes.py first run (no previous)
python tools/detect_changes.py --current /tmp/crawl_output.json > /tmp/changes_first.json
# Expected: Valid JSON with all content marked as "new"

# Test generate_digest.py
python tools/generate_digest.py --changes /tmp/changes.json --date 2026-02-10
# Expected: reports/2026-02-10.md file created with valid markdown

# Test save_snapshot.py
python tools/save_snapshot.py --snapshot /tmp/crawl_output.json --slug test-co --date 2026-02-10
# Expected: state/snapshots/test-co/2026-02-10.json and latest.json created

# Test send_email.py error handling (no SMTP credentials)
python tools/send_email.py --subject "Test" --body-text "Test" --recipients "test@example.com" 2>&1 | grep -q "error"
# Expected: Exit code 1 with error message about missing SMTP credentials

# If any tool fails: Read the error, fix the root cause, re-run.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline

# Step 1: Create sample competitor config
cat > config/competitors.json <<EOF
{
  "competitors": [
    {"name": "Test A", "slug": "test-a", "urls": {"blog": "https://example.com"}, "selectors": {"blog_posts": "article"}},
    {"name": "Test B", "slug": "test-b", "urls": {"blog": "https://example.org"}, "selectors": {"blog_posts": ".post"}}
  ],
  "email": {"enabled": false}
}
EOF

# Step 2: Simulate full workflow (sequential)
python tools/crawl_competitor.py --config <(jq '.competitors[0]' config/competitors.json) > /tmp/snapshot_a.json
python tools/crawl_competitor.py --config <(jq '.competitors[1]' config/competitors.json) > /tmp/snapshot_b.json
python tools/detect_changes.py --current /tmp/snapshot_a.json > /tmp/changes_a.json
python tools/detect_changes.py --current /tmp/snapshot_b.json > /tmp/changes_b.json
python tools/generate_digest.py --changes /tmp/changes_a.json /tmp/changes_b.json --date 2026-02-10
python tools/save_snapshot.py --snapshot /tmp/snapshot_a.json --slug test-a --date 2026-02-10
python tools/save_snapshot.py --snapshot /tmp/snapshot_b.json --slug test-b --date 2026-02-10

# Step 3: Verify outputs exist
test -f reports/2026-02-10.md && echo "✓ Report generated"
test -f state/snapshots/test-a/2026-02-10.json && echo "✓ Snapshot A saved"
test -f state/snapshots/test-b/2026-02-10.json && echo "✓ Snapshot B saved"

# Step 4: Verify cross-references
grep -q "test-a" reports/2026-02-10.md && echo "✓ Report mentions competitor A"
grep -q "test-b" reports/2026-02-10.md && echo "✓ Report mentions competitor B"

# Step 5: Verify subagent references in CLAUDE.md
grep -q "crawl-specialist" CLAUDE.md && echo "✓ CLAUDE.md documents crawl-specialist"
grep -q "change-detector-specialist" CLAUDE.md && echo "✓ CLAUDE.md documents change-detector-specialist"
grep -q "report-generator-specialist" CLAUDE.md && echo "✓ CLAUDE.md documents report-generator-specialist"
grep -q "snapshot-manager-specialist" CLAUDE.md && echo "✓ CLAUDE.md documents snapshot-manager-specialist"

# Step 6: Verify no hardcoded secrets
! grep -rE '(sk-|api_key=|bearer [a-zA-Z0-9])' tools/ && echo "✓ No hardcoded secrets"

# Expected: All checks pass. If any fail, fix and re-run Level 3.
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes and failure notifications
- [ ] .env.example lists all required environment variables
- [ ] .gitignore excludes .env, __pycache__/, state/snapshots/*/tmp files
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies
- [ ] config/competitors.json has example structure with 2-3 sample competitors

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only specific files
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks — Firecrawl should have Puppeteer and HTTP fallbacks
- Do not design subagents that call other subagents — only the main agent delegates
- Do not use Agent Teams when fewer than 3 independent tasks exist — but this system DOES have N competitors (likely 3+)
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not store snapshots > 10MB — compress by dropping excerpts if needed
- Do not fail the entire run if one competitor crawl fails — per-competitor error isolation is critical

---

## Confidence Score: 8/10

**Score rationale:**
- **Web scraping pattern**: High confidence — Firecrawl MCP is well-documented, fallback to Puppeteer and HTTP is proven. Pattern: **Scrape > Process > Output**
- **Change detection logic**: High confidence — difflib for text comparison is stdlib, pattern is straightforward (compare arrays of objects by key fields)
- **State management**: High confidence — Git-native snapshot storage is proven in other systems (rss-digest-monitor), atomic writes prevent corruption
- **Agent Teams parallelization**: High confidence — N independent crawls is textbook use case for Agent Teams, merge logic is simple (collect snapshots)
- **Auto-detecting new pages**: Medium-low confidence — **AMBIGUITY FLAG RAISED** (see below)

**Ambiguity flags** (areas requiring clarification before building):
- [x] **"Auto-detect new pages without limiting to known URLs only"** — Does this mean:
  - (a) Crawl all linked pages on the site and detect when a new URL appears in the link set? (Easy: extract all `<a>` tags, compare against previous week's link set)
  - (b) Smart detection of "blog post" vs "about page" vs "feature page" based on URL patterns or content analysis? (Medium: requires heuristics like URL path matching `/blog/`, `/features/`, or Claude-based classification)
  - (c) Full site crawl with unlimited depth? (Hard: rate limits, storage size, scope creep)
  
  **Recommended clarification question**: "For auto-detecting new pages, should the system (a) extract all links and flag new URLs that match known patterns (e.g., `/blog/*`, `/features/*`), (b) use Claude to classify new pages as blog/pricing/feature based on content, or (c) crawl unlimited depth?"
  
  **Temporary assumption for build**: Use option (a) — extract all links matching URL patterns in the competitor config (e.g., if `blog_url` is `https://example.com/blog`, flag any new URL starting with `/blog/` as a potential new blog post). This is deterministic, fast, and doesn't require Claude for classification.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/competitor-monitor.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
