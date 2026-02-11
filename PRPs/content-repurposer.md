name: "content-repurposer"
description: |

## Purpose
WAT System PRP (Product Requirements Prompt) — Multi-channel content repurposing system that transforms blog posts into platform-optimized social media content.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a system that accepts a blog post URL, extracts and analyzes the content, identifies the tone/style, and generates platform-optimized versions for Twitter (thread), LinkedIn (post), email newsletter (section), and Instagram (caption). Each output respects platform-specific character limits, format conventions, and includes relevant hashtags and mention suggestions. Output is a single JSON file with one key per platform. No auto-posting — generation only.

## Why
- **Business value**: Automates the tedious process of manually reformatting content for multiple social platforms
- **Manual process automated**: Content creators spend hours rewriting a single blog post for 4+ platforms, manually counting characters and adjusting tone
- **Who benefits**: Marketing teams, content creators, social media managers who need to maximize content reach across platforms
- **Frequency**: Daily or on-demand per blog post published

## What
User provides a blog post URL. System fetches content, analyzes tone (formal/casual, technical/accessible, humorous/serious), and generates four platform-optimized versions. Each version maintains the core message but adapts format, length, tone matching, hashtags, and suggested mentions to platform best practices.

### Success Criteria
- [ ] Extracts clean content from any blog post URL (handles different CMS platforms)
- [ ] Accurately identifies source content tone (returns structured tone analysis: formality, technical level, humor level)
- [ ] Generates Twitter thread that fits platform limits (280 chars/tweet, numbered sequence, hooks and CTAs)
- [ ] Generates LinkedIn post (1300 char target, professional tone, industry-relevant hashtags)
- [ ] Generates email newsletter section (500-800 words, clear structure, call-to-action)
- [ ] Generates Instagram caption (2200 char limit, line breaks for readability, 10-15 relevant hashtags)
- [ ] All outputs in a single JSON file: `{twitter: {}, linkedin: {}, email: {}, instagram: {}}`
- [ ] System runs autonomously via GitHub Actions on schedule or manual dispatch
- [ ] Results are committed back to repo in `output/{timestamp}-{slug}.json`
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs

```yaml
- name: "blog_url"
  type: "string (URL)"
  source: "manual input via CLI, GitHub Actions dispatch, or Agent HQ issue"
  required: true
  description: "Full URL of the blog post to repurpose. Must be publicly accessible."
  example: "https://example.com/blog/my-awesome-post"

- name: "author_handle"
  type: "string"
  source: "manual input (optional)"
  required: false
  description: "Author's social media handle to include in mentions (without @)"
  example: "johndoe"

- name: "brand_hashtags"
  type: "list[string]"
  source: "manual input (optional)"
  required: false
  description: "Brand-specific hashtags to include in every output"
  example: ["YourBrand", "ContentMarketing"]
```

## Outputs

