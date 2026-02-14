name: "site-intelligence-pack"
description: |

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

Build a comprehensive website analysis system that produces evidence-backed business intelligence reports by crawling target domains, ranking pages by relevance, extracting structured data from top pages, and synthesizing findings with full evidence provenance. The system must respect robots.txt, enforce rate limits, handle multi-domain batch processing, and produce audit-ready JSON outputs with quoted evidence for every claim.

**End state:** A scheduled or on-demand workflow that takes a domain (or CSV of domains), produces a complete "Site Intelligence Pack" JSON file with page inventory, ranked pages, deep extractions, synthesized findings, and an evidence index — all committed to the repo under `outputs/{domain}/{timestamp}/`.

---

## Why

- **Business value**: Automates 4-8 hours of manual competitive research into a 10-15 minute workflow, enabling marketing/sales teams to gather actionable intelligence at scale.
- **What it automates**: Manual website crawling, note-taking, screenshot collection, pricing extraction, feature comparison, and report writing.
- **Who benefits**: GTM teams (sales, marketing, BD) who need structured intelligence on prospects, competitors, or partnership targets. Runs nightly for a watchlist or on-demand for ad-hoc research.

---

## What

The system receives a target domain (single input or batch CSV), crawls up to 200 pages, ranks them by relevance (pricing, offers, FAQs, policies, testimonials), deep-extracts structured data from the top K pages, synthesizes findings with evidence tracking, and commits the full intelligence pack to the repo.

### User-visible behavior:

1. **Trigger**: `workflow_dispatch` with a single domain input OR scheduled run that processes `inputs/targets.csv`
2. **Execution**: System fetches robots.txt, crawls the site (respecting disallowed paths and rate limits), ranks pages, extracts structured data, and synthesizes findings
3. **Output**: Commits to `outputs/{domain}/{timestamp}/` containing:
   - `inventory.json` — all discovered pages with canonical URLs, titles, dedup clusters
   - `ranked_pages.json` — pages sorted by relevance with category tags
   - `deep_extract.json` — structured extractions from top K pages with quoted evidence
   - `site_intelligence_pack.json` — final synthesized report with evidence index
   - `README.md` — human-readable summary
4. **Failure handling**: If < 5 pages extracted successfully, open a GitHub Issue with diagnostic details but still commit partial outputs

### Success Criteria

- [x] Successfully crawls target domain (max 200 pages)
- [x] Respects robots.txt (fetches first, checks disallowed paths, skips blocked URLs)
- [x] Rate limiting enforced (1-2 req/sec with politeness controls)
- [x] Page discovery attempts explicit paths: /pricing, /faq, /about, /contact, /privacy, /terms
- [x] Relevance ranking applied to all pages (priority: offers/pricing → about/faq → blog/other)
- [x] Deep extraction on top K pages (K = 10-20 depending on page count)
- [x] Every synthesized claim has evidence entries (url + excerpt + timestamp)
- [x] De-duplication applied (canonical URLs, content hashing, cluster IDs)
- [x] JSON schema validation on final output
- [x] Outputs committed to `outputs/{domain}/{timestamp}/`
- [x] GitHub Issue created if < 5 pages extracted or critical failure
- [x] System runs autonomously via GitHub Actions on schedule
- [x] Results are committed back to repo or delivered via webhook/notification
- [x] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs

```yaml
- name: "target_domain"
  type: "string"
  source: "workflow_dispatch input OR first column of inputs/targets.csv"
  required: true
  description: "Domain to analyze (without protocol, e.g., 'example.com')"
  example: "stripe.com"

- name: "max_pages"
  type: "integer"
  source: "workflow_dispatch input (default: 200)"
  required: false
  description: "Maximum pages to crawl per domain"
  example: "200"

- name: "deep_extract_count"
  type: "integer"
  source: "workflow_dispatch input (default: 15)"
  required: false
  description: "Number of top-ranked pages to deep-extract"
  example: "15"

- name: "batch_mode"
  type: "boolean"
  source: "workflow_dispatch input (default: false)"
  required: false
  description: "If true, process all domains in inputs/targets.csv sequentially"
  example: "false"
```

---

## Outputs

