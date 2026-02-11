# Content Repurposer

> **WAT System**: Multi-channel content repurposing that transforms blog posts into platform-optimized social media content.

Automatically scrapes blog posts, analyzes tone, and generates optimized content for Twitter, LinkedIn, email newsletters, and Instagram — all matching the source content's writing style.

---

## What It Does

1. **Scrapes** blog post content from any URL (Firecrawl API + HTTP fallback)
2. **Analyzes** writing tone and style using Claude (formality, technical level, humor, emotion)
3. **Generates** platform-specific content matching the source tone:
   - **Twitter**: Threaded tweets with hooks, CTAs, hashtags (280 chars/tweet)
   - **LinkedIn**: Professional post with hook and CTA (target 1300 chars)
   - **Email**: Newsletter section with HTML and plain text (500-800 words)
   - **Instagram**: Caption with emojis and hashtags (1500-2000 chars)
4. **Outputs** single JSON file with all platforms + metadata

---

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key (Claude)
- Firecrawl API key (optional — HTTP fallback available)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Secrets

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

### 3. Run via CLI

```bash
export ANTHROPIC_API_KEY=your_key
export FIRECRAWL_API_KEY=your_key  # optional
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1  # optional, enables parallel mode

# Run with Claude Code
claude workflow.md --input '{
  "blog_url": "https://example.com/blog/my-post",
  "author_handle": "johndoe",
  "brand_hashtags": "YourBrand,ContentMarketing"
}'
```

### 4. Run via GitHub Actions

1. Push this system to your GitHub repository
2. Configure secrets in Settings > Secrets and variables > Actions:
   - `ANTHROPIC_API_KEY` (required)
   - `FIRECRAWL_API_KEY` (optional)
3. Go to Actions tab > "Content Repurposer — WAT System" > "Run workflow"
4. Enter blog URL and optional parameters
5. Check output in `output/` directory after run completes

### 5. Run via GitHub Agent HQ

1. Create an issue: "Repurpose Blog Post: https://example.com/blog/my-post"
2. In the body:
   ```
   Author Handle: johndoe
   Brand Hashtags: YourBrand, ContentMarketing
   ```
3. Assign to @claude
4. Review the draft PR with output file
5. Merge or request changes

---

## Output Format

Output files are saved to `output/{timestamp}-{slug}.json`:

```json
{
  "source_url": "https://example.com/blog/my-post",
  "source_title": "My Awesome Post",
  "generated_at": "2026-02-11T13:20:00Z",
  "tone_analysis": {
    "formality": "casual",
    "technical_level": "intermediate",
    "humor_level": "low",
    "primary_emotion": "informative",
    "confidence": 0.85
  },
  "twitter": {
    "thread": [
      {"tweet_number": 1, "text": "Hook...", "char_count": 125},
      {"tweet_number": 2, "text": "Point 1...", "char_count": 267}
    ],
    "total_tweets": 5,
    "hashtags": ["#ContentMarketing", "#SEO"]
  },
  "linkedin": {
    "text": "Full post...",
    "char_count": 1285,
    "hashtags": ["#Marketing"],
    "hook": "Attention-grabbing opening",
    "cta": "What's your take?"
  },
  "email": {
    "subject_line": "Newsletter subject",
    "section_html": "<h2>Title</h2><p>Content...</p>",
    "section_text": "Plain text version...",
    "word_count": 672
  },
  "instagram": {
    "caption": "Caption with emojis and line breaks...",
    "char_count": 1847,
    "hashtags": ["#contentmarketing", "#socialmedia"],
    "emoji_count": 3
  }
}
```

---

## Features

### Tone Matching
The system analyzes the source blog post's writing style and generates platform content that matches it. Formal blog → formal LinkedIn. Casual blog → casual Instagram.

### Agent Teams (Parallel Generation)
With `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, platform generation runs in parallel (4 concurrent LLM calls):
- **Sequential**: ~52-74 seconds
- **Parallel**: ~25-37 seconds (2x faster)
- Same token cost, identical results

### Graceful Degradation
- Firecrawl fails? Falls back to HTTP + BeautifulSoup
- Single platform fails? Delivers other 3 successfully
- Tone analysis fails? Uses default neutral profile

### Platform-Specific Optimization
- **Twitter**: Character count validation, thread numbering, hook/CTA placement
- **LinkedIn**: Visibility-optimized length (1300 chars), professional hashtags
- **Email**: HTML + plain text, subject line, structured sections
- **Instagram**: Emoji count, line breaks, lowercase hashtag validation

---

## Architecture

### Workflow Pattern

**Scrape > Process > Output + Content Transformation with Tone Matching + Fan-Out > Process > Merge**

1. Scrape blog post (Firecrawl + HTTP fallback)
2. Analyze tone (Claude structured extraction)
3. Generate platforms (4 parallel tasks with Agent Teams or sequential)
4. Assemble JSON output
5. Commit to repo

### Subagents

- **content-scraper-specialist**: Web scraping with fallback
- **tone-analyzer-specialist**: Tone analysis with Claude
- **content-generator-specialist**: Multi-platform generation coordinator
- **output-assembler-specialist**: JSON assembly and file writing

### Tools

All tools are standalone Python scripts in `tools/`:
- `scrape_blog_post.py` — Web scraping
- `analyze_tone.py` — Tone analysis
- `generate_twitter.py` — Twitter thread generator
- `generate_linkedin.py` — LinkedIn post generator
- `generate_email.py` — Email newsletter generator
- `generate_instagram.py` — Instagram caption generator
- `assemble_output.py` — Output assembly

---

## Configuration

### Required Secrets

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude API for LLM calls | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl API for scraping | No (HTTP fallback) |

### Optional Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Enable parallel generation | `0` (disabled) |

---

## Cost & Performance

**Per Run**:
- Firecrawl: $0.01-0.02 (1 scrape)
- Claude: ~$0.09 (tone + 4 platforms)
- **Total**: ~$0.10-0.11 per blog post

**Execution Time**:
- Sequential: ~52-74 seconds
- Parallel (Agent Teams): ~25-37 seconds

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Scraping fails (404) | Check URL is correct and publicly accessible |
| Scraping fails (paywall) | Content is behind authentication — cannot scrape |
| Low tone confidence (< 0.7) | Content is too short or ambiguous — uses default profile |
| Platform generation fails | Check Anthropic API key and rate limits |
| Character count exceeded | Tool truncates automatically with "..." |
| Missing dependencies | Run `pip install -r requirements.txt` |

---

## Documentation

- **CLAUDE.md**: Comprehensive operating instructions for Claude
- **workflow.md**: Step-by-step workflow process
- `.claude/agents/*.md`: Subagent specifications

---

## License

MIT

---

## Support

For issues or questions, open a GitHub issue.