```yaml
- name: "repurposed_content.json"
  type: "JSON"
  destination: "repo commit to output/{timestamp}-{slug}.json"
  description: "Single JSON file containing all platform-optimized versions with metadata"
  example: |
    {
      "source_url": "https://example.com/blog/post",
      "source_title": "My Awesome Post",
      "generated_at": "2026-02-11T13:32:00Z",
      "tone_analysis": {
        "formality": "semi-formal",
        "technical_level": "intermediate",
        "humor_level": "low",
        "primary_emotion": "informative",
        "confidence": 0.85
      },
      "twitter": {
        "thread": [
          {"tweet_number": 1, "text": "🧵 Thread opening...", "char_count": 125},
          {"tweet_number": 2, "text": "Key point 1...", "char_count": 267}
        ],
        "total_tweets": 5,
        "hashtags": ["#ContentMarketing", "#SEO"],
        "suggested_mentions": ["@Industry_Leader"]
      },
      "linkedin": {
        "text": "Full LinkedIn post text...",
        "char_count": 1285,
        "hashtags": ["#Marketing", "#ContentStrategy"],
        "hook": "First sentence that grabs attention",
        "cta": "What's your take on this? Share in comments."
      },
      "email": {
        "subject_line": "Suggested email subject",
        "section_html": "<h2>Title</h2><p>Content...</p>",
        "section_text": "Plain text version...",
        "word_count": 672,
        "cta": "Read the full post here: [link]"
      },
      "instagram": {
        "caption": "Instagram caption text with line breaks...",
        "char_count": 1847,
        "hashtags": ["#Marketing", "#ContentCreation", "#SocialMedia"],
        "line_break_count": 4,
        "emoji_count": 3
      }
    }
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://developer.twitter.com/en/docs/twitter-api/v2/tweet-caps"
  why: "Twitter character limits (280 per tweet), thread best practices"

- url: "https://www.linkedin.com/help/linkedin/answer/a521928"
  why: "LinkedIn post limits (3000 chars, 1300 recommended for visibility)"

- url: "https://help.instagram.com/1631821640426723"
  why: "Instagram caption limits (2200 chars), hashtag best practices (10-15 optimal)"

- doc: "config/mcp_registry.md"
  why: "Check for Firecrawl (web scraping), Fetch (HTTP fallback), Anthropic (tone analysis + generation)"

- doc: "library/patterns.md"
  why: "Scrape > Process > Output pattern fits this workflow"

- doc: "library/tool_catalog.md"
  why: "firecrawl_scrape for content extraction, llm_prompt for tone analysis and generation"
```

### Workflow Pattern Selection
```yaml
pattern: "Scrape > Process > Output"
rationale: "Fits perfectly: fetch URL content (scrape), analyze tone + generate variants (process), save JSON (output)"
modifications: "Process step splits into two subagents: tone-analyzer (analyze source) and content-generator (generate 4 platform variants)"
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "web scraping"
    primary_mcp: "firecrawl"
    alternative_mcp: "puppeteer"
    fallback: "Direct HTTP with requests + beautifulsoup4"
    secret_name: "FIRECRAWL_API_KEY"

  - name: "llm generation"
    primary_mcp: "anthropic"
    alternative_mcp: "openai"
    fallback: "None — LLM is required"
    secret_name: "ANTHROPIC_API_KEY"
```

### Known Gotchas & Constraints
```
# CRITICAL: Twitter thread generation must handle edge cases — single tweet vs multi-tweet logic
# CRITICAL: Character count must be EXACT — use len() on final strings, account for URL shortening (23 chars)
# CRITICAL: Tone analysis must produce structured output — JSON schema validation required
# CRITICAL: LinkedIn line breaks render differently in feed vs full post — test visibility
# CRITICAL: Instagram hashtags must be lowercase, no spaces, alphanumeric + underscores only
# CRITICAL: Firecrawl API rate limit: 500 requests/hour on standard plan — single request per run is safe
# CRITICAL: Blog post scraping may fail on paywalled or JS-heavy sites — must handle gracefully
# CRITICAL: Anthropic Claude Sonnet 4 max output tokens: 8192 — sufficient for all 4 platforms in one call
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
```

---

## System Design

### Subagent Architecture

```yaml
subagents:
  - name: "content-scraper-specialist"
    description: "Delegate when you need to fetch and extract clean content from a blog post URL"
    tools: "Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Call scrape_blog_post.py with the target URL"
      - "Validate that content was extracted successfully"
      - "Return clean markdown content + metadata (title, author, publish date)"
      - "Handle scraping errors gracefully (return error structure if fetch fails)"
    inputs: "blog_url: str"
    outputs: "dict with markdown_content, title, author, publish_date, url"

  - name: "tone-analyzer-specialist"
    description: "Delegate when you need to analyze the tone, style, and writing characteristics of content"
    tools: "Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Call analyze_tone.py with the markdown content"
      - "Return structured tone analysis (formality, technical level, humor, emotion, confidence)"
      - "Provide clear rationale for each dimension"
    inputs: "markdown_content: str"
    outputs: "dict with formality, technical_level, humor_level, primary_emotion, confidence, rationale"

  - name: "content-generator-specialist"
    description: "Delegate when you need to generate platform-optimized content variants from source material"
    tools: "Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Call generate_platform_content.py with content, tone analysis, and platform targets"
      - "Generate all 4 platform variants in a single call (efficient token usage)"
      - "Apply tone matching — output style mirrors source tone"
      - "Validate character counts before returning"
      - "Include hashtag and mention suggestions"
    inputs: "markdown_content: str, tone_analysis: dict, author_handle: str (optional), brand_hashtags: list (optional)"
    outputs: "dict with twitter, linkedin, email, instagram keys, each containing platform-specific formatted content"

  - name: "output-assembler-specialist"
    description: "Delegate when you need to merge all generated content into the final JSON output file"
    tools: "Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Merge source metadata, tone analysis, and all platform content into single JSON structure"
      - "Generate output filename: output/{timestamp}-{slug}.json"
      - "Write JSON file with pretty formatting (indent=2)"
      - "Validate JSON structure before writing"
      - "Return output file path and summary stats"
    inputs: "source_metadata: dict, tone_analysis: dict, platform_content: dict"
    outputs: "dict with output_path: str, total_chars: int, platform_count: int"
```