```yaml
- name: "inventory.json"
  type: "JSON"
  destination: "outputs/{domain}/{timestamp}/inventory.json"
  description: "All discovered pages with URLs, titles, HTTP status, content hashes, dedup cluster IDs"
  example: |
    [
      {
        "url": "https://example.com/pricing",
        "canonical_url": "https://example.com/pricing",
        "title": "Pricing Plans",
        "discovered_from": "sitemap",
        "http_status": 200,
        "content_hash": "sha256:abc123...",
        "dedup_cluster_id": "cluster_001",
        "notes": null
      }
    ]

- name: "ranked_pages.json"
  type: "JSON"
  destination: "outputs/{domain}/{timestamp}/ranked_pages.json"
  description: "Pages sorted by relevance score with category tags"
  example: |
    [
      {
        "url": "https://example.com/pricing",
        "canonical_url": "https://example.com/pricing",
        "rank": 1,
        "reasons": ["Path contains 'pricing'", "Title indicates pricing information"],
        "category": "offers_and_pricing"
      }
    ]

- name: "deep_extract.json"
  type: "JSON"
  destination: "outputs/{domain}/{timestamp}/deep_extract.json"
  description: "Structured extractions from top K pages with quoted evidence"
  example: |
    {
      "pages": [
        {
          "url": "https://example.com/pricing",
          "canonical_url": "https://example.com/pricing",
          "title": "Pricing Plans",
          "summary": "Three pricing tiers: Starter ($29/mo), Pro ($99/mo), Enterprise (custom)",
          "offers": [
            {
              "name": "Pro Plan",
              "price": "$99/month",
              "billing_terms": "Annual billing available at 20% discount",
              "guarantees": "30-day money-back guarantee",
              "evidence": ["EV_001", "EV_002"]
            }
          ]
        }
      ]
    }

- name: "site_intelligence_pack.json"
  type: "JSON"
  destination: "outputs/{domain}/{timestamp}/site_intelligence_pack.json"
  description: "Final synthesized intelligence report with evidence index"
  example: |
    {
      "site": {
        "target_url": "https://example.com",
        "domain": "example.com",
        "crawled_at_iso": "2026-02-14T14:30:00Z",
        "robots": {
          "fetched_url": "https://example.com/robots.txt",
          "allowed_summary": "All pages allowed except /admin",
          "disallowed_summary": "/admin",
          "raw_excerpt": "User-agent: *\nDisallow: /admin"
        }
      },
      "synthesized_findings": {
        "positioning": {
          "claims": [
            {
              "id": "POS_001",
              "claim": "Targets SMBs in e-commerce vertical",
              "evidence": ["EV_015", "EV_022"]
            }
          ]
        }
      },
      "evidence_index": {
        "EV_001": {
          "url": "https://example.com/pricing",
          "excerpt": "Pro Plan: $99/month with unlimited users",
          "page_title": "Pricing Plans",
          "extracted_at_iso": "2026-02-14T14:35:12Z"
        }
      }
    }

- name: "README.md"
  type: "Markdown"
  destination: "outputs/{domain}/{timestamp}/README.md"
  description: "Human-readable summary of findings"
  example: |
    # Site Intelligence Pack: example.com
    Generated: 2026-02-14 14:30:00 UTC
    
    ## Summary
    Crawled 187 pages, extracted 15 deep pages.
    Primary offering: SaaS analytics platform for e-commerce.
    
    ## Key Findings
    - Three pricing tiers: Starter ($29/mo), Pro ($99/mo), Enterprise (custom)
    - 30-day money-back guarantee on all plans
    - Targets SMB e-commerce merchants
    
    ## Files
    - inventory.json: Full page inventory (187 pages)
    - ranked_pages.json: Relevance-ranked pages (187 pages)
    - deep_extract.json: Structured extractions (15 pages)
    - site_intelligence_pack.json: Final intelligence pack with evidence

- name: "GitHub Issue (on failure)"
  type: "GitHub Issue"
  destination: "Repository issues"
  description: "Created if < 5 pages extracted or critical failure"
  example: |
    Title: "Site Intelligence Pack FAILED: example.com"
    Body:
    Target: example.com
    Timestamp: 2026-02-14T14:30:00Z
    Pages crawled: 2
    Pages extracted: 1
    Error: Firecrawl API returned 429 (rate limited) after 3 retries.
    Attempted fallback to HTTP scraping but site requires JavaScript rendering.
    Partial outputs committed to: outputs/example.com/2026-02-14T143000/
```

---

## All Needed Context

### Documentation & References

```yaml
# MUST READ — Include these in context when building
- url: "https://docs.firecrawl.dev/api-reference/endpoint/crawl"
  why: "Firecrawl crawl endpoint parameters, rate limits, response format"

- url: "https://docs.firecrawl.dev/api-reference/endpoint/scrape"
  why: "Firecrawl scrape endpoint for single-page extraction with selectors"

- doc: "config/mcp_registry.md"
  why: "Check Firecrawl MCP capabilities and fallback strategies"

- doc: "library/patterns.md"
  why: "Select workflow pattern (Scrape > Process > Output + Fan-Out > Process > Merge)"

- doc: "library/tool_catalog.md"
  why: "Reuse firecrawl_scrape, rest_client, structured_extract, github_create_issue patterns"

- url: "https://www.rfc-editor.org/rfc/rfc9309.html"
  why: "robots.txt specification for parsing and compliance"

- url: "https://json-schema.org/understanding-json-schema"
  why: "JSON Schema validation for final output structure"
```

### Workflow Pattern Selection

```yaml
pattern: "Scrape > Process > Output + Fan-Out > Process > Merge + Collect > Transform > Store"
rationale: |
  Base pattern is Scrape > Process > Output (crawl → extract → commit).
  Fan-Out > Process > Merge is used for parallel deep extraction of top K pages (3+ independent extraction tasks).
  Collect > Transform > Store handles the final synthesis and evidence indexing phase.
modifications: |
  - Add robots.txt fetch and compliance check before crawling
  - Add rate limiting middleware (1-2 req/sec) to all HTTP calls
  - Add de-duplication phase after inventory collection
  - Add evidence tracking to all extraction phases
  - Add schema validation gate before final commit
```

### MCP & Tool Requirements

```yaml
capabilities:
  - name: "web crawling"
    primary_mcp: "Firecrawl"
    alternative_mcp: "Puppeteer (for JS-heavy sites)"
    fallback: "Direct HTTP with requests + BeautifulSoup"
    secret_name: "FIRECRAWL_API_KEY"
    notes: "Firecrawl handles JS rendering and returns clean markdown. Fallback loses JS content but maintains basic functionality."

  - name: "web scraping (single page)"
    primary_mcp: "Firecrawl"
    alternative_mcp: "Fetch MCP"
    fallback: "Python requests library"
    secret_name: "FIRECRAWL_API_KEY"
    notes: "Firecrawl preferred for consistent formatting. HTTP fallback for simple pages."

  - name: "structured data extraction"
    primary_mcp: "Anthropic (Claude)"
    alternative_mcp: "None"
    fallback: "Regex + heuristics (limited accuracy)"
    secret_name: "ANTHROPIC_API_KEY"
    notes: "LLM extraction is core to this system. Fallback to regex only for simple fields (email, phone)."

  - name: "GitHub operations"
    primary_mcp: "GitHub MCP"
    alternative_mcp: "None"
    fallback: "gh CLI or direct REST API"
    secret_name: "GITHUB_TOKEN"
    notes: "Issue creation and commits. MCP preferred for simplicity."

  - name: "file operations"
    primary_mcp: "Filesystem MCP"
    alternative_mcp: "None"
    fallback: "Python pathlib (stdlib)"
    secret_name: "None"
    notes: "Local file I/O for JSON and markdown outputs."
```

### Known Gotchas & Constraints

```
# CRITICAL: Firecrawl API has rate limit of 10 concurrent requests. Enforce max_concurrency=5 to stay safe.
# CRITICAL: Firecrawl crawl endpoint can take 60-300 seconds for large sites. Set timeout to 600s minimum.
# CRITICAL: robots.txt MUST be fetched first. If disallowed path is crawled, respect and skip with warning.
# CRITICAL: Many sites use canonical link tags — ALWAYS extract and use for de-duplication.
# CRITICAL: Header/footer boilerplate detection: If content similarity > 80% across 5+ pages, flag as boilerplate.
# CRITICAL: Evidence tracking: Every extracted field MUST have a list of evidence IDs. No unsourced claims.
# CRITICAL: Evidence excerpts should be 50-150 chars — long enough to verify, short enough to read.
# CRITICAL: URL normalization: Strip query params (except pagination), lowercase domain, trailing slash normalization.
# CRITICAL: Authentication/paywall detection: If page returns login prompt or paywall notice, mark as inaccessible but include in inventory.
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env.
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function.
```

