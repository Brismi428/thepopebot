# Site Intelligence Pack -- Workflow

## Purpose

Build comprehensive website analysis reports that produce evidence-backed business intelligence by crawling target domains, ranking pages by relevance, extracting structured data from top pages, and synthesizing findings with full evidence provenance.

## Inputs

- `target_domain` (string, required) -- Domain to analyze without protocol (e.g., "stripe.com")
- `max_pages` (integer, optional, default: 200) -- Maximum pages to crawl per domain
- `deep_extract_count` (integer, optional, default: 15) -- Number of top-ranked pages to deep-extract
- `batch_mode` (boolean, optional, default: false) -- If true, process all domains in inputs/targets.csv

## Outputs

All outputs committed to `outputs/{domain}/{timestamp}/`:

- `inventory.json` -- All discovered pages with URLs, titles, HTTP status, content hashes, dedup cluster IDs
- `ranked_pages.json` -- Pages sorted by relevance score with category tags
- `deep_extract.json` -- Structured extractions from top K pages with quoted evidence
- `site_intelligence_pack.json` -- Final synthesized report with evidence index
- `README.md` -- Human-readable summary of findings

## Workflow Steps

---

### Step 1: Initialize

Parse inputs, validate domain, create output directory structure.

**Subagent:** Main agent (no delegation needed)

**Actions:**
1. Read inputs from workflow_dispatch or environment variables
2. Validate domain format (no protocol, valid DNS format)
3. If `batch_mode` is true, load all domains from `inputs/targets.csv`
4. Create timestamp: `YYYY-MM-DDTHHMMSS` format
5. Create output directory: `outputs/{domain}/{timestamp}/`
6. Initialize run metadata dict

**Outputs:** 
- Validated domain string
- Output directory path
- Timestamp string
- Run metadata dict

**Failure mode:** Invalid domain format or missing inputs
**Fallback:** Log error, skip domain in batch mode, halt in single mode

---

### Step 2: Fetch robots.txt

Fetch and parse robots.txt for the target domain. Extract User-agent: * disallowed paths.

**Subagent:** Main agent

**Tool:** `tools/fetch_robots.py`

**Actions:**
1. Call `fetch_robots.py` with domain
2. Store result in run metadata
3. Extract disallowed_paths list for next step

**Outputs:**
- `robots_dict`: {allowed_summary, disallowed_summary, raw_excerpt, disallowed_paths: [list]}

**Failure mode:** robots.txt not found (404) or unreachable
**Fallback:** Assume all paths allowed, log warning, proceed with empty disallowed_paths

---

### Step 3: Crawl site

Crawl the domain via Firecrawl API (or HTTP fallback). Respect robots.txt disallowed paths. Max 200 pages.

**Subagent:** Main agent

**Tool:** `tools/firecrawl_crawl.py` (primary), `tools/http_crawl_fallback.py` (fallback)

**Actions:**
1. Call `firecrawl_crawl.py` with domain, max_pages, disallowed_paths
2. **If Firecrawl fails:** Call `http_crawl_fallback.py` with same parameters
3. Store raw_pages list in memory

**Outputs:**
- `raw_pages`: [{url, title, content, status, discovered_from}]

**Failure mode:** Firecrawl rate limited, timeout, or API error
**Fallback:** Retry with exponential backoff (3 attempts). If Firecrawl fails, fall back to HTTP crawl (loses JS content but maintains basic functionality). If < 5 pages retrieved, open GitHub Issue but continue with partial data.

**Critical check:** If < 5 pages crawled successfully, flag for GitHub Issue creation at end but continue workflow.

---

### Step 4: Build inventory

Normalize URLs, extract canonical links, compute content hashes, identify duplicate clusters.

**Subagent:** Main agent

**Tool:** `tools/build_inventory.py`

**Actions:**
1. Call `build_inventory.py` with raw_pages
2. Write output to `outputs/{domain}/{timestamp}/inventory.json`
3. Store inventory list in memory for next step

**Outputs:**
- `inventory.json`: [{url, canonical_url, title, discovered_from, http_status, content_hash, dedup_cluster_id, notes}]

**Failure mode:** Parsing error on malformed URLs or canonical tags
**Fallback:** Use original URL as canonical, log warning, continue

---

### Step 5: Rank pages

Score pages by relevance using path keywords, titles, and lightweight semantic analysis. Delegate to relevance-ranker-specialist.

**Subagent:** `relevance-ranker-specialist`

**Tool:** `tools/rank_pages.py`

**Actions:**
1. Delegate to `relevance-ranker-specialist` with inventory
2. Specialist analyzes URLs, titles, and content previews
3. Specialist applies path keyword scoring and semantic scoring
4. Specialist assigns priority categories
5. Write output to `outputs/{domain}/{timestamp}/ranked_pages.json`
6. Store ranked list in memory for next step

**Outputs:**
- `ranked_pages.json`: [{url, canonical_url, rank, reasons: [list], category}]

**Failure mode:** Scoring algorithm error or missing required fields
**Fallback:** Assign default score based on path only, log warning, continue