### Agent Teams Analysis
```yaml
independent_tasks:
  - "Twitter thread generation"
  - "LinkedIn post generation"
  - "Email newsletter section generation"
  - "Instagram caption generation"

independent_task_count: 4
recommendation: "Use Agent Teams for platform content generation"
rationale: "4 independent platform-specific generation tasks — each takes ~10-15s with LLM call = 40-60s sequential vs 15s parallel. Meaningful speedup. Each platform can be generated independently once tone analysis is complete. Merge step is simple concatenation into JSON structure."

team_lead_responsibilities:
  - "After tone analysis completes, create shared task list with 4 platform generation tasks"
  - "Spawn 4 teammates in parallel, each generating one platform variant"
  - "Collect all 4 results and merge into unified JSON structure"
  - "Run validation on final merged output (character counts, required fields)"

teammates:
  - name: "twitter-generator"
    task: "Generate Twitter thread from content and tone analysis. Return thread array with tweet_number, text, char_count for each tweet. Include hashtags and suggested_mentions."
    inputs: "markdown_content, tone_analysis, author_handle, brand_hashtags"
    outputs: "dict with thread: list[dict], total_tweets: int, hashtags: list, suggested_mentions: list"

  - name: "linkedin-generator"
    task: "Generate LinkedIn post from content and tone analysis. Return text, char_count, hashtags, hook, cta. Target 1300 chars for optimal visibility."
    inputs: "markdown_content, tone_analysis, brand_hashtags"
    outputs: "dict with text: str, char_count: int, hashtags: list, hook: str, cta: str"

  - name: "email-generator"
    task: "Generate email newsletter section from content and tone analysis. Return subject_line, section_html, section_text, word_count, cta. Target 500-800 words."
    inputs: "markdown_content, tone_analysis, source_url"
    outputs: "dict with subject_line: str, section_html: str, section_text: str, word_count: int, cta: str"

  - name: "instagram-generator"
    task: "Generate Instagram caption from content and tone analysis. Return caption, char_count, hashtags, line_break_count, emoji_count. Target 1500-2000 chars with 10-15 hashtags."
    inputs: "markdown_content, tone_analysis, brand_hashtags"
    outputs: "dict with caption: str, char_count: int, hashtags: list, line_break_count: int, emoji_count: int"

# Sequential fallback is supported: if Agent Teams fails or is disabled, generate platforms sequentially with the content-generator-specialist subagent calling generate_platform_content.py once with all platforms.
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "workflow_dispatch"
    config:
      inputs:
        blog_url:
          description: "Blog post URL to repurpose"
          required: true
        author_handle:
          description: "Author social media handle (optional)"
          required: false
        brand_hashtags:
          description: "Comma-separated brand hashtags (optional)"
          required: false
    description: "Manual trigger via GitHub Actions UI or API for on-demand repurposing"

  - type: "schedule"
    config: "0 9 * * 1"
    description: "Weekly Monday 9 AM UTC — check for new blog posts in a feed and repurpose automatically (future enhancement)"
```

---

## Implementation Blueprint