---

## System Design

### Subagent Architecture

```yaml
subagents:
  - name: "relevance-ranker-specialist"
    description: "Delegate when you need to rank/prioritize pages by relevance to business intelligence needs. Called after inventory collection."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Analyze page URLs, titles, and first 500 chars of content"
      - "Apply path keyword scoring (pricing, faq, about, contact, terms, privacy, careers)"
      - "Apply lightweight semantic scoring on titles and headings"
      - "Assign priority categories: offers_and_pricing (highest), how_it_works, policies, testimonials, about, faq, contact, blog (lowest)"
      - "Return ranked list with scores and category tags"
    inputs: "inventory.json (all discovered pages)"
    outputs: "ranked_pages.json (sorted by relevance with category tags)"

  - name: "deep-extract-specialist"
    description: "Delegate when you need to extract structured business data from a page. Called for each of the top K ranked pages. Responsible for evidence tracking."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Deep-scrape a single page (full content via Firecrawl or HTTP fallback)"
      - "Extract structured fields: company_name, product_names, audience, locations, contact_points, offers, pricing, how_it_works, faq, testimonials, policies"
      - "For EVERY extracted field, capture quoted evidence (50-150 char excerpt) with URL and timestamp"
      - "Assign unique evidence IDs (EV_001, EV_002, etc.)"
      - "Mark pages requiring login or blocked by robots.txt as inaccessible"
      - "Return structured page extraction JSON with evidence lists"
    inputs: "Single page URL from ranked_pages.json"
    outputs: "Structured extraction dict with evidence IDs"

  - name: "synthesis-validator-specialist"
    description: "Delegate when you need to synthesize all extractions into the final intelligence pack. Called after all deep extractions complete. Responsible for evidence index and schema validation."
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Read all deep extraction JSONs"
      - "Build synthesized findings across 5 dimensions: positioning, offers_and_pricing, customer_journey, trust_signals, compliance_and_policies"
      - "Every synthesized claim MUST reference evidence IDs"
      - "Build evidence_index with EV_ID → {url, excerpt, page_title, extracted_at_iso}"
      - "Identify unknowns and gaps (e.g., pricing not found, no testimonials)"
      - "Run JSON schema validation on final output"
      - "Generate human-readable README.md summary"
    inputs: "deep_extract.json, ranked_pages.json, inventory.json"
    outputs: "site_intelligence_pack.json, README.md"
```

### Agent Teams Analysis

```yaml
independent_tasks:
  - "Deep-extract page 1 (top ranked)"
  - "Deep-extract page 2"
  - "Deep-extract page 3"
  - "Deep-extract page 4"
  - "Deep-extract page 5"
  - "[...up to K pages]"

independent_task_count: "10-20 (configurable)"
recommendation: "Use Agent Teams for deep extraction phase"
rationale: |
  Deep extraction of K pages is perfectly parallelizable. Each page extraction:
  - Takes 15-30 seconds per page (LLM call + scraping)
  - Has no dependency on other pages
  - Produces independent structured JSON
  
  Sequential: 10 pages × 20s = 200 seconds (3.3 minutes)
  Parallel (Agent Teams): 10 pages / 5 teammates = ~40 seconds (5x speedup)
  
  Trade-off: Same token cost, faster wall time, more complex coordination.

team_lead_responsibilities:
  - "Read ranked_pages.json and select top K pages for deep extraction"
  - "Create task manifest: list of URLs to extract"
  - "Spawn K teammates (or batch into groups of 5-10 for memory efficiency)"
  - "Collect all extraction results"
  - "Merge into deep_extract.json"
  - "Delegate to synthesis-validator-specialist for final pack"

teammates:
  - name: "page-extractor-01"
    task: "Deep-extract structured data from assigned page URL. Return JSON with evidence."
    inputs: "Single page URL"
    outputs: "Structured extraction dict"

  - name: "page-extractor-02"
    task: "Deep-extract structured data from assigned page URL. Return JSON with evidence."
    inputs: "Single page URL"
    outputs: "Structured extraction dict"

  # [...repeat for K teammates]

sequential_fallback: |
  If Agent Teams fails (coordination error, memory limit, timeout):
  - Fall back to sequential deep extraction
  - Process pages one at a time with progress logging
  - Same output format, just slower wall time
```

### GitHub Actions Triggers

```yaml
triggers:
  - type: "workflow_dispatch"
    config: |
      inputs:
        target_domain:
          description: 'Domain to analyze (e.g., stripe.com)'
          required: true
        max_pages:
          description: 'Maximum pages to crawl'
          required: false
          default: '200'
        deep_extract_count:
          description: 'Number of top pages to deep-extract'
          required: false
          default: '15'
        batch_mode:
          description: 'Process all domains in inputs/targets.csv'
          required: false
          default: 'false'
    description: "Manual trigger for single domain or batch processing"

  - type: "schedule"
    config: "cron: '0 2 * * *'  # Daily at 2 AM UTC"
    description: "Nightly batch processing of inputs/targets.csv (if batch_mode enabled)"

  - type: "repository_dispatch"
    config: "event_type: 'site_intelligence_request'"
    description: "External trigger via webhook (for integration with other systems)"
```

---

## Implementation Blueprint

### Workflow Steps

