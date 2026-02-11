# Content Repurposer

Multi-channel content repurposing system that transforms blog posts into platform-optimized social media content.

## What It Does

Takes a blog post URL and generates:
- **Twitter thread** (280 chars/tweet, numbered, with hashtags)
- **LinkedIn post** (1200-1400 chars, professional tone, hashtags)
- **Email newsletter section** (500-800 words, HTML + plain text)
- **Instagram caption** (1500-2000 chars, emojis, 10-15 hashtags)

Each output matches the source content's tone (formal/casual, technical level, humor) automatically.

## Features

- ✅ Automatic tone analysis and matching
- ✅ Platform-specific character limits enforced
- ✅ Hashtag and mention suggestions
- ✅ Graceful fallback (HTTP if Firecrawl fails)
- ✅ Parallel generation with Agent Teams (2x faster)
- ✅ Single JSON output with all platforms
- ✅ Three execution paths: CLI, GitHub Actions, Agent HQ

---

## Setup

### Prerequisites

- Python 3.10+
- Anthropic API key (required)
- Firecrawl API key (recommended)

### Installation

1. **Clone this system to your repository**

```bash
# If standalone
git clone <this-repo>
cd content-repurposer

# If part of a monorepo
# Files are already in systems/content-repurposer/
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your API keys
```

Get API keys:
- **Anthropic**: https://console.anthropic.com (required)
- **Firecrawl**: https://firecrawl.dev (optional but recommended)

---

## Usage

### Path 1: Local CLI (Development)

Run directly from command line with Claude Code:

```bash
# Basic usage
claude workflow.md --var blog_url="https://example.com/blog/post"

# With optional parameters
claude workflow.md \
  --var blog_url="https://example.com/blog/post" \
  --var author_handle="johndoe" \
  --var brand_hashtags="YourBrand,Marketing"
```

Output is written to `output/{timestamp}-{slug}.json`.

### Path 2: GitHub Actions (Production)

1. **Push this system to a GitHub repository**

2. **Configure GitHub Secrets**

Go to Settings > Secrets and variables > Actions, add:
- `ANTHROPIC_API_KEY` (required)
- `FIRECRAWL_API_KEY` (optional)

3. **Trigger workflow manually**

Via GitHub UI:
- Go to Actions tab
- Select "Content Repurposer" workflow
- Click "Run workflow"
- Enter blog URL and optional parameters
- Click "Run workflow"

Via GitHub CLI:
```bash
gh workflow run content-repurposer.yml \
  -f blog_url="https://example.com/blog/post" \
  -f author_handle="johndoe" \
  -f brand_hashtags="YourBrand,Marketing"
```

Via API:
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/content-repurposer.yml/dispatches \
  -d '{"ref":"main","inputs":{"blog_url":"https://example.com/blog/post"}}'