### Workflow Steps

```yaml
steps:
  - name: "Scrape Blog Post"
    description: "Fetch the blog post content from the provided URL and extract clean markdown"
    subagent: "content-scraper-specialist"
    tools: ["scrape_blog_post.py"]
    inputs: "blog_url (from user input)"
    outputs: "dict with markdown_content, title, author, publish_date, url"
    failure_mode: "URL is unreachable, paywalled, or returns invalid HTML"
    fallback: "Return error structure with status: 'scrape_failed', message: {error details}. Halt workflow and report to user."

  - name: "Analyze Tone"
    description: "Analyze the writing style and tone of the source content using Claude"
    subagent: "tone-analyzer-specialist"
    tools: ["analyze_tone.py"]
    inputs: "markdown_content (from Scrape step)"
    outputs: "dict with formality, technical_level, humor_level, primary_emotion, confidence, rationale"
    failure_mode: "LLM API error or content is too short/garbled to analyze"
    fallback: "Return default tone profile: {formality: 'neutral', technical_level: 'general', humor_level: 'low', primary_emotion: 'informative', confidence: 0.5}. Log warning and continue."

  - name: "Generate Platform Content (Parallel)"
    description: "Generate optimized content for all 4 platforms in parallel using Agent Teams"
    subagent: "Agent Teams (content-generator-specialist spawns 4 teammates)"
    tools: ["generate_twitter.py", "generate_linkedin.py", "generate_email.py", "generate_instagram.py"]
    inputs: "markdown_content, tone_analysis, author_handle, brand_hashtags"
    outputs: "dict with twitter, linkedin, email, instagram keys"
    failure_mode: "One or more platform generators fail due to LLM API error or timeout"
    fallback: "If any teammate fails, retry that platform once. If still fails, include error structure for that platform: {status: 'generation_failed', message: {error}}. Do NOT halt entire workflow for single platform failure."

  - name: "Assemble Output"
    description: "Merge all generated content into a single JSON file and commit to repo"
    subagent: "output-assembler-specialist"
    tools: ["assemble_output.py"]
    inputs: "source_metadata (from Scrape), tone_analysis (from Analyze), platform_content (from Generate)"
    outputs: "output file path and summary stats"
    failure_mode: "JSON serialization fails or file write fails"
    fallback: "Log full error, print output to stdout as JSON, halt workflow. User can manually save from logs."
```

### Tool Specifications

