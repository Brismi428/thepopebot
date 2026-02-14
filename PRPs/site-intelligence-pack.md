name: "Site Intelligence Pack"
description: |
  Comprehensive website analysis system with three specialist components for analyzing websites and producing evidence-backed business intelligence reports.

## Purpose
Build a GitHub-native, automated website intelligence gathering system that analyzes target domains through a three-phase pipeline: (1) crawl and inventory discovery, (2) intelligent page ranking and prioritization, (3) deep extraction of structured business data, and (4) synthesis into an evidence-backed intelligence pack. The system must respect robots.txt, handle failures gracefully, and produce auditable, citation-backed reports suitable for competitive analysis, market research, and lead qualification.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a fully autonomous website intelligence system that accepts a domain (or batch CSV of domains), crawls and analyzes the site, extracts structured business intelligence, and produces a comprehensive JSON intelligence pack with a human-readable summary report — all committed to the repository with full evidence provenance and compliance with robots.txt.

Success looks like: A user opens a GitHub Issue with "Analyze example.com", and 5-10 minutes later a PR is opened with a complete intelligence pack (JSON + README) containing ranked pages, extracted offers/pricing/policies, and synthesized business insights — every claim backed by URL + excerpt citations.

## Why
- **Business value**: Enables competitive intelligence, lead qualification, and market research at scale without manual research teams
- **User impact**: Converts hours of manual website research into minutes of automated analysis
- **Automation gap**: Eliminates manual website reading, note-taking, and data extraction for business intelligence
- **Who benefits**: Sales teams (lead qualification), product teams (competitive analysis), research teams (market intelligence) — used on-demand or nightly batch
- **Frequency**: On-demand (workflow_dispatch) for ad-hoc research; optional nightly scheduled batch for ongoing monitoring

## What
From the perspective of someone triggering the system:

**Single domain mode (workflow_dispatch)**:
1. User provides a domain (e.g., `example.com`)
2. System crawls the site (respecting robots.txt), discovers pages, and builds an inventory
3. System ranks pages by relevance (heuristics + semantic scoring)
4. System deep-extracts top K pages for structured data (offers, pricing, policies, etc.)
5. System synthesizes findings into a structured intelligence pack with evidence index
6. System validates that all claims have supporting evidence (url + excerpt)
7. System commits output files (JSON + README) to `outputs/{domain}/`
8. System opens a PR or commits directly (based on AUTO_MERGE setting)

**Batch mode (scheduled or workflow_dispatch with CSV)**:
1. System reads `inputs/targets.csv` (columns: `domain`, optional `priority`)
2. System processes each domain sequentially (to respect rate limits)
3. System outputs one intelligence pack per domain to `outputs/{domain}/`
4. System commits all outputs in a single commit with summary

**Failure modes handled**:
- Robots.txt disallows crawling → skip crawl, report robots.txt excerpt in output
- Pages require login/paywall → mark as inaccessible with reason, continue with accessible pages
- Firecrawl fails → fallback to direct HTTP + BeautifulSoup
- Fewer than 5 pages extracted → open GitHub Issue with failure summary, still commit partial output
- Rate limit hit → pause, wait, retry with exponential backoff

### Success Criteria
- [x] System accepts single domain via workflow_dispatch input or batch CSV from `inputs/targets.csv`
- [x] System respects robots.txt: fetches robots.txt first, skips disallowed paths, includes robots summary in output
- [x] System crawls up to 200 pages per site (default), discovers key pages (home, about, pricing, faq, contact, policies, terms, blog)
- [x] System ranks pages by relevance using heuristics (path keywords) + lightweight semantic scoring (titles/headings/first N chars)
- [x] System deep-extracts top K pages (default 10) for structured fields: offers, pricing, guarantees, process steps, FAQs, contact methods, policies, testimonials
- [x] System synthesizes findings into structured JSON: positioning, offers_and_pricing, customer_journey, trust_signals, compliance_and_policies, unknowns_and_gaps
- [x] System validates evidence: every claim in synthesized_findings must have evidence_index entry with url + excerpt + extracted_at + page_title
- [x] System de-duplicates URLs: canonicalize URLs (strip utm params, normalize trailing slashes, lowercase host), cluster near-identical pages
- [x] System rate-limits: ~1-2 req/sec, stops early on repeated errors
- [x] System commits outputs to repo: `outputs/{domain}/inventory.json`, `ranked_pages.json`, `deep_extract.json`, `site_intelligence_pack.json`, `README.md` (run report)
- [x] System runs autonomously via GitHub Actions on schedule (optional nightly batch) or workflow_dispatch (single domain)
- [x] All three execution paths work: CLI (local testing), GitHub Actions (production), Agent HQ (issue-driven)
- [x] System opens GitHub Issue on major failures (fewer than 5 pages extracted) with failure summary and still commits partial output
- [x] System handles fallback: Firecrawl failure → HTTP + BeautifulSoup; still blocked → produce partial pack with "inaccessible" section

---

## Inputs

```yaml
- name: "domain"
  type: "string"
  source: "workflow_dispatch input OR first column of inputs/targets.csv"
  required: true (for single-domain mode)
  description: "Target domain to analyze (without protocol). Examples: example.com, www.example.com"
  example: "stripe.com"

- name: "batch_csv_path"
  type: "string (file path)"
  source: "workflow_dispatch input OR default to inputs/targets.csv"
  required: false (for batch mode)
  description: "Path to CSV file containing batch targets. Columns: domain (required), priority (optional)"
  example: "inputs/targets.csv"

- name: "max_pages"
  type: "integer"
  source: "workflow_dispatch input OR environment variable"
  required: false
  description: "Maximum pages to crawl per site (default: 200)"
  example: "200"

- name: "top_k_deep_extract"
  type: "integer"
  source: "workflow_dispatch input OR environment variable"
  required: false
  description: "Number of top-ranked pages to deep extract (default: 10)"
  example: "10"

- name: "rate_limit_rps"
  type: "float"
  source: "workflow_dispatch input OR environment variable"
  required: false
  description: "Rate limit in requests per second (default: 1.5)"
  example: "1.5"
```

## Outputs

```yaml
- name: "site_intelligence_pack.json"
  type: "JSON"
  destination: "repo commit at outputs/{domain}/site_intelligence_pack.json"
  description: "Complete intelligence pack with site info, inventory, ranked pages, deep extract notes, synthesized findings, evidence index, and run metadata"
  example: |
    {
      "site": {
        "target_url": "https://stripe.com",
        "domain": "stripe.com",
        "crawled_at_iso": "2026-02-14T14:30:00Z",
        "robots": {
          "fetched_url": "https://stripe.com/robots.txt",
          "allowed_summary": "Most paths allowed",
          "disallowed_summary": "Disallowed: /admin, /internal",
          "raw_excerpt": "User-agent: *\nDisallow: /admin"
        }
      },
      "inventory": [...],
      "ranked_pages": [...],
      "deep_extract_notes": {...},
      "synthesized_findings": {...},
      "evidence_index": {...},
      "run_metadata": {...}
    }

- name: "inventory.json"
  type: "JSON"
  destination: "repo commit at outputs/{domain}/inventory.json"
  description: "Full page inventory with URLs, titles, discovery info, HTTP status, content hashes, dedup clusters"
  example: "Array of {url, canonical_url, title, discovered_from, http_status, content_hash, dedup_cluster_id, notes}"

- name: "ranked_pages.json"
  type: "JSON"
  destination: "repo commit at outputs/{domain}/ranked_pages.json"
  description: "Pages ranked by relevance with scores, reasons, and categories"
  example: "Array of {url, canonical_url, rank, reasons: [string], category: string}"

- name: "deep_extract.json"
  type: "JSON"
  destination: "repo commit at outputs/{domain}/deep_extract.json"
  description: "Deep-extracted structured data from top K pages"
  example: "Object with pages array containing extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints"

- name: "README.md"
  type: "Markdown"
  destination: "repo commit at outputs/{domain}/README.md"
  description: "Human-readable run report with summary, key findings, robots compliance, and any issues encountered"
  example: "# Site Intelligence Pack: stripe.com\n\n## Summary\nCrawled 147 pages, ranked 147, deep-extracted 10..."
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building

- url: "https://docs.firecrawl.dev/api-reference/crawl"
  why: "Firecrawl crawl endpoint usage, parameters (limit, scrapeOptions), response structure"

- url: "https://docs.firecrawl.dev/api-reference/scrape"
  why: "Firecrawl scrape endpoint for single-page deep extraction, formats (markdown, html, structured)"

- doc: "config/mcp_registry.md"
  why: "Check Firecrawl MCP availability and capabilities"

- doc: "library/patterns.md"
  why: "Select the best workflow pattern for multi-phase website analysis pipeline"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns for web scraping, data extraction, and validation"

- url: "https://www.robotstxt.org/robotstxt.html"
  why: "robots.txt specification for parsing and compliance checking"

- url: "https://docs.python.org/3/library/urllib.parse.html"
  why: "URL parsing and canonicalization (urlparse, urlunparse, urljoin)"

- url: "https://docs.python.org/3/library/hashlib.html"
  why: "Content hashing for de-duplication (hashlib.md5 or sha256)"

- url: "https://github.com/anthropics/anthropic-sdk-python"
  why: "Claude API for semantic scoring and synthesis tasks"
```

