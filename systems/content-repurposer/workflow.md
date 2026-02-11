# Content Repurposer — Workflow

Multi-channel content repurposing system that transforms blog posts into platform-optimized social media content.

---

## Inputs

- **blog_url** (string, required): Full URL of the blog post to repurpose. Must be publicly accessible.
- **author_handle** (string, optional): Author's social media handle to include in mentions (without @)
- **brand_hashtags** (list of strings, optional): Brand-specific hashtags to include in every output

## Outputs

- **JSON file**: `output/{timestamp}-{slug}.json` containing all platform-optimized versions
  - Twitter thread with tweet-by-tweet breakdown
  - LinkedIn post with character count and hashtags
  - Email newsletter section (HTML + plain text)
  - Instagram caption with hashtags and formatting
  - Source metadata and tone analysis

---

## Step 1: Scrape Blog Post

**Purpose**: Fetch the blog post content from the provided URL and extract clean markdown.

**Delegate to**: `content-scraper-specialist` subagent

**Process**:
1. Validate the blog_url format (must be a valid HTTP/HTTPS URL)
2. Call `scrape_blog_post.py` with the URL
3. The tool attempts to fetch content using Firecrawl API
4. If Firecrawl fails, fall back to direct HTTP + BeautifulSoup extraction
5. Extract metadata: title, author, publish date
6. Convert extracted content to clean markdown format
7. Return structured data with content and metadata

**Success output**:
```json
{
  "status": "success",
  "markdown_content": "# Blog Post Title\n\nContent here...",
  "title": "Blog Post Title",
  "author": "Author Name",
  "publish_date": "2026-02-11",
  "url": "https://example.com/blog/post"
}
```

**Failure Modes**:
- URL is unreachable (404, timeout, network error)
- Content is behind a paywall or login wall
- Page has no extractable article content (homepage, search results, etc.)
- Both Firecrawl and HTTP fallback fail

**Fallback**:
- Return error status: `{"status": "error", "error": "Failed to fetch content: {details}", ...}`
- Halt workflow and report error to user via GitHub Actions output
- Do NOT proceed to tone analysis with no content

---

## Step 2: Analyze Tone

**Purpose**: Analyze the writing style and tone of the source content to enable accurate tone matching in generated outputs.

**Delegate to**: `tone-analyzer-specialist` subagent

**Process**:
1. Receive markdown_content from Step 1
2. Call `analyze_tone.py` with the content
3. Send content to Claude with structured JSON schema for tone analysis
4. Analyze across 5 dimensions:
   - **Formality**: formal | semi-formal | casual
   - **Technical level**: beginner | intermediate | advanced | expert
   - **Humor level**: none | low | medium | high
   - **Primary emotion**: e.g., informative, inspiring, urgent, playful
   - **Confidence**: 0.0-1.0 (how confident the analysis is)
5. Return structured tone profile with rationale

**Success output**:
```json
{
  "formality": "semi-formal",
  "technical_level": "intermediate",
  "humor_level": "low",
  "primary_emotion": "informative",
  "confidence": 0.85,
  "rationale": "The content uses professional language with occasional casual phrases..."
}
```

**Failure Modes**:
- LLM API error (rate limit, timeout, authentication failure)
- Content is too short or garbled to analyze meaningfully
- JSON schema validation fails on LLM response

**Fallback**:
- Retry LLM call once with exponential backoff (wait 5 seconds)
- If still fails, return default tone profile:
  ```json
  {
    "formality": "neutral",
    "technical_level": "general",
    "humor_level": "low",
    "primary_emotion": "informative",
    "confidence": 0.5,
    "rationale": "Using default tone profile due to analysis failure"
  }
  ```
- Log warning but continue workflow
- Quality may be reduced, but system remains functional

---

## Step 3: Generate Platform Content (Parallel Execution)

**Purpose**: Generate optimized content for all 4 platforms in parallel using Agent Teams for maximum speed.

**Execution Mode**: Agent Teams (4 parallel teammates)

**Coordinator**: `content-generator-specialist` subagent (team lead)

**Team Lead Process**:
1. Receive markdown_content, tone_analysis, author_handle, brand_hashtags from previous steps
2. Create shared task list with 4 independent platform generation tasks
3. Spawn 4 teammates in parallel:
   - `twitter-generator` teammate
   - `linkedin-generator` teammate
   - `email-generator` teammate
   - `instagram-generator` teammate