```yaml
steps:
  - name: "Initialize"
    description: "Parse inputs, validate domain, create output directory structure"
    subagent: "main agent"
    tools: []
    inputs: "workflow_dispatch inputs or inputs/targets.csv"
    outputs: "Validated domain, output_dir path, config dict"
    failure_mode: "Invalid domain format or missing inputs"
    fallback: "Log error, skip domain, continue with next (batch mode) or halt (single mode)"

  - name: "Fetch robots.txt"
    description: "Fetch and parse robots.txt for the target domain. Extract User-agent: * rules."
    subagent: "main agent"
    tools: ["fetch_robots.py"]
    inputs: "target_domain"
    outputs: "robots_dict: {allowed_summary, disallowed_summary, raw_excerpt, disallowed_paths: [list]}"
    failure_mode: "robots.txt not found (404) or unreachable"
    fallback: "Assume all paths allowed, log warning, proceed with crawl"

  - name: "Crawl site"
    description: "Crawl the domain via Firecrawl API (or HTTP fallback). Respect robots.txt disallowed paths. Max 200 pages."
    subagent: "main agent"
    tools: ["firecrawl_crawl.py", "http_crawl_fallback.py"]
    inputs: "target_domain, max_pages, disallowed_paths"
    outputs: "raw_pages: [{url, title, content, status, discovered_from}]"
    failure_mode: "Firecrawl rate limited, timeout, or API error"
    fallback: "Retry with exponential backoff (3 attempts). If Firecrawl fails, fall back to HTTP crawl (loses JS content but maintains basic functionality). If < 5 pages retrieved, open GitHub Issue but continue with partial data."

  - name: "Build inventory"
    description: "Normalize URLs, extract canonical links, compute content hashes, detect duplicate clusters"
    subagent: "main agent"
    tools: ["build_inventory.py"]
    inputs: "raw_pages"
    outputs: "inventory.json: [{url, canonical_url, title, discovered_from, http_status, content_hash, dedup_cluster_id, notes}]"
    failure_mode: "Parsing error on malformed URLs or canonical tags"
    fallback: "Use original URL as canonical, log warning, continue"

  - name: "Rank pages"
    description: "Score pages by relevance using path keywords, titles, and lightweight semantic analysis"
    subagent: "relevance-ranker-specialist"
    tools: ["rank_pages.py"]
    inputs: "inventory.json"
    outputs: "ranked_pages.json: [{url, canonical_url, rank, reasons: [list], category}]"
    failure_mode: "Scoring algorithm error or missing required fields"
    fallback: "Assign default score based on path only, log warning, continue"

  - name: "Deep extract (Agent Teams)"
    description: "Extract structured data from top K ranked pages in parallel using Agent Teams"
    subagent: "deep-extract-specialist (team lead coordinates K teammates)"
    tools: ["deep_extract_page.py"]
    inputs: "ranked_pages.json (top K pages)"
    outputs: "deep_extract.json: {pages: [{url, title, summary, extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints}]}"
    failure_mode: "Agent Teams coordination failure, timeout, or LLM API error"
    fallback: "Fall back to sequential extraction (slower but reliable). If < 5 pages extracted, open GitHub Issue but commit partial results."

  - name: "Synthesize and validate"
    description: "Build final intelligence pack with synthesized findings, evidence index, and schema validation"
    subagent: "synthesis-validator-specialist"
    tools: ["synthesize_findings.py", "validate_schema.py", "generate_readme.py"]
    inputs: "inventory.json, ranked_pages.json, deep_extract.json"
    outputs: "site_intelligence_pack.json, README.md"
    failure_mode: "Schema validation failure or evidence mapping error"
    fallback: "Log validation errors, commit output with warnings, open GitHub Issue for manual review"

  - name: "Commit outputs"
    description: "Commit all JSON files and README to outputs/{domain}/{timestamp}/"
    subagent: "main agent"
    tools: ["git_commit_push.py"]
    inputs: "All JSON files, README.md, output_dir"
    outputs: "Git commit SHA, committed files list"
    failure_mode: "Git push failure or merge conflict"
    fallback: "Retry with rebase (3 attempts). If fails, log error and open GitHub Issue with outputs attached."

  - name: "Report status"
    description: "If critical failure (< 5 pages extracted), create GitHub Issue with diagnostics"
    subagent: "main agent"
    tools: ["github_create_issue.py"]
    inputs: "run_metadata, error logs"
    outputs: "GitHub Issue URL (if created)"
    failure_mode: "GitHub API error"
    fallback: "Log error to workflow logs, continue"
```

### Tool Specifications