### Workflow Pattern Selection
```yaml
# Reference library/patterns.md
pattern: "Scrape > Process > Output + Fan-Out > Process > Merge (for batch mode)"
rationale: |
  The system follows a multi-phase pipeline:
  1. Scrape (crawl + inventory) — Uses Firecrawl MCP to crawl domain and build page inventory
  2. Process (rank) — Applies heuristics and semantic scoring to rank pages by relevance
  3. Process (deep extract) — Deep-scrapes top K pages and extracts structured fields
  4. Process (synthesize + validate) — Merges extracts into intelligence pack with evidence validation
  5. Output — Commits JSON + README to repo

  For batch mode, we apply Fan-Out > Process > Merge pattern where each domain is an independent unit of work.
  However, to respect rate limits, batch processing is SEQUENTIAL by default (not parallel).
  Agent Teams is NOT recommended because tasks are NOT independent (sequential processing required for rate limits).

modifications: |
  - Add robots.txt pre-check before crawling
  - Add de-duplication step after inventory
  - Add evidence validation step after synthesis
  - Add fallback chain: Firecrawl → HTTP + BeautifulSoup → partial output with "inaccessible" section
  - Add GitHub Issue creation on major failures (fewer than 5 pages extracted)
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "web crawling and scraping"
    primary_mcp: "firecrawl"
    alternative_mcp: "puppeteer"
    fallback: "Direct HTTP with requests + beautifulsoup4 (no JS rendering)"
    secret_name: "FIRECRAWL_API_KEY"
    notes: "Firecrawl handles JS-rendered sites and returns clean markdown; fallback loses JS rendering but maintains basic scraping"

  - name: "LLM for semantic scoring and synthesis"
    primary_mcp: "anthropic"
    alternative_mcp: "none"
    fallback: "Heuristic-only ranking (no semantic component), synthesis via templates"
    secret_name: "ANTHROPIC_API_KEY"
    notes: "Used for lightweight semantic scoring on titles/headings and synthesis of findings; can run without LLM using heuristics only"

  - name: "GitHub issue creation on failure"
    primary_mcp: "github"
    alternative_mcp: "none"
    fallback: "gh CLI or direct GitHub REST API via requests"
    secret_name: "GITHUB_TOKEN"
    notes: "Used to open issues when fewer than 5 pages are extracted successfully"
```

