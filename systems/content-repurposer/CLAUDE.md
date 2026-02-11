# Content Repurposer — Operating Instructions for Claude Code

You are executing the **Content Repurposer** system, a multi-channel content transformation pipeline.

## Your Mission

Transform a blog post URL into platform-optimized social media content: Twitter thread, LinkedIn post, email newsletter section, and Instagram caption — all matching the source content's tone automatically.

---

## Execution Path

You are running workflow.md. The system uses **specialist subagents** for delegation. Follow the workflow steps precisely.

---

## Required Inputs

You must receive these variables (via `--var` flags or environment):

- **blog_url** (required): Full URL of the blog post to repurpose
- **author_handle** (optional): Author's social media handle (without @)
- **brand_hashtags** (optional): Comma-separated brand hashtags

---

## Workflow Overview

### Step 1: Scrape Blog Post

**Delegate to**: `content-scraper-specialist` subagent

The subagent will:
1. Validate the blog_url
2. Execute `tools/scrape_blog_post.py`
3. Return scraped content with metadata

**Critical**: If scraping fails (status: "error"), HALT immediately. You cannot proceed without content.

### Step 2: Analyze Tone

**Delegate to**: `tone-analyzer-specialist` subagent

The subagent will:
1. Receive markdown_content from Step 1
2. Execute `tools/analyze_tone.py`
3. Return structured tone profile (formality, technical_level, humor_level, etc.)

**Note**: If analysis fails, a default tone profile is returned. Log a warning but continue — platform generation will still work.

### Step 3: Generate Platform Content

**Delegate to**: `content-generator-specialist` subagent

The subagent coordinates generation of all 4 platforms:
- Twitter thread (via `generate_twitter.py`)
- LinkedIn post (via `generate_linkedin.py`)
- Email newsletter (via `generate_email.py`)
- Instagram caption (via `generate_instagram.py`)

**Agent Teams Option**: If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is enabled, the generator can spawn 4 parallel teammates for faster execution (~15s vs ~50s sequential).

**Partial Success**: If 1-2 platforms fail, continue with available content. Do NOT halt for single platform failure.

### Step 4: Assemble Output

**Delegate to**: `output-assembler-specialist` subagent

The subagent will:
1. Merge all content into unified JSON structure
2. Generate filename: `output/{timestamp}-{slug}.json`
3. Write file
4. Return output path and summary stats

---

## Subagent Delegation

You have **4 specialist subagents**:

| Subagent | When to Delegate | What They Do |
|----------|------------------|--------------|
| `content-scraper-specialist` | Need to fetch blog content | Execute scraper tool, validate output, return content + metadata |
| `tone-analyzer-specialist` | Need to analyze writing style | Execute tone analyzer, return structured tone profile |
| `content-generator-specialist` | Need to generate all platform content | Coordinate 4 platform generators (sequential or parallel), validate outputs |
| `output-assembler-specialist` | Need to merge into final JSON | Execute assembler, write output file, return summary |

**Always delegate to the appropriate subagent**. Do not execute tools directly from the main agent context.

---

## Tool Access

**Main agent**: You have Read, Write, Edit, Bash, Grep, Glob