```yaml
tools:
  - name: "fetch_robots.py"
    purpose: "Fetch and parse robots.txt for a domain"
    catalog_pattern: "rest_client (HTTP GET)"
    inputs:
      - "domain: str — Domain to fetch robots.txt from (e.g., example.com)"
    outputs: |
      JSON: {
        "fetched_url": "https://example.com/robots.txt",
        "allowed_summary": "All paths allowed except /admin",
        "disallowed_summary": "/admin, /private",
        "disallowed_paths": ["/admin", "/private"],
        "raw_excerpt": "User-agent: *\nDisallow: /admin"
      }
    dependencies: ["httpx"]
    mcp_used: "Fetch MCP (optional)"
    error_handling: "Return empty disallowed_paths list if 404 or timeout. Log warning."

  - name: "firecrawl_crawl.py"
    purpose: "Crawl a domain via Firecrawl API, respecting robots.txt and rate limits"
    catalog_pattern: "firecrawl_scrape (crawl mode)"
    inputs:
      - "domain: str — Domain to crawl"
      - "max_pages: int — Maximum pages to crawl (default 200)"
      - "disallowed_paths: list[str] — Paths to skip from robots.txt"
    outputs: |
      JSON: [
        {
          "url": "https://example.com/page",
          "title": "Page Title",
          "content": "markdown content...",
          "status": 200,
          "discovered_from": "sitemap"
        }
      ]
    dependencies: ["httpx", "firecrawl-py"]
    mcp_used: "Firecrawl"
    error_handling: "Retry with exponential backoff (3 attempts, 2s/4s/8s). Log error and return partial results. Raise exception if 0 pages returned."

  - name: "http_crawl_fallback.py"
    purpose: "Fallback crawler using direct HTTP requests (no JS rendering)"
    catalog_pattern: "rest_client + BeautifulSoup"
    inputs:
      - "domain: str — Domain to crawl"
      - "max_pages: int — Maximum pages to crawl"
      - "disallowed_paths: list[str] — Paths to skip"
    outputs: "Same format as firecrawl_crawl.py (list of page dicts)"
    dependencies: ["httpx", "beautifulsoup4"]
    mcp_used: "none"
    error_handling: "Skip pages that return 4xx/5xx errors. Log skipped URLs. Return partial results."

  - name: "build_inventory.py"
    purpose: "Normalize URLs, detect canonical links, compute content hashes, identify duplicate clusters"
    catalog_pattern: "transform_map + dedup"
    inputs:
      - "raw_pages: list[dict] — Raw pages from crawler"
    outputs: |
      JSON: [
        {
          "url": "https://example.com/page",
          "canonical_url": "https://example.com/page",
          "title": "Page Title",
          "discovered_from": "sitemap",
          "http_status": 200,
          "content_hash": "sha256:abc123...",
          "dedup_cluster_id": "cluster_001",
          "notes": null
        }
      ]
    dependencies: ["hashlib (stdlib)", "urllib.parse (stdlib)"]
    mcp_used: "none"
    error_handling: "If canonical link is malformed, use original URL. Log warning. Continue."

  - name: "rank_pages.py"
    purpose: "Score pages by relevance using path keywords, titles, and semantic analysis"
    catalog_pattern: "filter_sort + custom scoring logic"
    inputs:
      - "inventory: list[dict] — All discovered pages"
    outputs: |
      JSON: [
        {
          "url": "https://example.com/pricing",
          "canonical_url": "https://example.com/pricing",
          "rank": 1,
          "reasons": ["Path contains 'pricing'", "Title: 'Pricing Plans'"],
          "category": "offers_and_pricing"
        }
      ]
    dependencies: ["re (stdlib)"]
    mcp_used: "none"
    error_handling: "If scoring fails for a page, assign default score (50). Log warning. Continue."

  - name: "deep_extract_page.py"
    purpose: "Extract structured business data from a single page with evidence tracking"
    catalog_pattern: "structured_extract (LLM with JSON schema)"
    inputs:
      - "url: str — Page URL to extract"
      - "content: str — Page content (markdown or HTML)"
    outputs: |
      JSON: {
        "url": "https://example.com/pricing",
        "canonical_url": "https://example.com/pricing",
        "title": "Pricing Plans",
        "summary": "Three tiers: Starter, Pro, Enterprise",
        "extracted_entities": {
          "company_name": "Example Inc",
          "product_names": ["Example Pro", "Example Enterprise"],
          "audience": "SMB e-commerce merchants",
          "locations": ["USA", "UK"],
          "contact_points": ["support@example.com"]
        },
        "offers": [
          {
            "name": "Pro Plan",
            "description": "Full-featured plan for growing teams",
            "price": "$99/month",
            "billing_terms": "Annual billing available at 20% discount",
            "guarantees": "30-day money-back guarantee",
            "evidence": ["EV_001", "EV_002"]
          }
        ],
        "pricing": {
          "model": "Tiered subscription",
          "tiers": [
            {"name": "Starter", "price": "$29/mo"},
            {"name": "Pro", "price": "$99/mo"}
          ],
          "add_ons": [],
          "evidence": ["EV_003"]
        },
        "how_it_works": {
          "steps": ["Sign up", "Connect your store", "View analytics"],
          "evidence": ["EV_004"]
        },
        "faq": [
          {
            "q": "What payment methods do you accept?",
            "a": "Credit card, PayPal, and bank transfer",
            "evidence": ["EV_005"]
          }
        ],
        "testimonials": [
          {
            "quote": "Best analytics tool we've used",
            "name": "John Doe",
            "source_context": "CEO at ShopCo",
            "evidence": ["EV_006"]
          }
        ],
        "policies": {
          "privacy": "GDPR compliant",
          "terms": "Standard SaaS terms",
          "refunds": "30-day money-back",
          "shipping": "N/A (digital product)",
          "cancellations": "Anytime, no penalty",
          "evidence": ["EV_007", "EV_008"]
        },
        "constraints": {
          "requires_login": false,
          "blocked_by_robots": false
        }
      }
    dependencies: ["anthropic"]
    mcp_used: "Anthropic (Claude)"
    error_handling: "If LLM extraction fails after 3 retries, return empty structure with error note. Log error. Continue."

  - name: "synthesize_findings.py"
    purpose: "Build final intelligence pack with synthesized findings and evidence index"
    catalog_pattern: "llm_prompt + structured output"
    inputs:
      - "inventory: list[dict]"
      - "ranked_pages: list[dict]"
      - "deep_extract: dict"
    outputs: |
      JSON: {
        "site": {...},
        "inventory": [...],
        "ranked_pages": [...],
        "deep_extract_notes": {...},
        "synthesized_findings": {
          "positioning": {
            "claims": [
              {
                "id": "POS_001",
                "claim": "Targets SMB e-commerce merchants",
                "evidence": ["EV_015", "EV_022"]
              }
            ]
          },
          "offers_and_pricing": {...},
          "customer_journey": {...},
          "trust_signals": {...},
          "compliance_and_policies": {...},
          "unknowns_and_gaps": [...]
        },
        "evidence_index": {
          "EV_001": {
            "url": "https://example.com/pricing",
            "excerpt": "Pro Plan: $99/month with unlimited users",
            "page_title": "Pricing Plans",
            "extracted_at_iso": "2026-02-14T14:35:12Z"
          }
        },
        "run_metadata": {
          "max_pages": 200,
          "pages_crawled": 187,
          "pages_extracted": 15,
          "dedup_clusters": 23,
          "blocked_count": 5,
          "inaccessible_count": 3,
          "errors": []
        }
      }
    dependencies: ["anthropic"]
    mcp_used: "Anthropic (Claude)"
    error_handling: "If synthesis fails, return deep_extract data directly with error note. Log error."

  - name: "validate_schema.py"
    purpose: "Validate final JSON output against JSON Schema"
    catalog_pattern: "custom validation logic"
    inputs:
      - "data: dict — site_intelligence_pack JSON"
      - "schema: dict — JSON Schema definition"
    outputs: |
      JSON: {
        "valid": true,
        "errors": []
      }
    dependencies: ["jsonschema"]
    mcp_used: "none"
    error_handling: "Log validation errors. Do not halt execution. Return error list for review."

  - name: "generate_readme.py"
    purpose: "Generate human-readable README.md summary"
    catalog_pattern: "llm_prompt (summarization)"
    inputs:
      - "site_intelligence_pack: dict"
    outputs: "Markdown string"
    dependencies: ["anthropic"]
    mcp_used: "Anthropic (Claude)"
    error_handling: "If LLM summarization fails, generate minimal README with metadata only."

  - name: "github_create_issue.py"
    purpose: "Create GitHub Issue on critical failure"
    catalog_pattern: "github_create_issue"
    inputs:
      - "repo: str — Repository (owner/repo)"
      - "title: str — Issue title"
      - "body: str — Issue body with diagnostics"
      - "labels: list[str] — Issue labels"
    outputs: |
      JSON: {
        "issue_number": 123,
        "url": "https://github.com/owner/repo/issues/123"
      }
    dependencies: ["httpx"]
    mcp_used: "GitHub MCP"
    error_handling: "Log error if issue creation fails. Do not halt execution."

  - name: "git_commit_push.py"
    purpose: "Stage, commit, and push output files to repo"
    catalog_pattern: "git_commit_push"
    inputs:
      - "files: list[str] — Files to commit"
      - "message: str — Commit message"
      - "branch: str — Target branch (default: main)"
    outputs: |
      JSON: {
        "commit_sha": "abc123...",
        "branch": "main",
        "pushed": true
      }
    dependencies: ["subprocess (stdlib)"]
    mcp_used: "Git MCP (optional)"
    error_handling: "Retry with rebase on push failure (3 attempts). Log error if all retries fail."
```