### Known Gotchas & Constraints
```
# CRITICAL: Firecrawl API has rate limits — check response headers for X-RateLimit-* values
# CRITICAL: robots.txt MUST be fetched FIRST before any crawling — use requests.get(f"https://{domain}/robots.txt")
# CRITICAL: URL canonicalization is critical for de-duplication:
#   - Lowercase scheme and host (https://Example.com → https://example.com)
#   - Remove trailing slashes EXCEPT for domain root (example.com/ → example.com, example.com/page/ → example.com/page)
#   - Strip UTM params and tracking params (utm_*, fbclid, gclid, ref, etc.)
#   - Normalize path segments (remove /../, /./, etc.)
# CRITICAL: Content hashing for de-duplication — hash the visible text content (not HTML) to detect near-identical pages
# CRITICAL: Header/footer boilerplate appears on every page — must strip before hashing to avoid false duplicates
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: Evidence validation is MANDATORY — synthesized_findings must reference evidence_index entries
# CRITICAL: Rate limiting is MANDATORY — add delays between requests, respect 429 responses, implement exponential backoff
# CRITICAL: Page inventory must attempt discovery of: home, about, offers, pricing, faq, contact, policies, privacy, terms, blog
# CRITICAL: If fewer than 5 pages are extracted successfully, open a GitHub Issue with failure summary AND still commit partial output
# CRITICAL: Firecrawl crawl mode returns markdown — use this for inventory; Firecrawl scrape mode returns structured data — use for deep extract
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents:
  - name: "crawler-specialist"
    description: "Delegate when: Need to fetch robots.txt, crawl a domain, build page inventory, or handle crawl failures. This subagent handles all website fetching and inventory construction."
    tools: "Read, Bash, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Fetch and parse robots.txt from target domain"
      - "Crawl domain via Firecrawl API (or fallback to HTTP + BeautifulSoup)"
      - "Build page inventory with URLs, titles, discovered_from metadata"
      - "Check HTTP status codes and note accessibility issues"
      - "Handle crawl failures and implement fallback strategies"
      - "Respect robots.txt disallow rules and note compliance in output"
      - "Apply rate limiting (1-2 req/sec) and exponential backoff on errors"
    inputs: "domain string, max_pages integer, rate_limit_rps float"
    outputs: "inventory.json with array of {url, canonical_url, title, discovered_from, http_status, content_hash, notes}"

  - name: "relevance-ranker-specialist"
    description: "Delegate when: Need to rank pages by relevance, apply heuristics, or perform semantic scoring. This subagent prioritizes which pages are most valuable for deep extraction."
    tools: "Read, Bash, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Load inventory.json from crawler-specialist"
      - "Apply path-based heuristics (keywords like /pricing, /faq, /about, /terms)"
      - "Perform lightweight semantic scoring on titles, headings, first N chars (if ANTHROPIC_API_KEY available)"
      - "Assign relevance scores and categories (offers/pricing, policies, about, faq, contact, blog, other)"
      - "De-duplicate URLs (canonicalize, cluster near-identical pages, keep best representative)"
      - "Output ranked list with scores, reasons, and categories"
    inputs: "inventory.json from crawler-specialist"
    outputs: "ranked_pages.json with array of {url, canonical_url, rank, reasons: [string], category: string}"

  - name: "deep-extract-specialist"
    description: "Delegate when: Need to deep-scrape top K pages and extract structured business data. This subagent performs detailed content extraction with evidence capture."
    tools: "Read, Bash, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Load ranked_pages.json and select top K pages (default 10)"
      - "Deep-scrape each page via Firecrawl scrape endpoint (or fallback to HTTP + BeautifulSoup)"
      - "Extract structured fields: offers, pricing, guarantees, process_steps, faq, testimonials, contact_methods, policies, constraints"
      - "Capture quoted evidence for each extracted claim (url + excerpt + page_title + extracted_at)"
      - "Handle login/paywall pages gracefully (mark as inaccessible, log reason, continue)"
      - "Output deep_extract.json with pages array"
    inputs: "ranked_pages.json from relevance-ranker-specialist, top_k_deep_extract integer"
    outputs: "deep_extract.json with {pages: [{url, extracted_at, extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints}]}"

  - name: "synthesis-validator-specialist"
    description: "Delegate when: Need to synthesize findings into intelligence pack, validate evidence references, or run schema validation. This subagent produces the final deliverable."
    tools: "Read, Bash, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Load inventory.json, ranked_pages.json, deep_extract.json"
      - "Synthesize findings into structured JSON: positioning, offers_and_pricing, customer_journey, trust_signals, compliance_and_policies, unknowns_and_gaps"
      - "Build evidence_index mapping evidence_id to {url, excerpt, page_title, extracted_at_iso}"
      - "Validate that every claim in synthesized_findings has a reference in evidence_index"
      - "Run JSON schema validation on final site_intelligence_pack.json"
      - "Generate README.md (run report) with summary, key findings, robots compliance, issues encountered"
      - "Output final site_intelligence_pack.json and README.md"
      - "If fewer than 5 pages extracted, open GitHub Issue with failure summary and still commit partial output"
    inputs: "inventory.json, ranked_pages.json, deep_extract.json"
    outputs: "site_intelligence_pack.json (complete pack), README.md (human-readable report), optional GitHub Issue on major failure"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "None — all tasks have sequential dependencies"

independent_task_count: "0"
recommendation: "Sequential execution"
rationale: |
  The system has clear data dependencies between phases:
  1. Crawler must complete before ranker (ranker needs inventory)
  2. Ranker must complete before deep-extract (deep-extract needs ranked list)
  3. Deep-extract must complete before synthesis (synthesis needs extracted data)

  For batch mode (multiple domains), each domain is technically independent, but we MUST process sequentially
  to respect rate limits (1-2 req/sec across all domains). Parallel processing would violate rate limits and
  trigger API blocks.

  Therefore, Agent Teams is NOT recommended. Sequential execution is correct.

sequential_rationale: |
  All tasks depend on previous output (inventory → ranked → deep_extract → synthesis).
  Batch mode must be sequential to respect rate limits.
  No parallelization benefit without violating rate limits.
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "workflow_dispatch"
    config:
      inputs:
        domain:
          description: "Target domain to analyze (e.g., example.com)"
          required: false
        batch_csv_path:
          description: "Path to CSV file with batch targets (default: inputs/targets.csv)"
          required: false
          default: "inputs/targets.csv"
        max_pages:
          description: "Maximum pages to crawl per site"
          required: false
          default: "200"
        top_k_deep_extract:
          description: "Number of top-ranked pages to deep extract"
          required: false
          default: "10"
    description: "Manual trigger for single-domain analysis or batch mode (if domain is empty, batch mode is used)"

  - type: "schedule"
    config: "0 2 * * *  # Nightly at 2 AM UTC (optional — user can enable/disable)"
    description: "Optional nightly batch run — processes inputs/targets.csv for ongoing monitoring"

  - type: "issues"
    config: "opened with label 'site-analysis-request'"
    description: "Agent HQ integration — opening an issue with label 'site-analysis-request' and body containing 'domain: example.com' triggers analysis"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "Input Validation and Mode Detection"
    description: |
      Determine execution mode (single-domain or batch). Validate inputs.
      Single-domain mode: domain input is provided.
      Batch mode: domain input is empty, batch_csv_path points to CSV file.
    subagent: "none (main agent)"
    tools: []
    inputs: "domain (optional string), batch_csv_path (optional string)"
    outputs: "mode (single | batch), targets list (single domain or list from CSV)"
    failure_mode: "Invalid domain format, CSV file missing or malformed"
    fallback: "Halt with clear error message — invalid inputs cannot proceed"

  - name: "Robots.txt Fetch and Compliance Check"
    description: |
      For each target domain, fetch https://{domain}/robots.txt and parse.
      Identify disallowed paths for User-agent: *.
      Note compliance in run metadata.
    subagent: "crawler-specialist"
    tools: ["fetch_robots.py"]
    inputs: "domain string"
    outputs: "robots_info dict with {fetched_url, allowed_summary, disallowed_summary, raw_excerpt, disallowed_paths: [string]}"
    failure_mode: "robots.txt not found (404) or unreachable"
    fallback: "Assume all paths allowed (note in output: 'robots.txt not found, proceeding with caution')"

  - name: "Crawl and Inventory Discovery"
    description: |
      Crawl the domain via Firecrawl API (crawl mode) or fallback to HTTP + BeautifulSoup.
      Build page inventory with URLs, titles, discovered_from, HTTP status.
      Apply robots.txt disallow rules — skip disallowed paths.
      Enforce max_pages limit (default 200).
      Apply rate limiting (1-2 req/sec).
      Attempt discovery of key pages: home, about, offers, pricing, faq, contact, policies, privacy, terms, blog.
    subagent: "crawler-specialist"
    tools: ["crawl_domain.py"]
    inputs: "domain string, max_pages integer, rate_limit_rps float, robots_info dict (disallowed_paths)"
    outputs: "inventory.json with array of {url, canonical_url, title, discovered_from, http_status, content_hash, notes}"
    failure_mode: "Firecrawl API fails (rate limit, timeout, auth error)"
    fallback: "Switch to direct HTTP + BeautifulSoup for basic crawling (note loss of JS rendering in output)"

  - name: "URL Canonicalization and De-duplication"
    description: |
      For each page in inventory, canonicalize URL (lowercase host, strip utm params, normalize trailing slashes).
      Hash visible text content (strip HTML, remove header/footer boilerplate).
      Cluster pages with identical or near-identical content_hash.
      Keep best representative from each cluster (prefer shorter URLs, non-query-string URLs).
      Update inventory with canonical_url and dedup_cluster_id.
    subagent: "relevance-ranker-specialist"
    tools: ["deduplicate_urls.py"]
    inputs: "inventory.json from crawler-specialist"
    outputs: "inventory.json updated with canonical_url and dedup_cluster_id"
    failure_mode: "Content hashing error or malformed URL"
    fallback: "Skip de-duplication for problematic URLs, log warning, continue with duplicates"

  - name: "Page Relevance Ranking"
    description: |
      Load inventory.json (post-deduplication).
      Apply path-based heuristics: assign points for keywords in URL path (pricing=10, faq=8, about=7, contact=6, etc.).
      Apply lightweight semantic scoring: extract title, h1-h3 headings, first 500 chars from each page.
      Send to Claude for relevance scoring (0-10) based on business intelligence value (if ANTHROPIC_API_KEY available).
      Combine heuristic + semantic scores (weighted).
      Assign relevance category (offers/pricing, policies, about, faq, contact, blog, other).
      Sort by score descending.
      Output ranked list.
    subagent: "relevance-ranker-specialist"
    tools: ["rank_pages.py"]
    inputs: "inventory.json from crawler-specialist"
    outputs: "ranked_pages.json with array of {url, canonical_url, rank, reasons: [string], category: string}"
    failure_mode: "Semantic scoring fails (Claude API error or no ANTHROPIC_API_KEY)"
    fallback: "Use heuristic-only scoring (path keywords), skip semantic component, log warning"

  - name: "Deep Extract Structured Data"
    description: |
      Load ranked_pages.json and select top K pages (default 10).
      For each page, deep-scrape via Firecrawl scrape endpoint (structured mode) or fallback to HTTP + BeautifulSoup.
      Extract structured fields: offers, pricing, guarantees, process_steps, faq, testimonials, contact_methods, policies, constraints.
      Capture quoted evidence for each extracted claim (url + excerpt + page_title + extracted_at_iso).
      Handle login/paywall pages: mark as inaccessible with reason, skip extraction, continue with remaining pages.
      Apply rate limiting (1-2 req/sec).
      Output deep_extract.json with pages array.
    subagent: "deep-extract-specialist"
    tools: ["deep_extract.py"]
    inputs: "ranked_pages.json from relevance-ranker-specialist, top_k_deep_extract integer"
    outputs: "deep_extract.json with {pages: [{url, extracted_at, extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints}]}"
    failure_mode: "Firecrawl API fails, page requires auth, page is 404 or 500"
    fallback: "Skip failed pages, log errors, continue with remaining pages; if fewer than 5 pages succeed, flag for GitHub Issue"

  - name: "Synthesize Intelligence Pack"
    description: |
      Load inventory.json, ranked_pages.json, deep_extract.json.
      Synthesize findings into structured JSON sections:
        - positioning: What the company does, target market, value proposition
        - offers_and_pricing: Product/service offerings, pricing models, plans
        - customer_journey: How customers engage (signup, onboarding, usage, support)
        - trust_signals: Testimonials, case studies, guarantees, certifications
        - compliance_and_policies: Privacy policy, terms of service, data handling, refund policy
        - unknowns_and_gaps: What couldn't be determined from accessible pages
      Build evidence_index: map evidence_id to {url, excerpt, page_title, extracted_at_iso}.
      Ensure every claim in synthesized_findings references evidence_index.
      Populate run_metadata: crawl statistics (pages_crawled, pages_ranked, pages_extracted, errors).
      Assemble final site_intelligence_pack.json.
    subagent: "synthesis-validator-specialist"
    tools: ["synthesize_pack.py"]
    inputs: "inventory.json, ranked_pages.json, deep_extract.json"
    outputs: "site_intelligence_pack.json (complete pack with all sections)"
    failure_mode: "Missing evidence references, schema validation failure"
    fallback: "Flag claims without evidence as [needs verification], note in unknowns_and_gaps section, continue"

  - name: "Evidence Validation"
    description: |
      Load site_intelligence_pack.json.
      Validate that every claim in synthesized_findings has a corresponding evidence_index entry.
      Check that evidence_index entries have all required fields (url, excerpt, extracted_at_iso).
      Run JSON schema validation on the full pack.
      Log any validation errors.
    subagent: "synthesis-validator-specialist"
    tools: ["validate_evidence.py"]
    inputs: "site_intelligence_pack.json from synthesis step"
    outputs: "validation_report dict with {passed: bool, errors: [string]}"
    failure_mode: "Validation fails (missing evidence, malformed JSON)"
    fallback: "Log validation errors in run_metadata, flag site_intelligence_pack as 'partial' or 'needs_review', still commit"

  - name: "Generate Run Report (README.md)"
    description: |
      Generate human-readable summary report:
        - Summary: domain, pages crawled, pages ranked, pages extracted, execution time
        - Key Findings: high-level insights from synthesized_findings
        - Robots.txt Compliance: summary of allowed/disallowed paths, compliance status
        - Issues Encountered: any errors, inaccessible pages, validation warnings
        - Output Files: links to inventory.json, ranked_pages.json, deep_extract.json, site_intelligence_pack.json
      Write to README.md.
    subagent: "synthesis-validator-specialist"
    tools: ["generate_report.py"]
    inputs: "site_intelligence_pack.json, validation_report"
    outputs: "README.md (human-readable run report)"
    failure_mode: "Template rendering error"
    fallback: "Generate minimal README with raw JSON summary, log error"

  - name: "Commit Outputs to Repository"
    description: |
      Stage output files: inventory.json, ranked_pages.json, deep_extract.json, site_intelligence_pack.json, README.md.
      Commit to outputs/{domain}/ directory.
      Use descriptive commit message: "Site intelligence pack for {domain} ({pages_crawled} pages crawled, {pages_extracted} extracted)"
    subagent: "none (main agent)"
    tools: ["git"]
    inputs: "All output JSON and README.md files"
    outputs: "Git commit with outputs in outputs/{domain}/"
    failure_mode: "Git commit fails (merge conflict, permission error)"
    fallback: "Retry commit with rebase, if still fails, log error and exit"

  - name: "Open GitHub Issue on Major Failure (Conditional)"
    description: |
      If fewer than 5 pages were successfully extracted (from run_metadata), open a GitHub Issue:
        - Title: "Site intelligence pack failure: {domain} (only {N} pages extracted)"
        - Body: summary of errors, robots.txt status, inaccessible pages, suggested actions
        - Labels: "site-analysis-failure", "needs-review"
      Still commit partial output.
    subagent: "synthesis-validator-specialist"
    tools: ["create_github_issue.py"]
    inputs: "run_metadata, validation_report, domain"
    outputs: "GitHub Issue URL (if created)"
    failure_mode: "GitHub API fails (auth error, rate limit)"
    fallback: "Log failure to open issue, continue (partial output is already committed)"
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "fetch_robots.py"
    purpose: "Fetch and parse robots.txt from a domain, return allowed/disallowed paths for User-agent: *"
    catalog_pattern: "rest_client (HTTP GET with fallback)"
    inputs:
      - "domain: str — Target domain (e.g., 'example.com')"
    outputs: "{fetched_url: str, allowed_summary: str, disallowed_summary: str, raw_excerpt: str, disallowed_paths: [str]}"
    dependencies: ["requests", "robotparser (stdlib)"]
    mcp_used: "none (direct HTTP)"
    error_handling: "404 or timeout → return empty disallowed_paths list, note 'robots.txt not found' in summary"

  - name: "crawl_domain.py"
    purpose: "Crawl a domain via Firecrawl API (or fallback to HTTP + BeautifulSoup), return page inventory"
    catalog_pattern: "firecrawl_scrape (crawl mode) with HTTP fallback"
    inputs:
      - "domain: str — Target domain"
      - "max_pages: int — Maximum pages to crawl (default 200)"
      - "rate_limit_rps: float — Rate limit in requests per second (default 1.5)"
      - "disallowed_paths: [str] — List of disallowed URL paths from robots.txt"
    outputs: "[{url, canonical_url, title, discovered_from, http_status, content_hash, notes}]"
    dependencies: ["firecrawl-py", "requests", "beautifulsoup4", "hashlib"]
    mcp_used: "firecrawl (primary)"
    error_handling: "Firecrawl API error → fallback to requests + BeautifulSoup (no JS rendering); log fallback in notes; rate limit hit → exponential backoff"

  - name: "deduplicate_urls.py"
    purpose: "Canonicalize URLs and de-duplicate near-identical pages by content hash"
    catalog_pattern: "dedup (from tool_catalog.md) with URL normalization"
    inputs:
      - "inventory: [{url, content_hash, ...}] — Page inventory from crawl"
    outputs: "[{url, canonical_url, dedup_cluster_id, ...}] — Updated inventory with canonical URLs and cluster IDs"
    dependencies: ["urllib.parse (stdlib)"]
    mcp_used: "none"
    error_handling: "Malformed URL → skip canonicalization for that URL, log warning, keep original URL"

  - name: "rank_pages.py"
    purpose: "Rank pages by relevance using path heuristics + semantic scoring (optional)"
    catalog_pattern: "llm_prompt (for semantic scoring) + filter_sort"
    inputs:
      - "inventory: [{url, title, ...}] — Page inventory from deduplication"
    outputs: "[{url, canonical_url, rank, reasons: [str], category: str}]"
    dependencies: ["anthropic", "re (stdlib)"]
    mcp_used: "anthropic (optional — for semantic scoring)"
    error_handling: "Claude API error or no ANTHROPIC_API_KEY → use heuristic-only scoring, log warning"

  - name: "deep_extract.py"
    purpose: "Deep-scrape top K pages and extract structured business data with evidence capture"
    catalog_pattern: "firecrawl_scrape (scrape mode with structured output) + structured_extract"
    inputs:
      - "ranked_pages: [{url, ...}] — Ranked pages from ranker"
      - "top_k: int — Number of top pages to extract (default 10)"
      - "rate_limit_rps: float — Rate limit in requests per second"
    outputs: "{pages: [{url, extracted_at, extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints}]}"
    dependencies: ["firecrawl-py", "anthropic", "requests", "beautifulsoup4"]
    mcp_used: "firecrawl (primary), anthropic (for extraction)"
    error_handling: "Page requires auth/paywall → mark as inaccessible, log reason, skip extraction; Firecrawl API error → fallback to requests + BeautifulSoup; extraction fails → log error, continue with next page"

  - name: "synthesize_pack.py"
    purpose: "Synthesize intelligence pack from inventory, ranked pages, and deep extracts with evidence index"
    catalog_pattern: "llm_prompt (for synthesis) + custom assembly logic"
    inputs:
      - "inventory: [{...}] — Full inventory"
      - "ranked_pages: [{...}] — Ranked pages"
      - "deep_extract: {pages: [...]} — Deep-extracted data"
    outputs: "{site, inventory, ranked_pages, deep_extract_notes, synthesized_findings, evidence_index, run_metadata}"
    dependencies: ["anthropic"]
    mcp_used: "anthropic"
    error_handling: "Missing evidence for claim → flag as [needs verification], note in unknowns_and_gaps"

  - name: "validate_evidence.py"
    purpose: "Validate that all claims in synthesized_findings have evidence_index entries"
    catalog_pattern: "custom validation logic"
    inputs:
      - "site_intelligence_pack: {...} — Full pack from synthesis"
    outputs: "{passed: bool, errors: [str]}"
    dependencies: ["jsonschema"]
    mcp_used: "none"
    error_handling: "Validation error → log errors, return passed=false, continue (validation report included in run_metadata)"

  - name: "generate_report.py"
    purpose: "Generate human-readable README.md from intelligence pack"
    catalog_pattern: "custom reporting logic with markdown formatting"
    inputs:
      - "site_intelligence_pack: {...} — Full pack"
      - "validation_report: {passed, errors} — Validation results"
    outputs: "README.md (markdown string)"
    dependencies: ["jinja2 (optional for templating)"]
    mcp_used: "none"
    error_handling: "Template rendering error → generate minimal README with JSON summary, log error"

  - name: "create_github_issue.py"
    purpose: "Open a GitHub Issue on major failure (fewer than 5 pages extracted)"
    catalog_pattern: "github_create_issue (from tool_catalog.md)"
    inputs:
      - "repo: str — GitHub repo (owner/repo)"
      - "domain: str — Target domain"
      - "run_metadata: {...} — Run statistics and errors"
    outputs: "{issue_url: str}"
    dependencies: ["requests"]
    mcp_used: "github (or direct GitHub REST API)"
    error_handling: "GitHub API error → log failure, continue (partial output already committed)"
```

