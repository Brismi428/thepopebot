# Content Repurposer — Workflow

Multi-channel content repurposing system that transforms blog posts into platform-optimized social media content.

## Inputs

- **blog_url** (string): Full URL of the blog post to repurpose. Must be publicly accessible.
- **author_handle** (string, optional): Author's social media handle to include in mentions (without @)
- **brand_hashtags** (list[string], optional): Brand-specific hashtags to include in every output

## Outputs

- **repurposed_content.json**: Single JSON file in `output/{timestamp}-{slug}.json` containing:
  - Source metadata (URL, title, generated timestamp)
  - Tone analysis (formality, technical level, humor, emotion, confidence)
  - Platform-optimized content for Twitter, LinkedIn, email, and Instagram
  - Character counts, hashtag suggestions, and formatting metadata for each platform

---

## Step 1: Scrape Blog Post

Fetch the blog post content from the provided URL and extract clean markdown.

1. Receive `blog_url` from workflow input (GitHub Actions dispatch, CLI arg, or Agent HQ issue)
2. Delegate to `content-scraper-specialist` subagent
3. The subagent calls `tools/scrape_blog_post.py --url <blog_url>`
4. The tool attempts Firecrawl API scraping first
5. If Firecrawl fails (API error, timeout, 404), fall back to HTTP + BeautifulSoup extraction
6. Extract clean markdown content, title, author, publish date from the page
7. Return structured output: `{status, markdown_content, title, author, publish_date, url, error}`

**Decision point**: **If scraping fails (both Firecrawl and HTTP fallback)**:
- **Yes (failed)**: Return error structure with `status: 'scrape_failed'` and detailed error message. Halt workflow and log failure.
- **No (succeeded)**: Continue to Step 2 with markdown content

**Tool**: `tools/scrape_blog_post.py` — Fetches and extracts content from blog post URL

**Failure mode**: URL is unreachable, paywalled, or returns invalid HTML. Both Firecrawl and HTTP fail.

**Fallback**: Return error structure, halt workflow, log full error details for debugging. Do NOT proceed with empty content.

---

## Step 2: Analyze Tone

Analyze the writing style and tone of the source content using Claude.

1. Receive `markdown_content` from Step 1
2. Delegate to `tone-analyzer-specialist` subagent
3. The subagent calls `tools/analyze_tone.py` with the markdown content
4. The tool uses Claude API with structured JSON output to analyze tone across dimensions:
   - formality: "formal" | "semi-formal" | "casual"
   - technical_level: "beginner" | "intermediate" | "advanced" | "expert"
   - humor_level: "none" | "low" | "medium" | "high"
   - primary_emotion: (string describing dominant emotion)
   - confidence: (float 0.0-1.0)
   - rationale: (string explaining the analysis)
5. Validate the response against JSON schema
6. Return tone analysis structure

**Decision point**: **If LLM API call fails or content is too short/garbled**:
- **Yes (failed)**: Return default neutral tone profile: `{formality: 'neutral', technical_level: 'general', humor_level: 'low', primary_emotion: 'informative', confidence: 0.5}`. Log warning and continue.
- **No (succeeded)**: Use the analyzed tone profile for platform generation

**Tool**: `tools/analyze_tone.py` — Analyzes content tone using Claude with structured extraction

**Failure mode**: LLM API error (rate limit, timeout, auth failure) or content is too short (< 50 chars) to analyze meaningfully

**Fallback**: Return default tone profile with low confidence (0.5). Log warning but continue workflow. Platform content will be generated with generic tone matching.

---

## Step 3: Generate Platform Content (Parallel with Agent Teams)

Generate optimized content for all 4 platforms in parallel using Agent Teams.

**Agent Teams mode**: If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set, the content-generator-specialist delegates to 4 teammates in parallel. Otherwise, sequential execution.

### Parallel Execution (Agent Teams Enabled)

1. The content-generator-specialist acts as **team lead**
2. Creates a shared task list with 4 tasks:
   - Task 1: Generate Twitter thread
   - Task 2: Generate LinkedIn post
   - Task 3: Generate email newsletter section
   - Task 4: Generate Instagram caption
3. Spawns 4 teammates, each with:
   - Source markdown content
   - Tone analysis from Step 2
   - Optional author_handle and brand_hashtags
   - Platform-specific constraints (char limits, hashtag counts, format rules)
4. Each teammate runs independently:
   - **twitter-generator**: Calls `tools/generate_twitter.py` → Returns thread array with tweet objects, hashtags, suggested mentions
   - **linkedin-generator**: Calls `tools/generate_linkedin.py` → Returns text, char_count, hashtags, hook, CTA
   - **email-generator**: Calls `tools/generate_email.py` → Returns subject_line, section_html, section_text, word_count, CTA
   - **instagram-generator**: Calls `tools/generate_instagram.py` → Returns caption, char_count, hashtags, line_break_count, emoji_count
5. Team lead monitors task status (polls `TaskList` until all 4 are `completed`)
6. Team lead collects all 4 results using `TaskGet` for each task
7. Team lead merges results into unified `platform_content` dict with keys: twitter, linkedin, email, instagram

### Sequential Fallback (Agent Teams Disabled or Failed)