```yaml
tools:
  - name: "scrape_blog_post.py"
    purpose: "Fetch and extract clean content from a blog post URL"
    catalog_pattern: "firecrawl_scrape"
    inputs:
      - "url: str — Target blog post URL"
    outputs: "JSON: {status: 'success'|'error', markdown_content: str, title: str, author: str, publish_date: str, url: str, error: str|null}"
    dependencies: ["firecrawl-py", "httpx", "beautifulsoup4"]
    mcp_used: "firecrawl"
    error_handling: "Try Firecrawl API first. On failure (API error, 404, timeout), fall back to direct HTTP + BeautifulSoup extraction. If both fail, return error status with details."

  - name: "analyze_tone.py"
    purpose: "Analyze tone and writing style of content using Claude"
    catalog_pattern: "llm_prompt with structured_extract"
    inputs:
      - "markdown_content: str — Content to analyze"
    outputs: "JSON: {formality: str, technical_level: str, humor_level: str, primary_emotion: str, confidence: float, rationale: str}"
    dependencies: ["anthropic"]
    mcp_used: "anthropic"
    error_handling: "Retry LLM call once on transient errors (rate limit, timeout). If fails, return default tone profile with confidence: 0.0."

  - name: "generate_twitter.py"
    purpose: "Generate Twitter thread from content and tone"
    catalog_pattern: "llm_prompt"
    inputs:
      - "markdown_content: str — Source content"
      - "tone_analysis: dict — Tone profile"
      - "author_handle: str — Optional author handle"
      - "brand_hashtags: list[str] — Optional brand tags"
    outputs: "JSON: {thread: list[{tweet_number: int, text: str, char_count: int}], total_tweets: int, hashtags: list, suggested_mentions: list}"
    dependencies: ["anthropic"]
    mcp_used: "anthropic"
    error_handling: "Retry once on LLM error. Validate each tweet is <= 280 chars. If any tweet exceeds, truncate and add '...' flag."

  - name: "generate_linkedin.py"
    purpose: "Generate LinkedIn post from content and tone"
    catalog_pattern: "llm_prompt"
    inputs:
      - "markdown_content: str"
      - "tone_analysis: dict"
      - "brand_hashtags: list[str]"
    outputs: "JSON: {text: str, char_count: int, hashtags: list, hook: str, cta: str}"
    dependencies: ["anthropic"]
    mcp_used: "anthropic"
    error_handling: "Retry once on error. Target 1300 chars. If exceeds 3000 chars, truncate with ellipsis."

  - name: "generate_email.py"
    purpose: "Generate email newsletter section from content"
    catalog_pattern: "llm_prompt"
    inputs:
      - "markdown_content: str"
      - "tone_analysis: dict"
      - "source_url: str — Link back to original post"
    outputs: "JSON: {subject_line: str, section_html: str, section_text: str, word_count: int, cta: str}"
    dependencies: ["anthropic", "markdown"]
    mcp_used: "anthropic"
    error_handling: "Retry once on error. Convert generated markdown to HTML for section_html. Provide plain text fallback."

  - name: "generate_instagram.py"
    purpose: "Generate Instagram caption from content and tone"
    catalog_pattern: "llm_prompt"
    inputs:
      - "markdown_content: str"
      - "tone_analysis: dict"
      - "brand_hashtags: list[str]"
    outputs: "JSON: {caption: str, char_count: int, hashtags: list, line_break_count: int, emoji_count: int}"
    dependencies: ["anthropic"]
    mcp_used: "anthropic"
    error_handling: "Retry once on error. Validate caption <= 2200 chars. Count line breaks and emojis. Include 10-15 hashtags."

  - name: "assemble_output.py"
    purpose: "Merge all content into final JSON and write to file"
    catalog_pattern: "json_read_write"
    inputs:
      - "source_metadata: dict"
      - "tone_analysis: dict"
      - "platform_content: dict"
      - "output_dir: str — Default: output/"
    outputs: "JSON: {output_path: str, total_chars: int, platform_count: int}"
    dependencies: ["python stdlib only"]
    mcp_used: "none"
    error_handling: "Validate JSON serialization. Create output_dir if missing. On write failure, print JSON to stdout and log error."
```

### Per-Tool Pseudocode

