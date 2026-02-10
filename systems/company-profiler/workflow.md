# Company Profiler — Workflow

Takes a company URL as input, scrapes the website, extracts key business information, and outputs a structured company profile as a JSON file committed back to the repo.

## Inputs

- **company_url** (str): The URL of the company website to profile (e.g., `https://example.com`)
- **tracked_companies** (str): Optional — path to a JSON file listing URLs to re-profile in batch mode

## Outputs

- **company_profile.json**: Structured JSON file with extracted business information, committed to `output/`
- **batch_profiles/**: Directory of JSON profiles when running in batch mode (cron)

---

## Step 1: Validate Input

Parse and validate the input URL or batch file.

1. Check if the input is a single URL or a path to a tracked companies file
2. **If single URL**: Validate URL format (must start with `http://` or `https://`)
3. **If batch file**: Load the JSON file from `data/tracked_companies.json`, extract the list of URLs
4. For each URL, normalize it (remove trailing slashes, ensure scheme present)

**Decision point**: **If batch mode (multiple URLs)**:
- **Yes**: Loop through each URL and execute Steps 2-5 for each. Results go to `output/batch_profiles/`
- **No**: Execute Steps 2-5 once for the single URL. Result goes to `output/company_profile.json`

**Failure mode**: If URL is invalid, log the error and skip that URL. Continue with remaining URLs in batch mode.

---

## Step 2: Scrape Website

Fetch the company's website content using the best available web scraping tool.

1. Check available MCPs/tools (see CLAUDE.md for MCP configuration):
   - **Preferred**: Firecrawl MCP (handles JS rendering, returns clean markdown)
   - **Alternative**: Puppeteer MCP (browser-based, good for dynamic sites)
   - **Fallback**: Direct HTTP fetch via `requests` + `beautifulsoup4`
2. Scrape the main page (homepage)
3. Identify and scrape key subpages:
   - `/about` or `/about-us` — company description, team info
   - `/pricing` — pricing model
   - `/careers` or `/jobs` — job postings (tech stack signals, team size)
   - `/products` or `/services` — what they do
4. Collect all scraped content as markdown text

**Tool**: `tools/scrape_website.py` — Scrapes a URL and returns clean text content

**Failure mode**: If primary scraping tool fails, try the fallback. If all scraping fails, log the error and output a partial profile with whatever data was collected. If specific subpages return 404, skip them and continue.

---

## Step 3: Extract Business Information

Process the scraped content to extract structured business data.

1. Analyze the scraped content using Claude to extract:
   - **Company Name**: Official company name
   - **Description**: What the company does (1-2 sentences)
   - **Industry**: Primary industry/sector
   - **Products/Services**: List of main offerings
   - **Target Market**: Who they sell to (B2B, B2C, enterprise, SMB, etc.)
   - **Pricing Model**: Free, freemium, subscription, usage-based, enterprise, etc.
   - **Team Size Signals**: Any indicators of team size (job posting count, about page mentions)
   - **Tech Stack**: Technologies mentioned in job postings, built-with data, or site source
   - **Founded**: Year founded if available
   - **Location**: HQ location if available
   - **Social Links**: LinkedIn, Twitter, GitHub, etc.
2. Structure the extracted data as a JSON object
3. Assign confidence scores (high/medium/low) to each field based on data quality

**Tool**: `tools/extract_profile.py` — Processes scraped content and returns structured profile data

**Failure mode**: If extraction fails for specific fields, mark them as `null` with `"confidence": "none"`. The profile should still be valid JSON with whatever was successfully extracted.

---

## Step 4: Enrich Profile (Optional)

Supplement the scraped data with additional sources if available.

1. **If Brave Search MCP is available**: Search for `"{company_name}" company info` to find:
   - Crunchbase/LinkedIn profiles for funding and team data
   - Recent news articles
   - Review sites (G2, Capterra) for product details
2. **If built-with data is available**: Check for technology stack indicators
3. Merge enrichment data with the scraped profile, preferring higher-confidence sources
4. Update confidence scores for enriched fields

**Tool**: `tools/enrich_profile.py` — Searches additional sources and enriches the profile

**Decision point**: **If no search MCP is available**:
- **Yes**: Skip enrichment, proceed with scraped data only
- **No**: Run enrichment and merge results

**Failure mode**: Enrichment is optional. If it fails entirely, proceed with the scrape-only profile. Log what enrichment was attempted and what failed.

---

## Step 5: Output Results

Format and save the final company profile.

1. Assemble the final JSON profile:
   ```json
   {
     "url": "https://example.com",
     "scraped_at": "2025-01-15T10:30:00Z",
     "company_name": "Example Corp",
     "description": "...",
     "industry": "...",
     "products_services": ["..."],
     "target_market": "...",
     "pricing_model": "...",
     "team_size_signals": "...",
     "tech_stack": ["..."],
     "founded": "...",
     "location": "...",
     "social_links": {},
     "confidence": {},
     "enrichment_sources": []
   }
   ```
2. **If single URL mode**: Write to `output/company_profile.json`
3. **If batch mode**: Write each profile to `output/batch_profiles/{domain}.json`
4. Generate a summary log entry
5. Commit results back to the repo

**Tool**: `tools/output_profile.py` — Formats and writes the profile JSON

**Failure mode**: If file write fails, output the JSON to stdout as a fallback. If git commit fails, log the error — the output files are still available locally.

---

## Notes

- The system checks the MCP registry to select the best scraping and search tools
- All web scraping respects `robots.txt` where possible
- Rate limiting: when running batch mode, add a 2-second delay between URLs to avoid rate limits
- Profiles are idempotent — re-profiling the same URL overwrites the previous profile
- The `tracked_companies.json` file can be updated manually or by other WAT systems