### Per-Tool Pseudocode
```python
# fetch_robots.py
def main(domain: str) -> dict:
    # PATTERN: rest_client with robotparser
    # CRITICAL: Fetch https://{domain}/robots.txt BEFORE any crawling
    import urllib.robotparser, requests
    
    robots_url = f"https://{domain}/robots.txt"
    try:
        resp = requests.get(robots_url, timeout=10)
        resp.raise_for_status()
        raw_text = resp.text
    except Exception as e:
        # robots.txt not found — assume all paths allowed
        return {
            "fetched_url": robots_url,
            "allowed_summary": "robots.txt not found, assuming all paths allowed",
            "disallowed_summary": "None",
            "raw_excerpt": "",
            "disallowed_paths": [],
        }
    
    # Parse robots.txt
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(raw_text.splitlines())
    
    # Extract disallowed paths for User-agent: *
    disallowed_paths = [entry.path for entry in rp.entries if entry.useragents == ["*"] and not entry.allowance]
    
    return {
        "fetched_url": robots_url,
        "allowed_summary": "Most paths allowed" if len(disallowed_paths) < 10 else "Many paths disallowed",
        "disallowed_summary": f"Disallowed: {', '.join(disallowed_paths[:5])}" if disallowed_paths else "None",
        "raw_excerpt": raw_text[:500],
        "disallowed_paths": disallowed_paths,
    }

# crawl_domain.py
def main(domain: str, max_pages: int, rate_limit_rps: float, disallowed_paths: list[str]) -> list[dict]:
    # PATTERN: firecrawl_scrape with fallback to HTTP + BeautifulSoup
    # CRITICAL: Respect rate_limit_rps — add sleep between requests
    # CRITICAL: Skip URLs matching disallowed_paths from robots.txt
    import os, time, hashlib
    from firecrawl import FirecrawlApp
    from urllib.parse import urlparse
    
    app = FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY"))
    base_url = f"https://{domain}"
    
    try:
        # Firecrawl crawl mode
        result = app.crawl_url(base_url, params={
            "limit": max_pages,
            "scrapeOptions": {"formats": ["markdown"]},
        })
        pages = result.get("data", [])
    except Exception as e:
        # FALLBACK: Direct HTTP + BeautifulSoup (no JS rendering)
        import requests
        from bs4 import BeautifulSoup
        
        pages = []
        visited = set()
        queue = [base_url]
        
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            
            # Check robots.txt disallow
            path = urlparse(url).path
            if any(path.startswith(disallow) for disallow in disallowed_paths):
                continue  # Skip disallowed path
            
            try:
                time.sleep(1.0 / rate_limit_rps)  # Rate limit
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Extract title
                title = soup.title.string if soup.title else "No title"
                
                # Extract visible text for content hash
                visible_text = soup.get_text(separator=" ", strip=True)
                content_hash = hashlib.md5(visible_text.encode()).hexdigest()
                
                pages.append({
                    "url": url,
                    "title": title,
                    "http_status": resp.status_code,
                    "content_hash": content_hash,
                    "notes": "Crawled via HTTP fallback (no JS rendering)",
                })
                
                # Extract links for further crawling
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith("/"):
                        href = f"https://{domain}{href}"
                    if href.startswith(base_url):
                        queue.append(href)
            except Exception as crawl_err:
                continue  # Skip failed pages
        
    # De-duplicate and return inventory
    inventory = []
    for page in pages:
        url = page.get("url")
        canonical_url = _canonicalize_url(url)  # Helper function for URL normalization
        inventory.append({
            "url": url,
            "canonical_url": canonical_url,
            "title": page.get("title", ""),
            "discovered_from": "crawl",
            "http_status": page.get("http_status", 200),
            "content_hash": page.get("content_hash", ""),
            "notes": page.get("notes", ""),
        })
    
    return inventory

# deduplicate_urls.py
def main(inventory: list[dict]) -> list[dict]:
    # PATTERN: dedup with URL canonicalization
    # CRITICAL: Canonicalize URLs (lowercase host, strip utm params, normalize trailing slashes)
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    
    def canonicalize(url: str) -> str:
        parsed = urlparse(url)
        # Lowercase scheme and host
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Remove trailing slash EXCEPT for root
        path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path
        # Strip tracking params
        query_params = parse_qs(parsed.query)
        filtered_params = {k: v for k, v in query_params.items() if not k.startswith("utm_") and k not in ["fbclid", "gclid", "ref"]}
        query = urlencode(filtered_params, doseq=True)
        
        return urlunparse((scheme, netloc, path, "", query, ""))
    
    # Cluster by content_hash
    clusters = {}
    for item in inventory:
        content_hash = item.get("content_hash", "")
        if not content_hash:
            continue
        if content_hash not in clusters:
            clusters[content_hash] = []
        clusters[content_hash].append(item)
    
    # Keep best representative from each cluster (prefer shorter URLs)
    deduped = []
    for cluster_id, items in clusters.items():
        best = min(items, key=lambda x: len(x["url"]))  # Shortest URL
        best["dedup_cluster_id"] = cluster_id
        deduped.append(best)
    
    return deduped

# rank_pages.py
def main(inventory: list[dict]) -> list[dict]:
    # PATTERN: llm_prompt (semantic scoring) + filter_sort (heuristic scoring)
    # CRITICAL: Combine heuristic (path keywords) + semantic (Claude-based) scores
    import os, re
    from anthropic import Anthropic
    
    # Path-based heuristics
    heuristic_keywords = {
        "pricing": 10, "price": 10, "plans": 10, "buy": 9,
        "faq": 8, "help": 7, "support": 7,
        "about": 7, "company": 6, "team": 6,
        "contact": 6, "careers": 5,
        "blog": 4, "news": 4,
        "terms": 5, "privacy": 5, "legal": 5,
    }
    
    ranked = []
    for item in inventory:
        url = item["url"]
        path = url.lower()
        
        # Heuristic score
        heuristic_score = 0
        matched_keywords = []
        for keyword, points in heuristic_keywords.items():
            if keyword in path:
                heuristic_score += points
                matched_keywords.append(keyword)
        
        # Semantic score (optional)
        semantic_score = 0
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
                title = item.get("title", "")
                prompt = f"Rate the business intelligence value of this webpage for competitive analysis (0-10):\nTitle: {title}\nURL: {url}"
                msg = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=50,
                    messages=[{"role": "user", "content": prompt}]
                )
                semantic_score = float(msg.content[0].text.strip())
            except Exception:
                semantic_score = 0
        
        # Combined score (weighted: 60% heuristic, 40% semantic)
        total_score = (heuristic_score * 0.6) + (semantic_score * 0.4)
        
        # Assign category
        category = "other"
        if any(kw in path for kw in ["pricing", "price", "plans", "buy"]):
            category = "offers/pricing"
        elif any(kw in path for kw in ["terms", "privacy", "legal", "policy"]):
            category = "policies"
        elif any(kw in path for kw in ["about", "company", "team"]):
            category = "about"
        elif any(kw in path for kw in ["faq", "help", "support"]):
            category = "faq"
        elif any(kw in path for kw in ["contact", "careers"]):
            category = "contact"
        elif any(kw in path for kw in ["blog", "news"]):
            category = "blog"
        
        ranked.append({
            "url": url,
            "canonical_url": item["canonical_url"],
            "rank": total_score,
            "reasons": matched_keywords + ([f"semantic_score={semantic_score}"] if semantic_score > 0 else []),
            "category": category,
        })
    
    # Sort by rank descending
    ranked.sort(key=lambda x: x["rank"], reverse=True)
    
    return ranked

# deep_extract.py
def main(ranked_pages: list[dict], top_k: int, rate_limit_rps: float) -> dict:
    # PATTERN: firecrawl_scrape (scrape mode with structured output) + structured_extract
    # CRITICAL: Capture evidence (url + excerpt + page_title) for each extracted claim
    import os, time
    from firecrawl import FirecrawlApp
    from anthropic import Anthropic
    
    app = FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY"))
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    top_pages = ranked_pages[:top_k]
    extracted_pages = []
    
    for page in top_pages:
        url = page["url"]
        
        try:
            time.sleep(1.0 / rate_limit_rps)  # Rate limit
            
            # Fetch page via Firecrawl
            result = app.scrape_url(url, params={"formats": ["markdown"]})
            markdown = result.get("markdown", "")
            title = result.get("metadata", {}).get("title", "No title")
            
            # Extract structured data via Claude
            prompt = f"""Extract structured business intelligence from this webpage:
Title: {title}
URL: {url}

Extract and return JSON with these fields:
- offers: [list of products/services offered]
- pricing: [pricing information with amounts and plans]
- how_it_works: [process steps or workflow]
- faq: [frequently asked questions with answers]
- testimonials: [customer quotes or case studies]
- policies: [refund/guarantee/privacy policy highlights]
- constraints: [limitations, requirements, or restrictions]

For each extracted item, include the exact quoted excerpt as evidence.

Content:
{markdown[:4000]}
"""
            
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json
            extracted_data = json.loads(msg.content[0].text)
            
            extracted_pages.append({
                "url": url,
                "extracted_at": time.time(),
                "page_title": title,
                **extracted_data,
            })
        
        except Exception as e:
            # Log error, skip this page, continue
            print(f"Error extracting {url}: {e}")
            continue
    
    return {"pages": extracted_pages}

# synthesize_pack.py
def main(inventory: list[dict], ranked_pages: list[dict], deep_extract: dict) -> dict:
    # PATTERN: llm_prompt for synthesis + custom assembly
    # CRITICAL: Build evidence_index mapping evidence_id to {url, excerpt, page_title, extracted_at_iso}
    import os, time
    from anthropic import Anthropic
    
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Synthesize findings via Claude
    synthesis_prompt = f"""Synthesize business intelligence findings from the extracted data below into these sections:

1. positioning: What the company does, target market, value proposition
2. offers_and_pricing: Product/service offerings, pricing models, plans
3. customer_journey: How customers engage (signup, onboarding, usage, support)
4. trust_signals: Testimonials, case studies, guarantees, certifications
5. compliance_and_policies: Privacy policy, terms of service, data handling, refund policy
6. unknowns_and_gaps: What couldn't be determined from accessible pages

Extracted data:
{deep_extract}

Return JSON with the above sections. For each claim, reference the source URL.
"""
    
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": synthesis_prompt}]
    )
    
    import json
    synthesized_findings = json.loads(msg.content[0].text)
    
    # Build evidence_index
    evidence_index = {}
    evidence_counter = 1
    for page in deep_extract.get("pages", []):
        url = page["url"]
        title = page.get("page_title", "")
        extracted_at = page.get("extracted_at", time.time())
        
        # For each extracted field, create evidence entries
        for field in ["offers", "pricing", "how_it_works", "faq", "testimonials", "policies"]:
            items = page.get(field, [])
            for item in items:
                evidence_id = f"ev{evidence_counter}"
                evidence_index[evidence_id] = {
                    "url": url,
                    "excerpt": str(item)[:200],  # Truncate excerpt to 200 chars
                    "page_title": title,
                    "extracted_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(extracted_at)),
                }
                evidence_counter += 1
    
    # Assemble final pack
    site_intelligence_pack = {
        "site": {
            "target_url": f"https://{inventory[0]['canonical_url'].split('/')[2]}",
            "domain": inventory[0]["canonical_url"].split("/")[2],
            "crawled_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "robots": {},  # Populated from fetch_robots.py output
        },
        "inventory": inventory,
        "ranked_pages": ranked_pages,
        "deep_extract_notes": deep_extract,
        "synthesized_findings": synthesized_findings,
        "evidence_index": evidence_index,
        "run_metadata": {
            "pages_crawled": len(inventory),
            "pages_ranked": len(ranked_pages),
            "pages_extracted": len(deep_extract.get("pages", [])),
            "errors": [],
        },
    }
    
    return site_intelligence_pack

# validate_evidence.py
def main(site_intelligence_pack: dict) -> dict:
    # PATTERN: custom validation logic
    # CRITICAL: Ensure every claim in synthesized_findings has evidence_index entry
    
    synthesized = site_intelligence_pack.get("synthesized_findings", {})
    evidence_index = site_intelligence_pack.get("evidence_index", {})
    
    errors = []
    
    # Check that synthesized_findings sections exist
    required_sections = ["positioning", "offers_and_pricing", "customer_journey", "trust_signals", "compliance_and_policies", "unknowns_and_gaps"]
    for section in required_sections:
        if section not in synthesized:
            errors.append(f"Missing required section: {section}")
    
    # Check that evidence_index entries have required fields
    for ev_id, ev_entry in evidence_index.items():
        if "url" not in ev_entry:
            errors.append(f"Evidence entry {ev_id} missing 'url' field")
        if "excerpt" not in ev_entry:
            errors.append(f"Evidence entry {ev_id} missing 'excerpt' field")
        if "extracted_at_iso" not in ev_entry:
            errors.append(f"Evidence entry {ev_id} missing 'extracted_at_iso' field")
    
    # TODO: Cross-check that synthesized claims reference evidence_index (more complex validation)
    
    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }

# generate_report.py
def main(site_intelligence_pack: dict, validation_report: dict) -> str:
    # PATTERN: custom reporting with markdown formatting
    
    site = site_intelligence_pack.get("site", {})
    run_metadata = site_intelligence_pack.get("run_metadata", {})
    synthesized = site_intelligence_pack.get("synthesized_findings", {})
    
    report = f"""# Site Intelligence Pack: {site.get("domain", "Unknown")}

## Summary
- **Target URL**: {site.get("target_url", "N/A")}
- **Crawled At**: {site.get("crawled_at_iso", "N/A")}
- **Pages Crawled**: {run_metadata.get("pages_crawled", 0)}
- **Pages Ranked**: {run_metadata.get("pages_ranked", 0)}
- **Pages Extracted**: {run_metadata.get("pages_extracted", 0)}

## Key Findings

### Positioning
{synthesized.get("positioning", "No data")}

### Offers and Pricing
{synthesized.get("offers_and_pricing", "No data")}

### Customer Journey
{synthesized.get("customer_journey", "No data")}

### Trust Signals
{synthesized.get("trust_signals", "No data")}

### Compliance and Policies
{synthesized.get("compliance_and_policies", "No data")}

### Unknowns and Gaps
{synthesized.get("unknowns_and_gaps", "No data")}

## Robots.txt Compliance
{site.get("robots", {}).get("allowed_summary", "N/A")}
{site.get("robots", {}).get("disallowed_summary", "N/A")}

## Issues Encountered
{"; ".join(run_metadata.get("errors", [])) if run_metadata.get("errors") else "None"}

## Validation Status
{"✅ Passed" if validation_report.get("passed") else "❌ Failed"}
{"; ".join(validation_report.get("errors", [])) if not validation_report.get("passed") else ""}

## Output Files
- `inventory.json` — Full page inventory
- `ranked_pages.json` — Pages ranked by relevance
- `deep_extract.json` — Deep-extracted structured data
- `site_intelligence_pack.json` — Complete intelligence pack

---
Generated by Site Intelligence Pack system
"""
    
    return report

# create_github_issue.py
def main(repo: str, domain: str, run_metadata: dict) -> dict:
    # PATTERN: github_create_issue
    import os, requests
    
    pages_extracted = run_metadata.get("pages_extracted", 0)
    
    if pages_extracted >= 5:
        return {"issue_url": ""}  # No issue needed
    
    errors = run_metadata.get("errors", [])
    
    title = f"Site intelligence pack failure: {domain} (only {pages_extracted} pages extracted)"
    body = f"""## Summary
The site intelligence pack for **{domain}** failed to extract sufficient data.

**Pages extracted**: {pages_extracted} (threshold: 5)

## Errors
{chr(10).join(f"- {err}" for err in errors)}

## Suggested Actions
1. Check robots.txt compliance
2. Review inaccessible pages (login/paywall)
3. Check Firecrawl API rate limits
4. Review partial output in `outputs/{domain}/`

---
Auto-generated by Site Intelligence Pack system
"""
    
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    payload = {
        "title": title,
        "body": body,
        "labels": ["site-analysis-failure", "needs-review"],
    }
    
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    
    return {"issue_url": resp.json().get("html_url", "")}
```