1. The content-generator-specialist calls each tool sequentially:
   - Call `tools/generate_twitter.py` → wait for result
   - Call `tools/generate_linkedin.py` → wait for result
   - Call `tools/generate_email.py` → wait for result
   - Call `tools/generate_instagram.py` → wait for result
2. Merge results into unified `platform_content` dict

**Decision point**: **If one or more platform generators fail**:
- **Retry once**: For any failed platform, retry the tool call once
- **If still fails**: Include error structure for that platform: `{status: 'generation_failed', message: <error details>}`
- **Continue**: Do NOT halt entire workflow for single platform failure. Deliver successful platforms and log failed ones.

**Tools**:
- `tools/generate_twitter.py` — Generates Twitter thread matching source tone
- `tools/generate_linkedin.py` — Generates LinkedIn post with professional formatting
- `tools/generate_email.py` — Generates email newsletter section with HTML and plain text
- `tools/generate_instagram.py` — Generates Instagram caption with hashtags and emojis

**Failure mode**: One or more platform generators fail due to LLM API error, timeout, or validation failure (char count exceeded after generation)

**Fallback**: Retry failed platforms once. If still failing, include error structure in output for that platform. Partial success is acceptable — 3/4 platforms is better than all-or-nothing.

**Performance**:
- Sequential: ~52-74 seconds (4 LLM calls in series)
- Parallel (Agent Teams): ~25-37 seconds (4 LLM calls concurrent)

---

## Step 4: Assemble Output

Merge all generated content into a single JSON file and commit to repo.

1. Receive from previous steps:
   - `source_metadata` (from Step 1): url, title, author, publish_date
   - `tone_analysis` (from Step 2): all tone dimensions + confidence
   - `platform_content` (from Step 3): twitter, linkedin, email, instagram objects
2. Delegate to `output-assembler-specialist` subagent
3. The subagent calls `tools/assemble_output.py` with all inputs
4. The tool merges everything into unified JSON structure:
   ```json
   {
     "source_url": "...",
     "source_title": "...",
     "generated_at": "2026-02-11T13:32:00Z",
     "tone_analysis": {...},
     "twitter": {...},
     "linkedin": {...},
     "email": {...},
     "instagram": {...}
   }
   ```
5. Generate output filename: `output/{timestamp}-{slug}.json`
6. Slugify the source title to create a clean filename
7. Create `output/` directory if it doesn't exist
8. Write JSON file with pretty formatting (indent=2)
9. Validate JSON serialization before writing
10. Return output file path and summary stats (total_chars, platform_count)

**Decision point**: **If JSON serialization fails or file write fails**:
- **Yes (failed)**: Log full error details. Print the JSON output to stdout. Halt workflow with exit code 1. User can manually save from logs.
- **No (succeeded)**: Continue to Step 5 (commit)

**Tool**: `tools/assemble_output.py` — Merges all content into final JSON file

**Failure mode**: JSON serialization fails (malformed data), file write fails (permissions, disk full), or output directory cannot be created

**Fallback**: Print the complete output JSON to stdout so it's captured in logs. Log the error. Exit with non-zero code to signal failure. The user can manually save the output from the GitHub Actions logs.

---

## Step 5: Commit Results

Commit the output file to the repository.

1. Verify that output file was written successfully in Step 4
2. Stage ONLY the output file: `git add output/{timestamp}-{slug}.json`
3. Run `git status` to verify only the output file is staged
4. Commit with descriptive message: `"add: content repurposer output for {source_title} ({timestamp})"`
5. Pull with rebase before pushing: `git pull --rebase`
6. Push to the repository: `git push`

**Decision point**: **If git operations fail**:
- **Commit fails**: Log error. Check if there are no changes (file already committed). Exit gracefully.
- **Push fails (network, auth)**: Log error. Output file is committed locally but not pushed. Retry push on next workflow run.

**Failure mode**: Git commit fails (no changes, permissions), push fails (network, authentication, conflicts)

**Fallback**: If commit succeeds but push fails, the file is still committed locally. Next workflow run will push it. Log the push failure for visibility.

---

## Notes

- **Character count validation is critical**: Every platform generator must validate character counts BEFORE returning. Use `len()` on final strings. Account for URL shortening (Twitter: 23 chars).
- **Tone matching is the key differentiator**: The same blog post should sound formal on LinkedIn if the source was formal, casual on Instagram if the source was casual. Tone analysis drives generation quality.
- **Agent Teams is optional but recommended**: 4 independent platform generators = ideal parallelization candidate. 2x speedup with identical results and same token cost.
- **Partial success is acceptable**: If LinkedIn generation fails but Twitter/email/Instagram succeed, deliver the 3 successful platforms. Do not fail the entire run for one platform.
- **Firecrawl + HTTP fallback pattern**: Primary API with HTTP backup maximizes reliability. Most blog posts are scrapable with one of the two methods.
- **Secrets required**: `FIRECRAWL_API_KEY` (for scraping), `ANTHROPIC_API_KEY` (for LLM calls)
- **MCP alternatives**: Firecrawl MCP (preferred) or Fetch MCP + Puppeteer MCP (fallback). If no MCPs available, direct HTTP with Python `requests` + `beautifulsoup4`.
- **Cost per run**: ~$0.10-0.11 (Firecrawl: $0.01-0.02, Claude: ~$0.09 for tone + 4 platforms)
- **Execution time**: Sequential: ~52-74s, Parallel (Agent Teams): ~25-37s