```python
# scrape_blog_post.py
def main():
    # PATTERN: firecrawl_scrape with HTTP fallback
    # Step 1: Parse input URL
    args = parse_args()
    url = args.url

    # Step 2: Try Firecrawl API
    # GOTCHA: Firecrawl returns markdown in result["markdown"], metadata in result["metadata"]
    try:
        result = firecrawl_scrape(url, mode="scrape")
        return {
            "status": "success",
            "markdown_content": result["markdown"],
            "title": result["metadata"].get("title", ""),
            "author": result["metadata"].get("author", ""),
            "publish_date": result["metadata"].get("publishedTime", ""),
            "url": url,
            "error": None
        }
    except Exception as e:
        # Step 3: Fallback to HTTP + BeautifulSoup
        # CRITICAL: Extract <article>, <main>, or first <div> with substantial text
        try:
            resp = requests.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            article = soup.find("article") or soup.find("main")
            markdown_content = html_to_markdown(article.get_text())
            return {"status": "success", "markdown_content": markdown_content, ...}
        except Exception as fallback_error:
            return {"status": "error", "error": str(fallback_error), ...}

# analyze_tone.py
def main():
    # PATTERN: llm_prompt with structured JSON output
    # CRITICAL: Use structured_extract pattern with JSON schema validation
    schema = {
        "type": "object",
        "properties": {
            "formality": {"type": "string", "enum": ["formal", "semi-formal", "casual"]},
            "technical_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced", "expert"]},
            "humor_level": {"type": "string", "enum": ["none", "low", "medium", "high"]},
            "primary_emotion": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"}
        },
        "required": ["formality", "technical_level", "humor_level", "primary_emotion", "confidence"]
    }

    result = structured_extract(
        content=markdown_content,
        schema=schema,
        instructions="Analyze the tone and writing style of this content",
        retries=2
    )
    return result["data"]

# generate_twitter.py (and linkedin, email, instagram)
def main():
    # PATTERN: llm_prompt with platform-specific constraints
    # CRITICAL: Character limits MUST be validated before returning
    # Twitter: 280 per tweet, thread format with numbering
    system_prompt = f"""
    Generate a Twitter thread from the provided content.
    Match the source tone: {tone_analysis}
    Constraints:
    - Max 280 characters per tweet
    - Number tweets (1/N format)
    - Include hook in first tweet
    - Include CTA in last tweet
    - Suggest 2-3 relevant hashtags
    Return JSON: {{"thread": [...]}}
    """
    result = llm_prompt(prompt=markdown_content, system=system_prompt, ...)
    # Validate char counts
    for tweet in result["thread"]:
        if len(tweet["text"]) > 280:
            raise ValueError(f"Tweet {tweet['tweet_number']} exceeds 280 chars")
    return result

# assemble_output.py
def main():
    # PATTERN: json_read_write
    # Step 1: Merge all inputs into unified structure
    output = {
        "source_url": source_metadata["url"],
        "source_title": source_metadata["title"],
        "generated_at": datetime.utcnow().isoformat(),
        "tone_analysis": tone_analysis,
        "twitter": platform_content["twitter"],
        "linkedin": platform_content["linkedin"],
        "email": platform_content["email"],
        "instagram": platform_content["instagram"]
    }

    # Step 2: Generate filename
    slug = slugify(source_metadata["title"])
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_path = f"output/{timestamp}-{slug}.json"

    # Step 3: Write JSON with validation
    # PATTERN: Create directory if missing, write with indent
    pathlib.Path("output").mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return {"output_path": output_path, "total_chars": len(json.dumps(output)), "platform_count": 4}
```

### Integration Points

```yaml
SECRETS:
  - name: "FIRECRAWL_API_KEY"
    purpose: "Firecrawl API authentication for web scraping"
    required: true

  - name: "ANTHROPIC_API_KEY"
    purpose: "Claude API for tone analysis and content generation"
    required: true

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "FIRECRAWL_API_KEY=your_key_here  # Get from https://firecrawl.dev"
      - "ANTHROPIC_API_KEY=your_key_here  # Get from https://console.anthropic.com"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "firecrawl-py>=0.0.16  # Firecrawl Python SDK"
      - "anthropic>=0.18.0  # Claude API client"
      - "httpx>=0.27.0  # HTTP client for fallback scraping"
      - "beautifulsoup4>=4.12.0  # HTML parsing fallback"
      - "markdown>=3.5.0  # Markdown to HTML conversion for email"
      - "python-slugify>=8.0.0  # Generate clean filenames"

GITHUB_ACTIONS:
  - trigger: "workflow_dispatch"
    config: "Manual trigger with blog_url, author_handle, brand_hashtags inputs"
  - trigger: "schedule (optional)"
    config: "0 9 * * 1  # Weekly Monday 9 AM UTC"
```

---

## Validation Loop

### Level 1: Syntax & Structure