### Integration Points
```yaml
SECRETS:
  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API authentication for web crawling and scraping"
    required: true

  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API for semantic scoring and synthesis"
    required: true

  - name: "GITHUB_TOKEN"
    purpose: "GitHub API for opening issues on failures"
    required: true

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "FIRECRAWL_API_KEY=your_firecrawl_api_key_here  # Required: Firecrawl API key"
      - "ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Required: Claude API key"
      - "GITHUB_TOKEN=your_github_token_here  # Required: GitHub PAT for issue creation"
      - "MAX_PAGES=200  # Optional: Maximum pages to crawl per site"
      - "TOP_K_DEEP_EXTRACT=10  # Optional: Number of top-ranked pages to deep extract"
      - "RATE_LIMIT_RPS=1.5  # Optional: Rate limit in requests per second"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "firecrawl-py==1.0.0  # Firecrawl API client"
      - "anthropic==0.40.0  # Claude API client"
      - "requests==2.32.0  # HTTP client for fallback scraping and GitHub API"
      - "beautifulsoup4==4.12.0  # HTML parsing for fallback scraping"
      - "jsonschema==4.23.0  # JSON schema validation"
      - "jinja2==3.1.4  # Optional: Template rendering for reports"

GITHUB_ACTIONS:
  - trigger: "workflow_dispatch"
    config: |
      inputs:
        domain:
          description: 'Target domain to analyze (e.g., example.com)'
          required: false
        batch_csv_path:
          description: 'Path to CSV file with batch targets (default: inputs/targets.csv)'
          required: false
          default: 'inputs/targets.csv'
        max_pages:
          description: 'Maximum pages to crawl per site'
          required: false
          default: '200'
        top_k_deep_extract:
          description: 'Number of top-ranked pages to deep extract'
          required: false
          default: '10'
  
  - trigger: "schedule"
    config: "0 2 * * *  # Nightly at 2 AM UTC (optional)"
  
  - trigger: "issues"
    config: "opened with label 'site-analysis-request'"
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/fetch_robots.py').read())"
python -c "import ast; ast.parse(open('tools/crawl_domain.py').read())"
python -c "import ast; ast.parse(open('tools/deduplicate_urls.py').read())"
python -c "import ast; ast.parse(open('tools/rank_pages.py').read())"
python -c "import ast; ast.parse(open('tools/deep_extract.py').read())"
python -c "import ast; ast.parse(open('tools/synthesize_pack.py').read())"
python -c "import ast; ast.parse(open('tools/validate_evidence.py').read())"
python -c "import ast; ast.parse(open('tools/generate_report.py').read())"
python -c "import ast; ast.parse(open('tools/create_github_issue.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.fetch_robots')"
python -c "import importlib; importlib.import_module('tools.crawl_domain')"
python -c "import importlib; importlib.import_module('tools.deduplicate_urls')"
python -c "import importlib; importlib.import_module('tools.rank_pages')"
python -c "import importlib; importlib.import_module('tools.deep_extract')"
python -c "import importlib; importlib.import_module('tools.synthesize_pack')"
python -c "import importlib; importlib.import_module('tools.validate_evidence')"
python -c "import importlib; importlib.import_module('tools.generate_report')"
python -c "import importlib; importlib.import_module('tools.create_github_issue')"

# Structure check — verify main() exists
python -c "from tools.fetch_robots import main; assert callable(main)"
python -c "from tools.crawl_domain import main; assert callable(main)"
python -c "from tools.deduplicate_urls import main; assert callable(main)"
python -c "from tools.rank_pages import main; assert callable(main)"
python -c "from tools.deep_extract import main; assert callable(main)"
python -c "from tools.synthesize_pack import main; assert callable(main)"
python -c "from tools.validate_evidence import main; assert callable(main)"
python -c "from tools.generate_report import main; assert callable(main)"
python -c "from tools.create_github_issue import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test each tool independently with mock/sample data

# Test fetch_robots
python tools/fetch_robots.py --domain "example.com"
# Expected output: JSON with fetched_url, allowed_summary, disallowed_summary, disallowed_paths

# Test crawl_domain (limited to 5 pages for testing)
python tools/crawl_domain.py --domain "example.com" --max_pages 5 --rate_limit_rps 1.0 --disallowed_paths "[]"
# Expected output: JSON array with URLs, titles, http_status, content_hash

# Test deduplicate_urls
echo '[{"url": "https://example.com/page", "content_hash": "abc123"}, {"url": "https://example.com/page?utm_source=test", "content_hash": "abc123"}]' > /tmp/inventory.json
python tools/deduplicate_urls.py --inventory /tmp/inventory.json
# Expected output: JSON array with 1 entry (deduped), canonical_url, dedup_cluster_id

# Test rank_pages
echo '[{"url": "https://example.com/pricing", "title": "Pricing Plans"}, {"url": "https://example.com/about", "title": "About Us"}]' > /tmp/inventory.json
python tools/rank_pages.py --inventory /tmp/inventory.json
# Expected output: JSON array with ranked pages, reasons, categories

# Test deep_extract
echo '[{"url": "https://example.com/pricing", "canonical_url": "https://example.com/pricing"}]' > /tmp/ranked.json
python tools/deep_extract.py --ranked_pages /tmp/ranked.json --top_k 1 --rate_limit_rps 1.0
# Expected output: JSON with pages array containing extracted fields

# Test synthesize_pack
python tools/synthesize_pack.py --inventory /tmp/inventory.json --ranked_pages /tmp/ranked.json --deep_extract /tmp/deep_extract.json
# Expected output: Complete site_intelligence_pack.json

# Test validate_evidence
python tools/validate_evidence.py --site_intelligence_pack /tmp/site_intelligence_pack.json
# Expected output: {passed: true/false, errors: [...]}

# Test generate_report
python tools/generate_report.py --site_intelligence_pack /tmp/site_intelligence_pack.json --validation_report /tmp/validation.json
# Expected output: Markdown string (README.md content)

# Test create_github_issue (dry-run mode with mock data)
python tools/create_github_issue.py --repo "owner/repo" --domain "example.com" --run_metadata '{"pages_extracted": 2, "errors": ["Firecrawl API error"]}'
# Expected output: {issue_url: "https://github.com/owner/repo/issues/123"} (if pages_extracted < 5)

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with sample data

# Step 1: Fetch robots.txt
python tools/fetch_robots.py --domain "example.com" > /tmp/robots.json

# Step 2: Crawl domain (limited to 10 pages for testing)
python tools/crawl_domain.py --domain "example.com" --max_pages 10 --rate_limit_rps 1.0 --disallowed_paths "$(jq -r '.disallowed_paths | @json' /tmp/robots.json)" > /tmp/inventory.json

# Step 3: Deduplicate URLs
python tools/deduplicate_urls.py --inventory /tmp/inventory.json > /tmp/inventory_deduped.json

# Step 4: Rank pages
python tools/rank_pages.py --inventory /tmp/inventory_deduped.json > /tmp/ranked_pages.json

# Step 5: Deep extract top 3 pages
python tools/deep_extract.py --ranked_pages /tmp/ranked_pages.json --top_k 3 --rate_limit_rps 1.0 > /tmp/deep_extract.json

# Step 6: Synthesize intelligence pack
python tools/synthesize_pack.py --inventory /tmp/inventory_deduped.json --ranked_pages /tmp/ranked_pages.json --deep_extract /tmp/deep_extract.json > /tmp/site_intelligence_pack.json

# Step 7: Validate evidence
python tools/validate_evidence.py --site_intelligence_pack /tmp/site_intelligence_pack.json > /tmp/validation_report.json

# Step 8: Generate README
python tools/generate_report.py --site_intelligence_pack /tmp/site_intelligence_pack.json --validation_report /tmp/validation_report.json > /tmp/README.md

# Verify final outputs
python -c "
import json
pack = json.load(open('/tmp/site_intelligence_pack.json'))
assert 'site' in pack, 'Missing site section'
assert 'inventory' in pack, 'Missing inventory'
assert 'ranked_pages' in pack, 'Missing ranked_pages'
assert 'deep_extract_notes' in pack, 'Missing deep_extract_notes'
assert 'synthesized_findings' in pack, 'Missing synthesized_findings'
assert 'evidence_index' in pack, 'Missing evidence_index'
assert 'run_metadata' in pack, 'Missing run_metadata'
print('✅ Integration test passed')
"

# Verify workflow.md references match actual tool files
# Verify CLAUDE.md documents all tools and subagents
# Verify .github/workflows/ YAML is valid
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
- [ ] .gitignore excludes .env, __pycache__/, credentials
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies
- [ ] robots.txt compliance is enforced (fetch first, skip disallowed paths)
- [ ] Evidence validation is implemented (all claims reference evidence_index)
- [ ] De-duplication is implemented (URL canonicalization + content hashing)
- [ ] Rate limiting is implemented (1-2 req/sec with exponential backoff)
- [ ] GitHub Issue creation on major failure (fewer than 5 pages extracted)
- [ ] Fallback chain is implemented (Firecrawl → HTTP + BeautifulSoup → partial output)

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only specific files
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks
- Do not design subagents that call other subagents — only the main agent delegates
- Do not use Agent Teams when fewer than 3 independent tasks exist — the overhead is not justified
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not skip robots.txt compliance check — MUST fetch and parse robots.txt before any crawling
- Do not proceed with crawling if robots.txt disallows it — respect the rules, note in output
- Do not store evidence without url + excerpt + page_title + extracted_at — all evidence must be traceable
- Do not synthesize findings without evidence validation — every claim must reference evidence_index
- Do not skip de-duplication — URL canonicalization and content hashing are MANDATORY
- Do not exceed rate limits — implement delays and exponential backoff

---

## Confidence Score: 9/10

**Score rationale:**
- [System Architecture]: High confidence — subagent architecture is clear, workflow phases are well-defined, tools are scoped correctly — Confidence: high
- [Technical Feasibility]: High confidence — all required MCPs and APIs are available (Firecrawl, Anthropic, GitHub), fallback strategies are defined, rate limiting is implementable — Confidence: high
- [Validation Strategy]: High confidence — three-level validation (syntax, unit, integration) is comprehensive, test cases are specific, integration test covers full pipeline — Confidence: high
- [Evidence & Compliance Requirements]: High confidence — robots.txt compliance is enforceable, evidence validation is well-specified, de-duplication logic is clear — Confidence: high
- [Failure Modes & Fallbacks]: Medium-high confidence — fallback chains are defined (Firecrawl → HTTP), GitHub Issue creation on failure is specified, partial output handling is clear; uncertainty around edge cases (e.g., extremely large sites, rate limit exhaustion) — Confidence: medium-high
- [Batch Mode Scalability]: Medium confidence — sequential processing respects rate limits but may be slow for large batches (200 domains * 200 pages * 1.5 RPS = ~27,000 seconds = 7.5 hours); recommendation: batch processing is feasible but slow, may need chunking for very large batches — Confidence: medium

**Ambiguity flags** (areas requiring clarification before building):
- [ ] **Batch processing scale**: If inputs/targets.csv has 200+ domains, the nightly job may exceed reasonable runtime (7+ hours). Should we implement chunking (e.g., process 20 domains per run, rotate through the list)? Or is sequential processing acceptable for the expected batch sizes?
- [ ] **Semantic scoring model**: For lightweight semantic scoring (titles/headings/first N chars), should we use Claude Sonnet 4 (more accurate but slower/costlier) or Claude Haiku (faster/cheaper but less nuanced)? Or make it configurable?

**If any ambiguity flag is checked, DO NOT proceed to build. Ask the user to clarify first.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/site-intelligence-pack.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