4. Wait for all teammates to complete (or timeout after 120 seconds)
5. Collect results from all teammates
6. Validate each platform output for required fields and character limits
7. Merge into unified platform_content dictionary

### Teammate 1: Twitter Thread Generation

**Tool**: `generate_twitter.py`

**Process**:
1. Analyze content length to determine if single tweet or thread is needed
2. Extract key points from markdown_content (3-5 main takeaways)
3. Generate opening hook tweet (must grab attention in first 140 chars)
4. Generate body tweets (one key point per tweet)
5. Generate closing CTA tweet (call-to-action)
6. Number tweets in "X/N" format
7. Match tone from tone_analysis (formal → professional voice, casual → conversational)
8. Add brand_hashtags if provided (max 2 hashtags per tweet to preserve space)
9. Suggest relevant industry hashtags (2-3 per thread, not per tweet)
10. Suggest accounts to mention if author_handle provided
11. Validate every tweet is <= 280 characters

**Output**:
```json
{
  "thread": [
    {"tweet_number": 1, "text": "🧵 Here's why...", "char_count": 125},
    {"tweet_number": 2, "text": "Key insight: ...", "char_count": 267}
  ],
  "total_tweets": 5,
  "hashtags": ["#ContentMarketing", "#DigitalStrategy"],
  "suggested_mentions": ["@IndustryLeader"]
}
```

**Failure handling**: Retry once on LLM error. If char count exceeds 280 for any tweet, truncate and add ellipsis with warning flag.

### Teammate 2: LinkedIn Post Generation

**Tool**: `generate_linkedin.py`

**Process**:
1. Extract main message and supporting points from content
2. Generate attention-grabbing hook (first 1-2 sentences before "see more" fold)
3. Write body content in LinkedIn-optimized format:
   - Short paragraphs (2-3 sentences each)
   - Line breaks for readability
   - Bullet points or numbered lists where appropriate
4. Match tone (LinkedIn skews professional even for casual content)
5. Include industry-relevant insights and takeaways
6. Add call-to-action (comment prompt, share request, or link to original post)
7. Generate 3-5 hashtags (mix of popular and niche)
8. Include brand_hashtags if provided
9. Target length: 1200-1400 characters (optimal for LinkedIn feed visibility)
10. Maximum: 3000 characters (hard LinkedIn limit)

**Output**:
```json
{
  "text": "Full LinkedIn post text with line breaks...",
  "char_count": 1285,
  "hashtags": ["#Marketing", "#ContentStrategy", "#B2B"],
  "hook": "Ever wonder why most content fails?",
  "cta": "What's your take on this approach? Share in the comments."
}
```

**Failure handling**: Retry once on error. If exceeds 3000 chars, truncate intelligently at sentence boundary. Target 1300 chars for best visibility.

### Teammate 3: Email Newsletter Section Generation

**Tool**: `generate_email.py`

**Process**:
1. Summarize main points from content (3-5 key takeaways)
2. Generate compelling subject line (40-60 chars, includes curiosity gap or benefit)
3. Write newsletter section in scannable format:
   - Clear subheadings
   - Short paragraphs (3-4 sentences max)
   - Bullet points for lists
   - Bold key phrases
4. Match tone but adjust for email context (slightly more direct/personal)
5. Include clear call-to-action with link to original post
6. Generate both HTML and plain text versions
7. Target length: 500-800 words (3-5 minute read)
8. Convert markdown to HTML for section_html
9. Count words in plain text version

**Output**:
```json
{
  "subject_line": "The one thing everyone gets wrong about content",
  "section_html": "<h2>Key Insights</h2><p>Content here...</p>",
  "section_text": "KEY INSIGHTS\n\nContent here...",
  "word_count": 672,
  "cta": "Read the full deep-dive on the blog: https://example.com/post"
}
```

**Failure handling**: Retry once on error. If word count exceeds 1000, summarize more aggressively. Always provide plain text fallback.

### Teammate 4: Instagram Caption Generation

**Tool**: `generate_instagram.py`

**Process**:
1. Extract visual storytelling elements from content
2. Generate caption that works WITHOUT the accompanying image (must be standalone)
3. Structure for Instagram best practices:
   - Hook in first 1-2 lines (before "more" fold)
   - Body with line breaks every 2-3 sentences
   - Strategic use of emojis (3-5 per caption, not excessive)
   - Lists or numbered points where appropriate