### Per-Tool Pseudocode

```python
# fetch_robots.py
def main(domain: str) -> dict:
    """Fetch and parse robots.txt for a domain."""
    # PATTERN: REST client with fallback
    # CRITICAL: Handle 404 gracefully — many sites don't have robots.txt
    import httpx
    
    url = f"https://{domain}/robots.txt"
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        if resp.status_code == 404:
            return {
                "fetched_url": url,
                "allowed_summary": "All paths allowed (no robots.txt)",
                "disallowed_summary": "None",
                "disallowed_paths": [],
                "raw_excerpt": ""
            }
        resp.raise_for_status()
        raw_text = resp.text
        
        # Parse User-agent: * rules
        disallowed = []
        for line in raw_text.splitlines():
            if line.strip().startswith("Disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallowed.append(path)
        
        return {
            "fetched_url": url,
            "allowed_summary": "All paths allowed" if not disallowed else "Restricted paths found",
            "disallowed_summary": ", ".join(disallowed) if disallowed else "None",
            "disallowed_paths": disallowed,
            "raw_excerpt": raw_text[:500]
        }
    except Exception as e:
        logging.warning(f"Failed to fetch robots.txt: {e}")
        return {
            "fetched_url": url,
            "allowed_summary": "All paths allowed (fetch failed)",
            "disallowed_summary": "Unknown",
            "disallowed_paths": [],
            "raw_excerpt": ""
        }

# firecrawl_crawl.py
def main(domain: str, max_pages: int = 200, disallowed_paths: list[str] = []) -> list[dict]:
    """Crawl a domain via Firecrawl API with robots.txt compliance."""
    # PATTERN: firecrawl_scrape (crawl mode)
    # CRITICAL: Firecrawl can take 60-300s for large sites — set timeout to 600s
    # CRITICAL: Enforce max_concurrency=5 to avoid Firecrawl rate limits
    import os
    from firecrawl import FirecrawlApp
    from tenacity import retry, stop_after_attempt, wait_exponential
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8))
    def _crawl():
        app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
        result = app.crawl_url(
            f"https://{domain}",
            params={
                "limit": max_pages,
                "scrapeOptions": {"formats": ["markdown"]},
                "allowBackwardCrawling": False,
                "maxDepth": 5
            }
        )
        return result.get("data", [])
    
    try:
        pages = _crawl()
    except Exception as e:
        logging.error(f"Firecrawl crawl failed: {e}")
        raise  # Trigger fallback in workflow
    
    # Filter out robots.txt disallowed paths
    filtered_pages = []
    for page in pages:
        url_path = urlparse(page["url"]).path
        if any(url_path.startswith(dis) for dis in disallowed_paths):
            logging.info(f"Skipping disallowed path: {page['url']}")
            continue
        filtered_pages.append({
            "url": page["url"],
            "title": page.get("metadata", {}).get("title", ""),
            "content": page.get("markdown", ""),
            "status": page.get("statusCode", 200),
            "discovered_from": "crawl"
        })
    
    return filtered_pages

# deep_extract_page.py
def main(url: str, content: str) -> dict:
    """Extract structured data from a page with evidence tracking."""
    # PATTERN: structured_extract (LLM with JSON schema)
    # CRITICAL: Evidence excerpts must be 50-150 chars and directly quoted from content
    import os, json
    from anthropic import Anthropic
    
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "extracted_entities": {"type": "object"},
            "offers": {"type": "array"},
            "pricing": {"type": "object"},
            # ... (full schema)
        },
        "required": ["summary"]
    }
    
    system_prompt = f"""
    Extract structured business intelligence from the page content.
    
    CRITICAL RULES:
    1. Every extracted field MUST have an "evidence" list with evidence IDs
    2. Generate evidence IDs as EV_001, EV_002, etc.
    3. Evidence excerpts MUST be 50-150 chars, directly quoted from content
    4. If a field is not found, omit it or set to null (do not guess)
    5. Mark pages requiring login or blocked by robots.txt in "constraints"
    
    Return ONLY valid JSON matching this schema:
    {json.dumps(schema, indent=2)}
    """
    
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": f"URL: {url}\n\nContent:\n{content[:50000]}"}]
        )
        
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        parsed = json.loads(raw)
        parsed["url"] = url
        return parsed
        
    except Exception as e:
        logging.error(f"Extraction failed for {url}: {e}")
        return {
            "url": url,
            "summary": f"Extraction failed: {e}",
            "constraints": {"requires_login": False, "blocked_by_robots": False}
        }
```

### Integration Points