```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/scrape_blog_post.py').read())"
python -c "import ast; ast.parse(open('tools/analyze_tone.py').read())"
python -c "import ast; ast.parse(open('tools/generate_twitter.py').read())"
python -c "import ast; ast.parse(open('tools/generate_linkedin.py').read())"
python -c "import ast; ast.parse(open('tools/generate_email.py').read())"
python -c "import ast; ast.parse(open('tools/generate_instagram.py').read())"
python -c "import ast; ast.parse(open('tools/assemble_output.py').read())"

# Import check — verify no missing dependencies
python -c "import tools.scrape_blog_post"
python -c "import tools.analyze_tone"
python -c "import tools.generate_twitter"
python -c "import tools.generate_linkedin"
python -c "import tools.generate_email"
python -c "import tools.generate_instagram"
python -c "import tools.assemble_output"

# Structure check — verify main() exists in each tool
python -c "from tools.scrape_blog_post import main; assert callable(main)"
python -c "from tools.analyze_tone import main; assert callable(main)"
python -c "from tools.generate_twitter import main; assert callable(main)"
python -c "from tools.generate_linkedin import main; assert callable(main)"
python -c "from tools.generate_email import main; assert callable(main)"
python -c "from tools.generate_instagram import main; assert callable(main)"
python -c "from tools.assemble_output import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests

```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Test scraper with a known-good URL
python tools/scrape_blog_post.py --url "https://example.com/blog/test-post"
# Expected output: JSON with status: "success", markdown_content: non-empty string, title: non-empty

# Test tone analyzer with sample content
echo '{"markdown_content": "This is a test blog post about AI and automation. It has a casual tone."}' | \
python tools/analyze_tone.py
# Expected output: JSON with formality, technical_level, humor_level, confidence between 0-1

# Test Twitter generator with sample content and tone
echo '{"markdown_content": "Test content", "tone_analysis": {"formality": "casual"}}' | \
python tools/generate_twitter.py
# Expected output: JSON with thread array, each tweet <= 280 chars

# Test LinkedIn generator
echo '{"markdown_content": "Test content", "tone_analysis": {"formality": "professional"}}' | \
python tools/generate_linkedin.py
# Expected output: JSON with text, char_count, hashtags

# Test email generator
echo '{"markdown_content": "Test content", "tone_analysis": {"formality": "neutral"}, "source_url": "https://example.com"}' | \
python tools/generate_email.py
# Expected output: JSON with subject_line, section_html, section_text, word_count

# Test Instagram generator
echo '{"markdown_content": "Test content", "tone_analysis": {"formality": "casual"}}' | \
python tools/generate_instagram.py
# Expected output: JSON with caption <= 2200 chars, hashtags array (10-15 items)

# Test assembler with mock data
echo '{"source_metadata": {"url": "https://example.com", "title": "Test"}, "tone_analysis": {}, "platform_content": {"twitter": {}, "linkedin": {}, "email": {}, "instagram": {}}}' | \
python tools/assemble_output.py
# Expected output: JSON with output_path, confirms file was written to output/

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests

```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with a real blog post URL

# Step 1: Scrape
python tools/scrape_blog_post.py --url "https://example.com/blog/sample-post" > /tmp/scraped.json

# Verify output has required fields
python -c "
import json
data = json.load(open('/tmp/scraped.json'))
assert data['status'] == 'success', 'Scrape failed'
assert len(data['markdown_content']) > 100, 'Content too short'
print('✓ Scrape passed')
"

# Step 2: Analyze tone
python tools/analyze_tone.py < /tmp/scraped.json > /tmp/tone.json

# Verify tone analysis structure
python -c "
import json
data = json.load(open('/tmp/tone.json'))
assert 'formality' in data, 'Missing formality'
assert 'confidence' in data, 'Missing confidence'
assert 0 <= data['confidence'] <= 1, 'Invalid confidence value'
print('✓ Tone analysis passed')
"

# Step 3: Generate Twitter (parallel simulation — run sequentially for test)
python tools/generate_twitter.py --content "$(jq -r .markdown_content /tmp/scraped.json)" \
  --tone "$(cat /tmp/tone.json)" > /tmp/twitter.json

# Verify Twitter thread
python -c "
import json
data = json.load(open('/tmp/twitter.json'))
assert 'thread' in data, 'Missing thread'
assert len(data['thread']) > 0, 'Empty thread'
for tweet in data['thread']:
    assert len(tweet['text']) <= 280, f'Tweet exceeds 280 chars: {len(tweet[\"text\"])}'
print('✓ Twitter generation passed')
"

# Step 4: Generate all platforms (repeat for LinkedIn, email, Instagram)
# ... similar validation for each platform

# Step 5: Assemble output
python tools/assemble_output.py \
  --source /tmp/scraped.json \
  --tone /tmp/tone.json \
  --twitter /tmp/twitter.json \
  --linkedin /tmp/linkedin.json \
  --email /tmp/email.json \
  --instagram /tmp/instagram.json

# Verify final output file exists and has correct structure
python -c "
import json, glob, pathlib
output_files = glob.glob('output/*.json')
assert len(output_files) > 0, 'No output file generated'
latest = max(output_files, key=lambda f: pathlib.Path(f).stat().st_mtime)
data = json.load(open(latest))
assert 'twitter' in data, 'Missing twitter in output'
assert 'linkedin' in data, 'Missing linkedin in output'
assert 'email' in data, 'Missing email in output'
assert 'instagram' in data, 'Missing instagram in output'
assert 'tone_analysis' in data, 'Missing tone_analysis in output'
print(f'✓ Integration test passed. Output: {latest}')
"

# Verify workflow.md references match actual tool files
ls tools/*.py | while read tool; do
  grep -q "$(basename $tool)" workflow.md || echo "WARNING: $tool not referenced in workflow.md"
done

# Verify CLAUDE.md documents all tools
for tool in scrape_blog_post analyze_tone generate_twitter generate_linkedin generate_email generate_instagram assemble_output; do
  grep -q "$tool" CLAUDE.md || echo "WARNING: $tool not documented in CLAUDE.md"
done

# Verify all subagents are documented in CLAUDE.md
for agent in content-scraper-specialist tone-analyzer-specialist content-generator-specialist output-assembler-specialist; do
  grep -q "$agent" CLAUDE.md || echo "WARNING: subagent $agent not documented in CLAUDE.md"
done

# Verify .github/workflows/ YAML is valid
for workflow in .github/workflows/*.yml; do
  python -c "import yaml; yaml.safe_load(open('$workflow'))" || echo "ERROR: $workflow has invalid YAML"
done
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes and failure notifications
- [ ] .env.example lists all required environment variables (FIRECRAWL_API_KEY, ANTHROPIC_API_KEY)
- [ ] .gitignore excludes .env, __pycache__/, output/*.json
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files (.claude/agents/) have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies
- [ ] Character count validation is EXACT in all platform generators
- [ ] Twitter thread logic handles both single-tweet and multi-tweet cases
- [ ] Instagram hashtag formatting is validated (lowercase, alphanumeric + underscores)

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only output/ files
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not generate content that exceeds platform limits — validate before returning
- Do not use Agent Teams when tone analysis hasn't completed — platforms depend on tone data
- Do not ignore character count precision — off-by-one errors break Twitter posts
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not assume blog post scraping will always succeed — graceful degradation is critical
- Do not generate Instagram captions without line breaks — readability requires formatting

---

## Confidence Score: 9/10

**Score rationale:**
- **Web scraping**: High confidence — Firecrawl MCP + HTTP fallback is proven pattern. Blog post extraction is straightforward with fallback to BeautifulSoup.
- **Tone analysis**: High confidence — Claude excels at stylistic analysis. Structured JSON output with schema validation ensures consistency.
- **Platform generation**: High confidence — Character limit validation and platform-specific formatting are well-defined. Claude can match tone accurately.
- **Agent Teams parallelization**: High confidence — 4 independent generation tasks with clear merge logic. Parallel speedup is significant (40s → 15s).
- **Tool patterns**: High confidence — All tools map to proven catalog patterns (firecrawl_scrape, llm_prompt, structured_extract, json_read_write).
- **Validation gates**: High confidence — All three levels have clear pass/fail criteria. Integration test simulates full pipeline.
- **Subagent architecture**: High confidence — Four specialist subagents with clear responsibilities and minimal tool access. Follows WAT best practices.
- **Uncertainty: Hashtag quality**: Medium confidence — Auto-generated hashtags may not always match trending tags or brand voice. Consider adding a hashtag validation/suggestion API call.
- **Uncertainty: Email HTML rendering**: Medium confidence — Email clients render HTML inconsistently. Need thorough testing across Gmail, Outlook, Apple Mail.

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — all requirements are clear and actionable. System can be built immediately.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/content-repurposer.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