---

### Step 6: Deep extract (Agent Teams)

Extract structured data from top K ranked pages in parallel using Agent Teams.

**Subagent:** `deep-extract-specialist` (team lead + K teammates)

**Tool:** `tools/deep_extract_page.py`

**Actions:**

**Team Lead (deep-extract-specialist):**
1. Read ranked_pages.json
2. Select top K pages (K = deep_extract_count parameter)
3. **If K >= 3:** Use Agent Teams for parallel execution:
   - Create task manifest: list of URLs to extract
   - Spawn K teammates (or batch into groups of 5-10 if K > 10)
   - Each teammate calls `deep_extract_page.py` with assigned URL
   - Collect all extraction results
   - Merge into single deep_extract dict
4. **If K < 3:** Sequential execution (no Agent Teams overhead):
   - Call `deep_extract_page.py` for each URL sequentially
   - Append results to deep_extract dict
5. Write output to `outputs/{domain}/{timestamp}/deep_extract.json`

**Each Teammate (page-extractor-NN):**
1. Receive assigned page URL
2. Call `deep_extract_page.py` with URL and content
3. Return structured extraction dict with evidence

**Outputs:**
- `deep_extract.json`: {pages: [{url, title, summary, extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints}]}

**Failure mode:** Agent Teams coordination failure, timeout, or LLM API error
**Fallback:** Fall back to sequential extraction (slower but reliable). If < 5 pages extracted, open GitHub Issue but commit partial results.

**Critical check:** If < 5 pages extracted successfully, flag for GitHub Issue creation at end but continue workflow.

---

### Step 7: Synthesize and validate

Build final intelligence pack with synthesized findings, evidence index, and schema validation. Delegate to synthesis-validator-specialist.

**Subagent:** `synthesis-validator-specialist`

**Tool:** `tools/synthesize_findings.py`, `tools/validate_schema.py`, `tools/generate_readme.py`

**Actions:**
1. Delegate to `synthesis-validator-specialist` with all previous outputs
2. Specialist reads inventory, ranked_pages, and deep_extract
3. Specialist calls `synthesize_findings.py` to build intelligence pack
4. Specialist calls `validate_schema.py` to check JSON schema
5. **If validation fails:** Log errors, include warnings in output, continue
6. Specialist calls `generate_readme.py` to create human-readable summary
7. Write `site_intelligence_pack.json` to output directory
8. Write `README.md` to output directory

**Outputs:**
- `site_intelligence_pack.json`: Complete intelligence report with evidence index
- `README.md`: Human-readable summary

**Failure mode:** Schema validation failure or evidence mapping error
**Fallback:** Log validation errors, commit output with warnings, open GitHub Issue for manual review

---

### Step 8: Commit outputs

Commit all JSON files and README to outputs/{domain}/{timestamp}/.

**Subagent:** Main agent

**Tool:** Git CLI (via bash)

**Actions:**
1. Stage output files: `git add outputs/{domain}/{timestamp}/*`
2. Commit with message: `Add Site Intelligence Pack for {domain} ({timestamp})`
3. Push to origin with retry on failure

**Outputs:**
- Git commit SHA
- Committed files list

**Failure mode:** Git push failure or merge conflict
**Fallback:** Retry with rebase (3 attempts). If fails, log error and open GitHub Issue with outputs attached.

---

### Step 9: Report status

If critical failure (< 5 pages crawled OR < 5 pages extracted), create GitHub Issue with diagnostics.

**Subagent:** Main agent

**Tool:** `tools/github_create_issue.py`

**Actions:**
1. Check run_metadata for critical failures:
   - Pages crawled < 5
   - Pages extracted < 5
2. **If critical failure detected:**
   - Call `github_create_issue.py` with:
     - Title: `Site Intelligence Pack FAILED: {domain}`
     - Body: Target, timestamp, pages crawled/extracted, error details
     - Labels: `site-intelligence-pack`, `failed-run`
3. Log GitHub Issue URL

**Outputs:**
- GitHub Issue URL (if created)

**Failure mode:** GitHub API error
**Fallback:** Log error to workflow logs, continue

---

## Execution Paths

This system supports three execution modes:

### 1. GitHub Actions (Primary)
- Triggered via `workflow_dispatch` or schedule
- Runs in GitHub Actions environment
- Auto-commits results to repo
- Sends notifications on completion

### 2. Local CLI (Development)
- Run: `python workflow.py --domain example.com`
- Executes same workflow locally
- Manual commit of outputs

### 3. Agent HQ (Issue-driven)
- Open GitHub Issue with domain in body
- Assign to @claude
- Agent executes workflow
- Delivers results as PR

## Notes

- Rate limiting enforced: 1-2 req/sec with politeness controls
- Evidence tracking: Every extracted field MUST have evidence IDs
- Robots.txt compliance: Disallowed paths are filtered from crawl results
- De-duplication: Canonical URLs and content hashing prevent duplicates
- Partial success: System continues even if some pages fail
- Audit trail: Every run creates timestamped output directory with full logs