```yaml
SECRETS:
  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API authentication for crawling/scraping"
    required: true

  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API for structured data extraction and synthesis"
    required: true

  - name: "GITHUB_TOKEN"
    purpose: "GitHub API for issue creation and commits"
    required: true

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "FIRECRAWL_API_KEY=your_firecrawl_api_key_here  # Get from firecrawl.dev"
      - "ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Get from console.anthropic.com"
      - "GITHUB_TOKEN=your_github_token_here  # Personal Access Token with repo scope"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "firecrawl-py>=1.0.0  # Firecrawl API client"
      - "anthropic>=0.40.0  # Claude API client"
      - "httpx>=0.27.0  # HTTP client with retry support"
      - "beautifulsoup4>=4.12.0  # HTML parsing (fallback)"
      - "jsonschema>=4.20.0  # JSON Schema validation"
      - "tenacity>=8.2.0  # Retry logic"
      - "python-dateutil>=2.8.0  # Date parsing"

GITHUB_ACTIONS:
  - trigger: "workflow_dispatch"
    config: |
      name: Site Intelligence Pack
      on:
        workflow_dispatch:
          inputs:
            target_domain:
              description: 'Domain to analyze (e.g., stripe.com)'
              required: true
            max_pages:
              description: 'Maximum pages to crawl'
              required: false
              default: '200'
            deep_extract_count:
              description: 'Number of top pages to deep-extract'
              required: false
              default: '15'
            batch_mode:
              description: 'Process all domains in inputs/targets.csv'
              required: false
              default: 'false'
        schedule:
          - cron: '0 2 * * *'  # Daily at 2 AM UTC
      
      jobs:
        build-intelligence-pack:
          runs-on: ubuntu-latest
          timeout-minutes: 60
          steps:
            - uses: actions/checkout@v4
            - uses: actions/setup-python@v5
              with:
                python-version: '3.12'
            - run: pip install -r requirements.txt
            - run: python workflow.py
              env:
                FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
                ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
                GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
                TARGET_DOMAIN: ${{ github.event.inputs.target_domain }}
                MAX_PAGES: ${{ github.event.inputs.max_pages }}
                DEEP_EXTRACT_COUNT: ${{ github.event.inputs.deep_extract_count }}
                BATCH_MODE: ${{ github.event.inputs.batch_mode }}
            - run: |
                git config user.name "GitHub Actions"
                git config user.email "actions@github.com"
                git add outputs/
                git commit -m "Add Site Intelligence Pack for ${{ github.event.inputs.target_domain }}"
                git push
```

---

## Validation Loop

### Level 1: Syntax & Structure

```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/fetch_robots.py').read())"
python -c "import ast; ast.parse(open('tools/firecrawl_crawl.py').read())"
python -c "import ast; ast.parse(open('tools/build_inventory.py').read())"
python -c "import ast; ast.parse(open('tools/rank_pages.py').read())"
python -c "import ast; ast.parse(open('tools/deep_extract_page.py').read())"
python -c "import ast; ast.parse(open('tools/synthesize_findings.py').read())"
python -c "import ast; ast.parse(open('tools/validate_schema.py').read())"
python -c "import ast; ast.parse(open('tools/generate_readme.py').read())"
python -c "import ast; ast.parse(open('tools/github_create_issue.py').read())"

# Import check — verify no missing dependencies
python -c "from tools import fetch_robots"
python -c "from tools import firecrawl_crawl"
python -c "from tools import build_inventory"
python -c "from tools import rank_pages"
python -c "from tools import deep_extract_page"
python -c "from tools import synthesize_findings"
python -c "from tools import validate_schema"
python -c "from tools import generate_readme"
python -c "from tools import github_create_issue"

# Structure check — verify main() exists in each tool
python -c "from tools.fetch_robots import main; assert callable(main)"
python -c "from tools.firecrawl_crawl import main; assert callable(main)"
python -c "from tools.build_inventory import main; assert callable(main)"
python -c "from tools.rank_pages import main; assert callable(main)"
python -c "from tools.deep_extract_page import main; assert callable(main)"
python -c "from tools.synthesize_findings import main; assert callable(main)"
python -c "from tools.validate_schema import main; assert callable(main)"
python -c "from tools.generate_readme import main; assert callable(main)"
python -c "from tools.github_create_issue import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests

```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test fetch_robots.py with a known domain
python tools/fetch_robots.py --domain example.com > /tmp/robots_test.json
python -c "
import json
data = json.load(open('/tmp/robots_test.json'))
assert 'fetched_url' in data, 'Missing fetched_url'
assert 'disallowed_paths' in data, 'Missing disallowed_paths'
print('✓ fetch_robots.py unit test passed')
"

# Test build_inventory.py with sample data
echo '[{"url": "https://example.com/page1", "content": "test content"}]' > /tmp/raw_pages.json
python tools/build_inventory.py --input /tmp/raw_pages.json > /tmp/inventory_test.json
python -c "
import json
data = json.load(open('/tmp/inventory_test.json'))
assert len(data) == 1, 'Expected 1 inventory item'
assert 'canonical_url' in data[0], 'Missing canonical_url'
assert 'content_hash' in data[0], 'Missing content_hash'
print('✓ build_inventory.py unit test passed')
"

# Test rank_pages.py with sample inventory
python tools/rank_pages.py --input /tmp/inventory_test.json > /tmp/ranked_test.json
python -c "
import json
data = json.load(open('/tmp/ranked_test.json'))
assert len(data) == 1, 'Expected 1 ranked page'
assert 'rank' in data[0], 'Missing rank'
assert 'category' in data[0], 'Missing category'
print('✓ rank_pages.py unit test passed')
"

# Test validate_schema.py with sample pack
echo '{"site": {"domain": "example.com"}, "inventory": [], "ranked_pages": []}' > /tmp/sample_pack.json
python tools/validate_schema.py --input /tmp/sample_pack.json --schema tools/schema.json > /tmp/validation_test.json
python -c "
import json
data = json.load(open('/tmp/validation_test.json'))
assert 'valid' in data, 'Missing valid field'
print('✓ validate_schema.py unit test passed')
"

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests

