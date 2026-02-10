# Marketing Pipeline — Workflow

A lead enrichment, scoring, segmentation, and outreach generation pipeline. Takes a CSV of leads (from lead-gen-machine or manual upload), enriches each with company data and decision-maker contacts, deep-scores them on a 0-100 scale, segments into tiers (Hot/Warm/Cold), and generates personalized email sequences for outreach and nurture.

## Inputs

- **leads_csv** (file path) — Path to a CSV file with at minimum a `company_name` column. Optional columns: `website`, `industry`, `location`, `company_size`, `notes`. Can be provided via:
  - `TASK_INPUT` environment variable (path to CSV)
  - `--input` command-line argument
  - Dropped into the `input/` directory (latest file used)
  - Issue body (for Agent HQ — expects CSV content or path)

## Outputs

- **output/enriched_leads_{timestamp}.csv** — Full enriched data for all leads
- **output/hot_leads.csv** — Hot tier leads (score 80+), ready for direct outreach
- **output/warm_leads.csv** — Warm tier leads (score 50-79), nurture sequence
- **output/outreach/emails_{company}.md** — Personalized 3-email cold outreach sequence per hot lead
- **output/nurture/sequence.md** — 5-email nurture drip content for warm leads
- **output/pipeline_summary.json** — Run stats, score distribution, segment breakdown

---

## Step 1: Ingest and Validate Leads

Parse and validate the input CSV.

1. Locate the input CSV:
   - Check `TASK_INPUT` env var first
   - Then check `--input` CLI argument
   - Then check `input/` directory for the most recent `.csv` file
2. Read the CSV using `tools/ingest_leads.py`
3. Validate required column: `company_name` must exist and be non-empty
4. Normalize data: trim whitespace, lowercase for matching, preserve original case for display
5. Deduplicate by `company_name` (case-insensitive)
6. Log: number of leads ingested, duplicates removed, columns detected

**Tool**: `tools/ingest_leads.py` — Reads, validates, and deduplicates the input CSV

**Decision point**: **If company_name column is missing**:
- **Yes**: Exit with error listing the columns found and the expected format
- **No**: Continue to Step 2

**Failure mode**: If the CSV is malformed (encoding issues, delimiter mismatch), attempt auto-detection with `chardet` and retry with detected encoding. If still failing, exit with a descriptive error.

---

## Step 2: Enrich Leads

Pull company details, tech stack, social profiles, and key decision makers for each lead.

1. For each lead, run enrichment via `tools/enrich_leads.py`:
   - **Apollo.io API** (primary): Query by company name/domain for company size, revenue estimate, tech stack, social profiles, and key contacts (name, title, email, LinkedIn)
   - **Hunter.io API** (secondary): Verify/find email addresses, find additional contacts
   - **Brave Search API** (research): Search for company blog posts, job listings, news, funding announcements
   - **Claude API** (analysis): Analyze scraped content for pain signals — hiring for ops roles, mentions of manual processes, complaints in reviews
2. For each lead, collect:
   - `company_size` (employee count or range)
   - `revenue_estimate` (if available)
   - `tech_stack` (list of technologies used, especially automation tools)
   - `social_profiles` (LinkedIn, Twitter/X, Crunchbase URLs)
   - `decision_makers` (list of {name, title, email, linkedin_url})
   - `recent_blog_posts` (list of recent article titles/URLs)
   - `job_listings` (list of relevant open positions)
   - `funding_history` (recent rounds if available)
   - `pain_signals` (list of detected pain indicators)
3. Rate-limit API calls: 1 req/sec for Apollo, 1 req/sec for Hunter, 1 req/sec for Brave
4. Track enrichment status per lead: `full`, `partial`, `failed`

**Tool**: `tools/enrich_leads.py` — Enriches leads via Apollo, Hunter, Brave Search, and Claude APIs

**Decision point**: **If Apollo API key is missing**:
- **Yes**: Fall back to Brave Search + Claude for company research (reduced data quality, no direct contacts). Log warning.
- **No**: Use Apollo as primary enrichment source

**Decision point**: **If enrichment fails for a specific lead**:
- **Yes**: Mark as `enrichment_status: failed`, continue with remaining leads. Do not block the batch.
- **No**: Continue processing

**Failure mode**: If all enrichment APIs are unreachable, exit with error. If only some fail, proceed with partial data and document gaps in the summary.

---

## Step 3: Deep Score Leads

Score each enriched lead on a 0-100 scale across 5 dimensions.

1. For each lead, compute scores via `tools/score_leads.py`:
   - **Company Size Fit** (0-20 points): Does the company size match the target? Exact range match = 20, adjacent = 10, no data = 5
   - **Tech Stack Compatibility** (0-25 points): Do they use automation tools (n8n, Zapier, Make, Workato, Tray.io)? Using competitors = 25, using adjacent tools = 15, no automation found = 5, no data = 3
   - **Budget Signals** (0-20 points): Job postings (especially ops/automation roles) = +8, recent funding = +6, growth indicators (hiring, expanding) = +6
   - **Decision Maker Accessibility** (0-15 points): Direct email found = 10, LinkedIn found = 5, multiple contacts = +5 (cap at 15)
   - **Pain Signal Detection** (0-20 points): Hiring for ops = +7, complaints about manual processes = +7, seeking automation solutions = +6
2. Total score = sum of all dimensions (cap at 100)
3. For each lead, store the breakdown: `{size_fit, tech_stack, budget_signals, accessibility, pain_signals, total}`

