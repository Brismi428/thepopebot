Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "site-intelligence-pack".

Problem description:
Comprehensive website analysis system with three specialist components for analyzing websites and producing evidence-backed business intelligence reports.

System Requirements:
- Input format: Single domain per run and batch supported. Batch list comes from a CSV in the repo at inputs/targets.csv.
- Triggering: On-demand (workflow_dispatch) + optional nightly scheduled batch run.
- Output destination: Commit outputs to the repo (JSON + README). No external storage by default.
- Scale expectations: 200 pages max per site by default. Follow robots.txt; add basic politeness: rate cap ~1–2 req/sec and stop early on repeated errors.
- Integration needs: Use Firecrawl for crawl/extract; GitHub for committing outputs and opening an Issue on major failures. No other integrations needed initially.

Three Specialist Components:
1. relevance-ranker-specialist: ranks pages using heuristics (path keywords like pricing/faq/terms) + lightweight semantic scoring on titles/headings/first N chars.
2. deep-extract-specialist: deep-scrapes top K pages; extracts structured fields (offer, pricing, guarantees, process steps, FAQs, contact methods, policies, testimonials) with quoted evidence.
3. synthesis-validator-specialist: builds final JSON pack, ensures every "important claim" has evidence entries (url + excerpt), and runs schema validation.

Core Requirements / Constraints:
- MUST respect robots.txt: Fetch https://{domain}/robots.txt first. If disallowed crawling is detected for relevant paths, do not crawl them; include this in run_report with the robots.txt excerpt.
- No authentication bypass: If pages require login/paywall, mark as inaccessible; do not attempt to bypass; include the URL + reason.
- Evidence rules: Every key claim in synthesized_findings must map to evidence_index entries with url + excerpt + extracted_at + page_title
- De-duplication: Canonicalize URLs (strip utm params, normalize trailing slashes, lowercasing host, etc.). Cluster near-identical pages and keep the best representative. Avoid repeating header/footer boilerplate as "content".
- Page inventory focus: Crawl broadly, but explicitly attempt discovery of: home, about, offers, pricing, faq, contact, policies, privacy, terms, blog.
- Ranking priority: Top relevance categories: offers/pricing/how-it-works/policies/testimonials → then about/faq/contact → then blog/other.
- Failure modes: If Firecrawl crawl fails or is blocked: fall back to direct HTTP inventory attempt; if still blocked, produce partial pack with clear "inaccessible" section. If fewer than N (default 5) pages are extracted successfully, open a GitHub Issue summarizing failure and still commit partial outputs.

JSON Schema (Site Intelligence Pack):
- site: { target_url, domain, crawled_at_iso, robots: {fetched_url, allowed_summary, disallowed_summary, raw_excerpt?} }
- inventory: [{ url, canonical_url, title?, discovered_from?, http_status?, content_hash?, dedup_cluster_id, notes? }]
- ranked_pages: [{ url, canonical_url, rank, reasons: [string], category: string }]
- deep_extract_notes with pages containing extracted_entities, offers, pricing, how_it_works, faq, testimonials, policies, constraints
- synthesized_findings with positioning, offers_and_pricing, customer_journey, trust_signals, compliance_and_policies, unknowns_and_gaps
- evidence_index mapping evidence_id to { url, excerpt, page_title?, extracted_at_iso }
- run_metadata with crawl statistics and errors

Repo Behavior:
Write outputs under output_dir including inventory.json, ranked_pages.json, deep_extract.json, site_intelligence_pack.json, README.md (run_report). Commit changes on completion.

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/site-intelligence-pack.md
5. Log the confidence score and any ambiguity flags

IMPORTANT: End your final commit message with exactly this line:
CONFIDENCE_SCORE: X/10
where X is the PRP's confidence score. This is used for automated pipeline decisions.