```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with a sample domain (use a small, fast site)

# Step 1: Fetch robots.txt
python tools/fetch_robots.py --domain example.com > /tmp/robots.json
echo "✓ Step 1: robots.txt fetched"

# Step 2: Crawl site (mock with a single page to avoid external dependencies)
echo '[{"url": "https://example.com/pricing", "title": "Pricing", "content": "Our plans start at $10/month", "status": 200, "discovered_from": "mock"}]' > /tmp/crawl_result.json
echo "✓ Step 2: crawl completed (mocked)"

# Step 3: Build inventory
python tools/build_inventory.py --input /tmp/crawl_result.json > /tmp/inventory.json
echo "✓ Step 3: inventory built"

# Step 4: Rank pages
python tools/rank_pages.py --input /tmp/inventory.json > /tmp/ranked.json
echo "✓ Step 4: pages ranked"

# Step 5: Deep extract (mock LLM call to avoid API cost)
echo '{"url": "https://example.com/pricing", "summary": "Three pricing tiers", "offers": [{"name": "Basic", "price": "$10/mo", "evidence": ["EV_001"]}]}' > /tmp/deep_extract.json
echo "✓ Step 5: deep extraction completed (mocked)"

# Step 6: Synthesize (mock LLM call)
echo '{"site": {"domain": "example.com"}, "synthesized_findings": {"positioning": {"claims": []}}, "evidence_index": {"EV_001": {"url": "https://example.com/pricing", "excerpt": "Plans start at $10/month"}}}' > /tmp/site_pack.json
echo "✓ Step 6: synthesis completed (mocked)"

# Step 7: Validate schema
python tools/validate_schema.py --input /tmp/site_pack.json --schema tools/schema.json > /tmp/validation.json
python -c "
import json
data = json.load(open('/tmp/validation.json'))
assert data['valid'] == True, 'Schema validation failed'
print('✓ Step 7: schema validation passed')
"

# Verify workflow.md references match actual tool files
grep -q "fetch_robots.py" workflow.md || (echo "✗ workflow.md missing fetch_robots.py reference" && exit 1)
grep -q "firecrawl_crawl.py" workflow.md || (echo "✗ workflow.md missing firecrawl_crawl.py reference" && exit 1)
grep -q "deep_extract_page.py" workflow.md || (echo "✗ workflow.md missing deep_extract_page.py reference" && exit 1)
echo "✓ workflow.md references verified"

# Verify CLAUDE.md documents all tools and subagents
grep -q "relevance-ranker-specialist" CLAUDE.md || (echo "✗ CLAUDE.md missing relevance-ranker-specialist" && exit 1)
grep -q "deep-extract-specialist" CLAUDE.md || (echo "✗ CLAUDE.md missing deep-extract-specialist" && exit 1)
grep -q "synthesis-validator-specialist" CLAUDE.md || (echo "✗ CLAUDE.md missing synthesis-validator-specialist" && exit 1)
echo "✓ CLAUDE.md subagent documentation verified"

# Verify .github/workflows/ YAML is valid
python -c "
import yaml
with open('.github/workflows/site-intelligence-pack.yml') as f:
    yaml.safe_load(f)
print('✓ GitHub Actions workflow YAML is valid')
"

echo ""
echo "========================================="
echo "✓ All integration tests passed"
echo "========================================="
```

---

## Final Validation Checklist

- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes (60) and failure notifications
- [ ] .env.example lists all required environment variables (FIRECRAWL_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN)
- [ ] .gitignore excludes .env, __pycache__/, outputs/ (except committed results)
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies with pinned versions
- [ ] JSON Schema file (tools/schema.json) defines complete site_intelligence_pack structure
- [ ] Evidence tracking verified: all claims in synthesized_findings reference evidence IDs
- [ ] robots.txt compliance verified: disallowed paths are filtered from crawl results
- [ ] Rate limiting verified: max 1-2 req/sec enforced with delays between requests
- [ ] De-duplication verified: canonical URLs used, content hashes computed, clusters assigned
- [ ] Failure recovery verified: GitHub Issue created when < 5 pages extracted

---

## Anti-Patterns to Avoid

- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only outputs/ directory
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks — Firecrawl failure must not halt the system
- Do not design subagents that call other subagents — only the main agent delegates
- Do not use Agent Teams when fewer than 3 independent tasks exist — overhead is not justified
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not extract data without evidence tracking — every claim needs quoted evidence
- Do not ignore robots.txt — always fetch first and filter disallowed paths
- Do not crawl without rate limiting — enforce 1-2 req/sec maximum
- Do not skip de-duplication — canonical URLs and content hashing are required
- Do not commit outputs without validation — run schema validation before committing
- Do not let a single page failure halt the entire workflow — isolate errors and continue
- Do not generate evidence excerpts longer than 150 chars — keep them readable
- Do not create evidence IDs without a mapping in evidence_index — every ID must be resolvable

---

## Confidence Score: 8/10

**Score rationale:**

- **Firecrawl integration**: High confidence. Firecrawl API is well-documented, and fallback to HTTP scraping is straightforward. Confidence: **high**
- **LLM-based extraction**: Medium-high confidence. Structured extraction with JSON schema is proven, but quality depends on prompt engineering. Evidence tracking adds complexity but is manageable with clear instructions. Confidence: **medium-high**
- **robots.txt compliance**: High confidence. Parsing robots.txt is straightforward, and filtering logic is simple. Confidence: **high**
- **Rate limiting**: High confidence. Simple sleep-based rate limiting is reliable and easy to implement. Confidence: **high**
- **Agent Teams parallelization**: Medium confidence. Parallel extraction is ideal for Agent Teams, but coordination overhead may introduce edge cases. Sequential fallback is critical. Confidence: **medium**
- **Evidence tracking**: Medium confidence. Mapping every claim to evidence is conceptually clear but requires careful LLM prompt design and validation. Risk of missing evidence IDs if LLM doesn't follow instructions perfectly. Confidence: **medium**
- **De-duplication**: High confidence. Canonical URL extraction and content hashing are standard techniques. Confidence: **high**
- **Schema validation**: High confidence. JSON Schema validation is straightforward with `jsonschema` library. Confidence: **high**
- **GitHub Issue creation on failure**: High confidence. Simple GitHub API call with clear failure thresholds. Confidence: **high**

**Ambiguity flags** (areas requiring clarification before building):

- [ ] **Deep extract count (K)**: Default is 15, but optimal value depends on site size. Should this be auto-adjusted based on total page count? (e.g., top 10% of pages up to max 20)
- [ ] **Evidence excerpt length**: Spec says 50-150 chars. Should this be enforced strictly (truncate), or is it a guideline for the LLM?
- [ ] **Batch mode behavior**: If one domain fails in batch mode, should the workflow continue with remaining domains or halt? (Recommendation: continue and report failures)
- [ ] **De-duplication strategy**: Should duplicate pages be completely removed from inventory, or kept with a cluster ID for reference? (Recommendation: keep with cluster ID)
- [ ] **Rate limiting implementation**: Should rate limiting be per-domain or global across batch processing? (Recommendation: per-domain to maximize throughput)

**Resolution**: These ambiguities are minor and can be resolved with reasonable defaults during build. No blocker to proceeding.

**If any ambiguity flag above is critical, DO NOT proceed to build. Ask the user to clarify first.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/site-intelligence-pack.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