**Subagents**: Each has minimal tool access (see .claude/agents/*.md for details)

**Secrets**: Available as environment variables:
- `ANTHROPIC_API_KEY` (required)
- `FIRECRAWL_API_KEY` (optional but recommended)

Tools automatically read these from `os.environ`.

---

## Agent Teams Configuration

If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is set:

**Step 3 (Platform Generation) uses Agent Teams**:
- Team lead: `content-generator-specialist`
- Teammates: 4 parallel platform generators
- Speedup: ~2x faster (40-50s → 15-18s)
- Cost: Same token usage, just parallel execution

**How it works**:
1. Generator specialist creates shared task list with 4 platform tasks
2. Spawns 4 teammates in parallel
3. Each teammate generates one platform (Twitter, LinkedIn, email, Instagram)
4. Team lead collects and merges results
5. Validates character counts and required fields

**Fallback**: If Agent Teams fails or is disabled, platforms are generated sequentially. Results are identical.

---

## Secret Requirements

### Required

- **ANTHROPIC_API_KEY**: Claude API key for tone analysis and generation
  - Get from: https://console.anthropic.com
  - Used by: tone analyzer, all 4 platform generators

### Optional

- **FIRECRAWL_API_KEY**: Firecrawl API key for reliable web scraping
  - Get from: https://firecrawl.dev
  - Used by: scraper tool (primary method)
  - Fallback: Direct HTTP + BeautifulSoup if not set

---

## Expected Execution Flow

```
[Main Agent] Start workflow.md
    ↓
    Delegate to content-scraper-specialist
        → Execute scrape_blog_post.py
        → Validate content
        → Return scraped data
    ↓
[Main Agent] Receive scraped content
    ↓
    Delegate to tone-analyzer-specialist
        → Execute analyze_tone.py
        → Return tone profile
    ↓
[Main Agent] Receive tone analysis
    ↓
    Delegate to content-generator-specialist
        → [If Agent Teams enabled] Spawn 4 teammates in parallel
        → [If not enabled] Generate platforms sequentially
        → Validate outputs
        → Return all platform content
    ↓
[Main Agent] Receive platform content
    ↓
    Delegate to output-assembler-specialist
        → Execute assemble_output.py
        → Write output/{timestamp}-{slug}.json
        → Return output path and stats
    ↓
[Main Agent] Workflow complete
    → Report output file path
    → Report summary stats
```

---

## Error Handling

### Scraping Failure (Step 1)

**Symptoms**: status: "error" from scraper

**Action**: HALT workflow immediately. Log error clearly:
```
❌ Failed to fetch content from {url}: {error}
Cannot proceed without content.
```

### Tone Analysis Failure (Step 2)

**Symptoms**: Default tone profile returned (confidence: 0.5)

**Action**: Log warning but continue:
```
⚠️ Tone analysis returned default profile (confidence: 0.5)
Proceeding with generation using neutral tone.
```

### Platform Generation Failure (Step 3)

**Symptoms**: One or more platforms have status: "generation_failed"

**Action**: Continue with successful platforms. Log warning:
```
⚠️ Twitter generation failed: {error}
✅ LinkedIn, Email, Instagram generated successfully (3/4)
```

**Acceptable**: 2-4 platforms generated = workflow succeeds

**Unacceptable**: 0-1 platforms generated = workflow fails

### Assembly Failure (Step 4)

**Symptoms**: File write fails

**Action**: Print JSON to stdout, log error, HALT:
```
❌ Failed to write output file: {error}
Full JSON output (save manually):
{...full json...}
```

---

## Output Validation

Before marking workflow as complete, verify:

✅ Output file exists at `output/{timestamp}-{slug}.json`
✅ File contains all required top-level keys: source_url, source_title, generated_at, tone_analysis, twitter, linkedin, email, instagram
✅ At least 2 platforms have valid content (not "generation_failed")
✅ Character counts are within limits:
   - Twitter: each tweet ≤ 280 chars
   - LinkedIn: ≤ 3000 chars
   - Instagram: ≤ 2200 chars

---

## Reporting

### Success Report

```
✅ Content Repurposer Complete

Source: {blog_url}
Title: {source_title}

Generated:
- Twitter: {N} tweets
- LinkedIn: {chars} characters
- Email: {words} words
- Instagram: {chars} characters

Output: output/{timestamp}-{slug}.json
Total characters: {total_chars}
Execution time: {duration}
```

### Failure Report

```
❌ Content Repurposer Failed

Source: {blog_url}
Error: {error_details}

Step failed: {step_name}
Action: {what to do next}
```

---

## Execution Paths

### Path 1: GitHub Actions (Primary)

Triggered via `workflow_dispatch` in `.github/workflows/content-repurposer.yml`:
- Python environment set up automatically
- Dependencies installed from requirements.txt
- Secrets injected as environment variables
- Output committed back to repo
- GitHub Actions summary generated

### Path 2: Local CLI

Run directly:
```bash
claude workflow.md --var blog_url="https://example.com/post"
```

Requirements:
- `.env` file with API keys
- Python dependencies installed
- Output written to local `output/` directory

### Path 3: Agent HQ (Future)

Issue-driven execution:
- Open issue with label `content-repurpose`
- Issue body contains blog_url and optional parameters
- Agent HQ parses issue and executes workflow
- Opens draft PR with results

---

## Performance Notes

### Execution Time

- **With Agent Teams**: ~25-37 seconds
  - Scraping: 3-5s
  - Tone: 8-12s
  - Generation (parallel): 12-18s
  - Assembly: 1-2s

- **Without Agent Teams**: ~52-74 seconds
  - Scraping: 3-5s
  - Tone: 8-12s
  - Generation (sequential): 40-55s
  - Assembly: 1-2s

### Token Usage

Per run (approximate):
- Tone analysis: 500 input + 200 output tokens
- Twitter: 1000 input + 500 output
- LinkedIn: 1000 input + 300 output
- Email: 1000 input + 600 output
- Instagram: 1000 input + 400 output
- **Total**: ~4500 input + 2000 output tokens

Cost (Claude Sonnet 4): ~$0.04 per run (LLM only)
+ Firecrawl: ~$0.01-0.02 per scrape

### Rate Limits

Claude API: 50 requests/minute (standard tier)
Firecrawl API: 500 requests/hour (standard plan)

Both are well within limits for this workflow (5-6 Claude calls, 1 Firecrawl call per run).

---

## Troubleshooting

### Issue: Scraping returns error

**Check**:
- Is the URL publicly accessible?
- Is it behind a paywall or login?
- Is FIRECRAWL_API_KEY set correctly?

**Solution**:
- Try a different URL
- Verify API key is valid
- Check Firecrawl dashboard for quota

### Issue: Character counts exceed limits

**Check**: Tool logs for truncation warnings

**Behavior**: Tools automatically truncate with "..." and log warning. This is expected occasionally.

### Issue: Agent Teams not parallelizing

**Check**: Is `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` set to `true`?

**Fallback**: Sequential execution is automatic fallback. Results are identical, just slower.

---

## Anti-Patterns to Avoid

❌ Do NOT execute tools directly from main agent — always delegate to subagents
❌ Do NOT proceed if scraping fails — content is required
❌ Do NOT halt workflow if 1-2 platforms fail — partial success is acceptable
❌ Do NOT modify tool files during execution — they are validated and tested
❌ Do NOT skip character count validation — platform limits are strict
❌ Do NOT retry infinitely — tools have built-in retry logic (1 retry each)
❌ Do NOT commit .env files — secrets stay in environment variables only

---

## Success Criteria

✅ You successfully complete the workflow if:
1. Blog content is scraped (status: "success")
2. Tone analysis completes (even if default profile)
3. At least 2 platforms generate content successfully
4. Output file is written to `output/`
5. Character counts are within platform limits

🎯 **Goal**: Produce a single JSON file with all 4 platform variants, matching the source tone, ready for manual publishing.
