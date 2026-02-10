# Lead Gen Machine — Workflow

An automated lead generation system that takes an ideal customer profile, searches the web for matching companies, scrapes their websites for contact info and business details, scores each lead against the criteria, and outputs a ranked CSV of qualified leads committed back to the repo.

## Inputs

- **ideal_customer_profile** (JSON) — Description of the ideal customer with the following fields:
  - `industry` (string): Target industry (e.g., "SaaS", "Healthcare", "Fintech")
  - `company_size` (string): Target size range (e.g., "50-200", "201-1000", "1000+")
  - `location` (string): Geographic target (e.g., "United States", "San Francisco, CA", "Europe")
  - `keywords` (list[string]): Keywords describing the ideal customer (e.g., ["AI", "machine learning", "enterprise"])
  - `max_results` (int, optional): Maximum number of leads to generate (default: 50)
  - `min_score` (float, optional): Minimum match score threshold 0-100 (default: 40)

## Outputs

- **output/leads_{timestamp}.csv** — Ranked CSV file with columns: rank, company_name, website, industry, company_size, location, match_score, email, phone, description, scraped_at
- **output/run_summary.json** — Execution metadata: run timestamp, input profile, total found, total qualified, search queries used

---

## Step 1: Parse and Validate Input

Receive the ideal customer profile and validate it.

1. Parse the input JSON from environment variable `TASK_INPUT` or command-line argument
2. Validate required fields exist: `industry`, `company_size`, `location`, `keywords`
3. Set defaults: `max_results` to 50 if not provided, `min_score` to 40 if not provided
4. Normalize inputs: lowercase industry, trim whitespace from all fields

**Decision point**: **If required fields are missing**:
- **Yes**: Log the error, output a clear message listing missing fields, and exit with error code
- **No**: Continue to Step 2

**Failure mode**: If input JSON is malformed, exit with a descriptive parse error. Do not proceed with partial data.

---

## Step 2: Build Search Queries

Construct targeted search queries to find matching companies.

1. Combine the profile fields into multiple search query variations:
   - Primary query: `"{industry}" companies "{location}" {keywords[0]} {keywords[1]}`
   - Size-targeted query: `"{company_size} employees" "{industry}" "{location}"`
   - Keyword-focused queries: one query per keyword combined with industry and location
2. Generate 3-5 distinct queries to maximize coverage
3. Log all generated queries

**Tool**: `tools/search_companies.py` — Executes web searches and aggregates results

**Failure mode**: If query construction produces empty strings, fall back to a simple query: `"{industry}" companies "{location}"`.

---

## Step 3: Search for Companies

Execute web searches to find matching companies.

1. Run each search query through the Brave Search API (or fallback to web search)
2. Collect up to `max_results * 2` raw results (over-collect to account for deduplication and filtering)
3. For each result, extract: company name, URL, snippet description
4. Deduplicate results by domain name
5. Filter out obviously irrelevant results (job boards, directories, news articles) by domain pattern

**Tool**: `tools/search_companies.py` — Executes searches via Brave API with fallback to HTTP

**Decision point**: **If fewer than 5 results found**:
- **Yes**: Broaden queries by removing the most specific keyword, retry once
- **No**: Continue to Step 4

**Failure mode**: If the search API is unreachable, log the error and try the fallback HTTP search. If all searches fail, exit with an error listing what was attempted.

---

## Step 4: Scrape Company Websites

Visit each company website to extract business details and contact information.

1. For each company URL from Step 3:
   - Scrape the homepage using Firecrawl API (or fallback to requests + BeautifulSoup)
   - Also attempt to scrape common subpages: `/about`, `/contact`, `/team`
2. Extract raw text content from each page
3. Respect rate limits: wait 1-2 seconds between requests
4. Track scraping success/failure per company

**Tool**: `tools/scrape_websites.py` — Scrapes websites via Firecrawl with HTTP fallback

**Decision point**: **If a specific URL fails to scrape**:
- **Yes**: Mark as `scrape_failed`, continue with remaining companies. Do not let one failure block the batch.
- **No**: Continue processing

**Failure mode**: If Firecrawl API is unavailable, fall back to requests + BeautifulSoup (will not handle JS-rendered pages). If more than 80% of scrapes fail, log a warning and continue with whatever was retrieved.

---

## Step 5: Extract Structured Contact Info

Use Claude to extract structured data from the scraped content.

1. For each company's scraped content, send to Claude with a structured extraction prompt
2. Extract the following fields:
   - `company_name`: Official company name
   - `industry`: Detected industry/sector
   - `company_size`: Estimated employee count or range
   - `location`: Headquarters or primary location
   - `description`: One-sentence company description
   - `email`: General contact email or sales email
   - `phone`: Main phone number
   - `technologies`: Key technologies or products mentioned
3. Validate extracted data against expected types
4. Merge extracted data with the search result metadata

**Tool**: `tools/extract_contacts.py` — Uses Claude API for structured extraction from scraped content

**Failure mode**: If extraction fails for a company (LLM error, timeout), use whatever data was captured from the search snippet. Mark the record with `extraction_status: partial`.

---

## Step 6: Score and Rank Leads

Score each lead based on how well it matches the ideal customer profile.

1. For each lead, compute a match score (0-100) based on:
   - **Industry match** (0-30 points): Exact match = 30, related industry = 15, no match = 0
   - **Size match** (0-25 points): Within target range = 25, adjacent range = 12, no match = 0
   - **Location match** (0-20 points): Exact location = 20, same country = 10, no match = 0
   - **Keyword match** (0-25 points): Points proportional to keywords found in company description/technologies
2. Filter out leads below the `min_score` threshold
3. Sort remaining leads by score descending
4. Assign rank numbers

**Tool**: `tools/score_leads.py` — Computes match scores and ranks leads

**Failure mode**: If scoring fails for a record (missing data), assign a default score of 0 and include it at the bottom of the list with a note.

---

## Step 7: Generate Output CSV

Format the ranked leads into a CSV file.

1. Create the output CSV with columns: rank, company_name, website, industry, company_size, location, match_score, email, phone, description, scraped_at
2. Write to `output/leads_{YYYY-MM-DD_HHMM}.csv`
3. Generate `output/run_summary.json` with execution metadata:
   - Run timestamp
   - Input profile used
   - Total companies found
   - Total companies after filtering
   - Score distribution (min, max, avg, median)
   - Search queries used

**Tool**: `tools/generate_csv.py` — Formats data and writes CSV and summary JSON

**Failure mode**: If CSV write fails, output results as JSON to `output/leads_fallback.json` and log the CSV error.

---

## Step 8: Commit Results

Commit the output files back to the repository.

1. Stage all files in `output/`
2. Create a commit with message: `leads: {N} qualified leads for {industry} ({date})`
3. Push to the current branch

**Failure mode**: If git commit fails (no changes, auth error), log the failure. The output files are still available locally.

---

## Notes

- **Rate limiting**: The system spaces out API calls to respect rate limits. Brave Search allows 1 req/sec on free tier. Firecrawl varies by plan.
- **Data freshness**: Lead data is only as fresh as the company websites. Consider re-running weekly for active campaigns.
- **MCP preferences**: Brave Search and Firecrawl are preferred but not required. The system works with HTTP fallbacks.
- **Parallelization opportunity**: Steps 4 and 5 (scraping and extraction) can be parallelized per-company with Agent Teams. The sequential version processes one company at a time.
- **Privacy**: This system only collects publicly available business information from company websites. It does not scrape personal social media profiles or use data brokers.