**Tool**: `tools/score_leads.py` — Computes multi-dimensional lead scores

**Failure mode**: If scoring data is missing for a dimension, use conservative defaults (see point values above for "no data" cases). Never skip a lead due to missing data — always produce a score.

---

## Step 4: Segment Leads

Sort scored leads into tiers.

1. Run `tools/segment_leads.py` on the scored leads
2. Apply tier thresholds:
   - **Hot** (score 80+): Ready for direct outreach
   - **Warm** (score 50-79): Nurture sequence
   - **Cold** (score below 50): Archive for later
3. Within each tier, sort by score descending
4. Log segment counts: Hot: N, Warm: N, Cold: N

**Tool**: `tools/segment_leads.py` — Segments leads into Hot/Warm/Cold tiers

**Failure mode**: If no leads qualify as Hot or Warm, log a warning and proceed — the system still produces enriched output. Suggest broadening the lead list or adjusting thresholds.

---

## Step 5: Generate Outreach Sequences (Hot Leads)

For each Hot lead, generate a personalized 3-email cold outreach sequence.

1. For each Hot lead, run `tools/generate_outreach.py`:
   - **Email 1 — Intro**: Reference something specific about the company (recent blog post, job listing, tech stack choice). Introduce the value proposition. Clear, personalized subject line.
   - **Email 2 — Value Add**: Share a relevant case study or insight. Connect their specific pain signal to a solution. No ask yet.
   - **Email 3 — Soft Close**: Gentle call-to-action (15-minute call, demo, resource). Reference previous emails. Create mild urgency without being pushy.
2. Each email includes: subject line, body, send timing (days after previous)
3. Claude generates the content using company-specific data from enrichment
4. Write each sequence to `output/outreach/emails_{company_slug}.md`

**Tool**: `tools/generate_outreach.py` — Generates personalized 3-email sequences using Claude

**Decision point**: **If Agent Teams is enabled AND 3+ Hot leads exist**:
- **Yes**: Fan out — each teammate generates outreach for a subset of Hot leads concurrently
- **No**: Process Hot leads sequentially

**Failure mode**: If Claude API fails for a specific lead, skip that lead's outreach generation, log the error, and continue. Mark the lead with `outreach_status: failed` in the summary.

---

## Step 6: Generate Nurture Sequence (Warm Leads)

Generate a 5-email drip sequence for the Warm tier.

1. Run `tools/generate_nurture.py` with the list of Warm leads:
   - **Email 1 — Welcome/Education**: Introduce the problem space. Share an industry insight.
   - **Email 2 — Case Study**: Real-world example of solving the automation problem.
   - **Email 3 — How-To**: Practical tips for improving operations/automation.
   - **Email 4 — Social Proof**: Testimonials, metrics, success stories.
   - **Email 5 — Soft CTA**: Invitation to learn more (webinar, guide, demo).
2. The nurture sequence is generic but informed by common pain signals across the Warm tier
3. Each email includes: subject line, body, send timing (days after previous)
4. Write to `output/nurture/sequence.md`

**Tool**: `tools/generate_nurture.py` — Generates 5-email nurture drip sequence using Claude

**Failure mode**: If generation fails, create a stub sequence with placeholder content and log the error. The pipeline still produces all other outputs.

---

## Step 7: Generate Outputs

Produce all output files.

1. Run `tools/output_pipeline.py` to generate:
   - `output/enriched_leads_{timestamp}.csv` — All leads with full enrichment data
   - `output/hot_leads.csv` — Hot tier leads only
   - `output/warm_leads.csv` — Warm tier leads only
   - `output/pipeline_summary.json` with:
     - Run timestamp
     - Input file used
     - Total leads processed
     - Enrichment stats (full/partial/failed counts)
     - Score distribution (min, max, avg, median)
     - Segment breakdown (hot/warm/cold counts and percentages)
     - Outreach sequences generated (count, list of companies)
     - Nurture sequence generated (boolean)
2. Verify all expected files were created

**Tool**: `tools/output_pipeline.py` — Generates CSVs and summary JSON

**Failure mode**: If CSV write fails, output as JSON fallback. If summary generation fails, the CSVs are still valid output.

---

## Step 8: Commit Results

Commit all output files back to the repository.

1. Stage all files in `output/`
2. Create commit: `pipeline: {N} leads processed, {hot} hot, {warm} warm ({date})`
3. Push to current branch

**Failure mode**: If git commit fails (no changes, auth error), log the failure. Output files are still available locally.

---

## Notes

- **Rate limiting**: Apollo (1 req/sec), Hunter (1 req/sec), Brave (1 req/sec free tier). The system respects all rate limits.
- **API fallback chain**: Apollo > Hunter > Brave Search + Claude > HTTP scraping. Each level degrades gracefully.
- **Privacy**: This system enriches business leads from publicly available sources and professional networking APIs. It does not scrape personal social media or use data brokers for personal information.
- **Token cost**: Email generation (Steps 5-6) is the primary Claude API cost. Expect ~1000 tokens per email, 3 emails per hot lead, 5 emails for nurture. Budget accordingly.
- **Parallelization**: Steps 5 and 6 are independent and can run in parallel with Agent Teams. Per-lead enrichment in Step 2 can also be parallelized.
- **Scheduling**: Recommended weekly via cron. Input CSV can be refreshed from lead-gen-machine output or manual upload between runs.