4. Match tone (Instagram skews more casual and visual even for professional content)
5. Generate call-to-action (comment prompt, tag a friend, save for later)
6. Generate 10-15 hashtags (mix of broad, niche, and branded)
   - First 3-5 hashtags: high-traffic, broad reach
   - Next 5-7 hashtags: niche, targeted audience
   - Last 2-3 hashtags: branded or campaign-specific
7. Include brand_hashtags if provided (at end of hashtag list)
8. Format hashtags: lowercase, alphanumeric + underscores only
9. Target length: 1500-2000 characters (ideal for Instagram)
10. Maximum: 2200 characters (hard Instagram limit)
11. Count line breaks and emojis for formatting validation

**Output**:
```json
{
  "caption": "Ever wondered why...?\n\n💡 Here's what changed...",
  "char_count": 1847,
  "hashtags": [
    "#marketing", "#contentcreator", "#digitalmarketing",
    "#contentstrategy", "#socialmediatips", "#marketingtips",
    "#businessgrowth", "#entrepreneurship", "#contentmarketing",
    "#instagramtips", "#YourBrand"
  ],
  "line_break_count": 6,
  "emoji_count": 4
}
```

**Failure handling**: Retry once on error. If exceeds 2200 chars, truncate at sentence boundary. Validate hashtag format (no spaces, special chars).

### Team Lead: Result Merging

After all 4 teammates complete:

1. Validate each platform output has required fields
2. Check character counts are within limits
3. If any teammate failed:
   - Retry that specific platform once
   - If still fails, include error structure: `{"status": "generation_failed", "error": "..."}`
   - Do NOT halt workflow for single platform failure
4. Merge all outputs into unified dictionary:
   ```json
   {
     "twitter": {...},
     "linkedin": {...},
     "email": {...},
     "instagram": {...}
   }
   ```
5. Log token usage for cost tracking
6. Return merged platform_content to main workflow

**Sequential Fallback**:

If Agent Teams is disabled or fails entirely:
1. Call `generate_twitter.py` sequentially
2. Call `generate_linkedin.py` sequentially
3. Call `generate_email.py` sequentially
4. Call `generate_instagram.py` sequentially
5. Merge results (same validation as parallel mode)

Wall time: 40-60s sequential vs 15s parallel, but results are identical.

---

## Step 4: Assemble Output

**Purpose**: Merge all generated content into a single JSON file and commit to repository.

**Delegate to**: `output-assembler-specialist` subagent

**Process**:
1. Receive inputs from all previous steps:
   - source_metadata (from Step 1)
   - tone_analysis (from Step 2)
   - platform_content (from Step 3)
2. Generate timestamp: `YYYYMMDD-HHMMSS` format in UTC
3. Generate slug from source title: lowercase, hyphens, alphanumeric only, max 50 chars
4. Create output filename: `output/{timestamp}-{slug}.json`
5. Merge all data into unified structure:
   ```json
   {
     "source_url": "...",
     "source_title": "...",
     "source_author": "...",
     "generated_at": "2026-02-11T13:32:00Z",
     "tone_analysis": {...},
     "twitter": {...},
     "linkedin": {...},
     "email": {...},
     "instagram": {...}
   }
   ```
6. Validate JSON structure (all required keys present)
7. Create `output/` directory if it doesn't exist
8. Write JSON file with pretty formatting (indent=2, ensure_ascii=False for emoji support)
9. Calculate summary stats:
   - Total characters across all platforms
   - Number of successfully generated platforms
   - Token usage (if available)
10. Return output path and stats for GitHub Actions summary

**Success output**:
```json
{
  "output_path": "output/20260211-133200-awesome-blog-post.json",
  "total_chars": 8472,
  "platform_count": 4,
  "status": "success"
}
```