```

4. **View results**

- Output is committed to `output/{timestamp}-{slug}.json`
- GitHub Actions summary shows stats and link to output file

### Path 3: Agent HQ (Issue-Driven)

1. **Open a GitHub Issue** with label `content-repurpose`

2. **Issue body format**:

```
Blog URL: https://example.com/blog/awesome-post
Author Handle: johndoe
Brand Hashtags: YourBrand, Marketing
```

3. **Agent HQ will**:
- Parse the issue body
- Execute the workflow via GitHub Actions
- Open a draft PR with the generated output
- Comment on the issue with PR link and summary

4. **Review and merge** the PR to add the output to your repo

---

## Output Format

### Example Output File: `output/20260211-133200-awesome-post.json`

```json
{
  "source_url": "https://example.com/blog/awesome-post",
  "source_title": "How to Master Content Marketing",
  "source_author": "Jane Doe",
  "source_publish_date": "2026-02-10",
  "generated_at": "2026-02-11T13:32:00Z",
  
  "tone_analysis": {
    "formality": "semi-formal",
    "technical_level": "intermediate",
    "humor_level": "low",
    "primary_emotion": "informative",
    "confidence": 0.85,
    "rationale": "Professional yet accessible tone..."
  },
  
  "twitter": {
    "thread": [
      {"tweet_number": 1, "text": "🧵 Ever wonder why...", "char_count": 125},
      {"tweet_number": 2, "text": "Here's the key insight...", "char_count": 267}
    ],
    "total_tweets": 5,
    "hashtags": ["#ContentMarketing", "#MarketingTips"],
    "suggested_mentions": ["@IndustryLeader"]
  },
  
  "linkedin": {
    "text": "Full LinkedIn post...",
    "char_count": 1285,
    "hashtags": ["#Marketing", "#ContentStrategy"],
    "hook": "Ever wonder why most content fails?",
    "cta": "What's your take? Share in comments."
  },
  
  "email": {
    "subject_line": "The one thing about content marketing",
    "section_html": "<h2>Key Insights</h2><p>...</p>",
    "section_text": "KEY INSIGHTS\n\n...",
    "word_count": 672,
    "cta": "Read the full post: https://example.com/blog/post"
  },
  
  "instagram": {
    "caption": "Ever wondered...?\n\n💡 Here's what changed...",
    "char_count": 1847,
    "hashtags": ["#marketing", "#contentcreator", "#tips"],
    "line_break_count": 6,
    "emoji_count": 4
  }
}
```

---

## Architecture

### Workflow Steps

1. **Scrape Blog Post** → `content-scraper-specialist` → `scrape_blog_post.py`
2. **Analyze Tone** → `tone-analyzer-specialist` → `analyze_tone.py`
3. **Generate Platforms (Parallel)** → `content-generator-specialist` → 4 platform generators
4. **Assemble Output** → `output-assembler-specialist` → `assemble_output.py`

### Subagents

- **content-scraper-specialist**: Fetches and extracts blog content
- **tone-analyzer-specialist**: Analyzes writing style
- **content-generator-specialist**: Coordinates platform generation (can use Agent Teams)
- **output-assembler-specialist**: Merges into final JSON

### Agent Teams Parallelization

Platform generation runs in parallel (4 teammates) when enabled:
- Sequential: 40-55 seconds
- Parallel: 12-18 seconds
- **2x speedup** with identical results

---

## Performance

### Execution Time

- **With Agent Teams**: ~25-37 seconds total
- **Without Agent Teams**: ~52-74 seconds total
- Bottleneck: Claude API calls (inevitable)

### Cost Per Run

Assuming Claude Sonnet 4 pricing ($3/MTok input, $15/MTok output):

- Scraping: $0.01-0.02 (Firecrawl)
- Tone analysis: ~$0.01
- Platform generation (4x): ~$0.08
- **Total: ~$0.10-0.11 per blog post**

At 100 runs/month: ~$11/month API costs + negligible GitHub Actions minutes.

---

## Troubleshooting

### Scraping Fails

**Symptom**: `status: "error"` from scraper

**Causes**:
- URL is behind paywall or login wall
- Site blocks bots (User-Agent filtering)
- Page has no article content (homepage, search results)

**Solutions**:
- Try a different URL
- Check if manual browser access works
- If consistently failing, check Firecrawl API key

### Tone Analysis Returns Default Profile

**Symptom**: `confidence: 0.5` or lower

**Causes**:
- Content too short (< 100 chars)
- LLM API error or timeout

**Impact**: Platform content still generates, but tone matching quality may be reduced

### Platform Generation Fails

**Symptom**: Platform has `status: "generation_failed"`

**Causes**:
- LLM API rate limit
- LLM API timeout
- Character count validation failed

**Solutions**:
- Retry the workflow (tools have 1 automatic retry)
- Check ANTHROPIC_API_KEY is valid
- Check API rate limits on Anthropic dashboard

### Character Count Exceeds Limit

**Symptom**: Warning in logs, content truncated

**Cause**: LLM generated content over platform limit

**Behavior**: Tool automatically truncates with "..." and flags warning

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for tone analysis and generation |
| `FIRECRAWL_API_KEY` | No | Firecrawl API key (improves scraping reliability) |

### GitHub Secrets

Set these in repo Settings > Secrets:
- `ANTHROPIC_API_KEY`
- `FIRECRAWL_API_KEY` (optional)

### Customization

Edit platform generation prompts in:
- `tools/generate_twitter.py`
- `tools/generate_linkedin.py`
- `tools/generate_email.py`
- `tools/generate_instagram.py`

Adjust character targets, hashtag counts, tone instructions, etc.

---

## Validation

### Level 1: Syntax Check

```bash
# Verify all tools are valid Python
python -c "import ast; ast.parse(open('tools/scrape_blog_post.py').read())"
python -c "import ast; ast.parse(open('tools/analyze_tone.py').read())"
python -c "import ast; ast.parse(open('tools/generate_twitter.py').read())"
python -c "import ast; ast.parse(open('tools/generate_linkedin.py').read())"
python -c "import ast; ast.parse(open('tools/generate_email.py').read())"
python -c "import ast; ast.parse(open('tools/generate_instagram.py').read())"
python -c "import ast; ast.parse(open('tools/assemble_output.py').read())"
```

### Level 2: Unit Tests

```bash
# Test each tool with sample data
python tools/scrape_blog_post.py --url "https://example.com/blog/test"
# ... (see PRP for full test suite)
```

### Level 3: Integration Test

```bash
# Run full pipeline with a real blog post
claude workflow.md --var blog_url="https://example.com/blog/sample"
# Verify output file exists and has all 4 platforms
```

---

## Contributing

### Adding a New Platform

1. Create `tools/generate_PLATFORM.py` following existing tool patterns
2. Add platform to `content-generator-specialist.md` subagent
3. Update `assemble_output.py` to include new platform
4. Add validation in workflow.md
5. Update this README

### Improving Tone Matching

Edit `tools/analyze_tone.py`:
- Add new dimensions to analysis schema
- Adjust confidence thresholds
- Refine LLM prompts

---

## License

[Your license here]

## Support

Issues: [GitHub Issues](https://github.com/yourusername/content-repurposer/issues)
Docs: [Full documentation](./docs/)