**Failure Modes**:
- JSON serialization fails (invalid data structure)
- File write fails (permissions, disk full, directory doesn't exist)
- Validation fails (missing required fields)

**Fallback**:
- On write failure: Print full JSON to stdout with clear markers
- Log detailed error to GitHub Actions
- User can manually save JSON from workflow logs
- Mark workflow as failed but preserve all generated content

---

## Execution Paths

### Path 1: GitHub Actions (Primary)

Triggered via `workflow_dispatch` with inputs:
1. User provides blog_url, optional author_handle and brand_hashtags via Actions UI
2. GitHub Actions spins up Python environment
3. Installs dependencies from requirements.txt
4. Sets environment variables from GitHub Secrets (FIRECRAWL_API_KEY, ANTHROPIC_API_KEY)
5. Executes workflow with Claude Code CLI
6. Commits output JSON to `output/` directory
7. Creates GitHub Actions summary with stats and link to output file
8. Sends failure notification if any step errors

### Path 2: Local CLI

For development and testing:
```bash
# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run workflow
claude workflow.md --var blog_url="https://example.com/blog/post"
```

Output is written to `output/` directory in local repo.

### Path 3: Agent HQ (Issue-Driven)

1. Open a GitHub Issue with label `content-repurpose`
2. Issue body format:
   ```
   Blog URL: https://example.com/blog/post
   Author Handle: johndoe (optional)
   Brand Hashtags: YourBrand, Marketing (optional)
   ```
3. Agent HQ parses issue body
4. Executes workflow via GitHub Actions
5. Opens draft PR with generated output
6. Comments on issue with PR link and summary

---

## Failure Recovery

### Total Failure (No Output Generated)

If scraping fails and no content is extracted:
- Halt workflow immediately after Step 1
- Log clear error message: "Failed to fetch content from {url}: {error}"
- GitHub Actions marks workflow as failed
- User receives notification with error details
- No partial output is generated

### Partial Failure (Some Platforms Missing)

If 1-3 platforms fail but others succeed:
- Continue workflow with available platform content
- Failed platforms show error structure in final JSON:
  ```json
  {
    "twitter": {"status": "generation_failed", "error": "LLM timeout"},
    "linkedin": {...successful output...},
    ...
  }
  ```
- Workflow completes but GitHub Actions shows warning status
- User can retry individual platforms manually if needed

### Tone Analysis Failure

If tone analysis fails:
- Use default tone profile (neutral across all dimensions)
- Log warning: "Using default tone profile due to analysis failure"
- Continue with generation (quality may be slightly reduced)
- Mark final output with `"tone_analysis_fallback": true` flag

---

## Performance & Cost

### Execution Time

**With Agent Teams (Parallel)**:
- Step 1 (Scrape): 3-5 seconds
- Step 2 (Tone): 8-12 seconds
- Step 3 (Generate - Parallel): 12-18 seconds
- Step 4 (Assemble): 1-2 seconds
- **Total**: ~25-37 seconds

**Without Agent Teams (Sequential)**:
- Step 1: 3-5 seconds
- Step 2: 8-12 seconds
- Step 3 (Generate - Sequential): 40-55 seconds
- Step 4: 1-2 seconds
- **Total**: ~52-74 seconds

**Speedup**: ~2x faster with Agent Teams for generation step.

### API Cost Estimates

Per run (single blog post):
- Firecrawl API: $0.01-0.02 per scrape
- Claude API:
  - Tone analysis: ~500 input tokens + 200 output tokens = $0.01
  - Twitter generation: ~1000 input + 500 output = $0.02
  - LinkedIn generation: ~1000 input + 300 output = $0.02
  - Email generation: ~1000 input + 600 output = $0.02
  - Instagram generation: ~1000 input + 400 output = $0.02
  - Total Claude: ~$0.09 per run

**Total per run**: ~$0.10-0.11

Assumes Claude Sonnet 4 pricing: $3/MTok input, $15/MTok output

### GitHub Actions Minutes

Per run: ~1 minute (including setup + execution + commit)

Monthly cost if running 100x/month:
- 100 runs × $0.11/run = $11 API costs
- 100 minutes GitHub Actions (well within free tier: 2000 min/month private, unlimited public)

---

## Success Metrics

Track these metrics in GitHub Actions summaries:

1. **Success Rate**: % of runs that complete without errors
2. **Platform Coverage**: % of runs that generate all 4 platforms successfully
3. **Average Execution Time**: Track trend over time
4. **Character Count Distribution**: Track Twitter thread length, LinkedIn post length
5. **Tone Analysis Confidence**: Average confidence score across runs
6. **API Error Rate**: % of runs that hit API failures (rate limits, timeouts)

Log these to a tracking file: `metrics/run_log.jsonl` (one line per run).
