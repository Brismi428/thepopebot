# Content Repurposer

Multi-channel content repurposing system that transforms blog posts into platform-optimized social media content. Automatically extracts content, analyzes tone, and generates versions for Twitter, LinkedIn, email newsletters, and Instagram.

## System Overview

- **Type**: WAT System (Workflow, Agents, Tools)
- **Purpose**: Automate content repurposing for multi-channel social media distribution
- **Pattern**: Scrape > Process > Output + Content Transformation with Tone Matching + Fan-Out > Process > Merge (Agent Teams)

## Execution

This system can be run three ways:

1. **Claude Code CLI**: Run `workflow.md` directly in the terminal
2. **GitHub Actions**: Trigger via Actions UI, API, or cron schedule
3. **GitHub Agent HQ**: Assign an issue to @claude with task input in the body

## Inputs

- **blog_url** (string, required): Full URL of the blog post to repurpose. Must be publicly accessible.
- **author_handle** (string, optional): Author's social media handle to include in mentions (without @)
- **brand_hashtags** (string, optional): Comma-separated brand-specific hashtags to include in every output

## Outputs

- **repurposed_content.json**: Single JSON file in `output/{timestamp}-{slug}.json` containing:
  - Source metadata (URL, title, author, publish date, generated timestamp)
  - Tone analysis (formality, technical level, humor, primary emotion, confidence score)
  - Platform-optimized content for Twitter, LinkedIn, email newsletter, and Instagram
  - Character counts, hashtag suggestions, formatting metadata for each platform

## Workflow

Follow `workflow.md` for the step-by-step process. Key phases:

1. **Scrape Blog Post** — Fetch content from URL using Firecrawl with HTTP fallback
2. **Analyze Tone** — Extract tone profile (formality, technical level, humor, emotion) using Claude
3. **Generate Platform Content (Parallel)** — Generate Twitter, LinkedIn, email, Instagram content concurrently with tone matching
4. **Assemble Output** — Merge all content into unified JSON file
5. **Commit Results** — Write output to repo and commit

## Tools

| Tool | Purpose |
|------|---------|
| `tools/scrape_blog_post.py` | Fetch and extract clean content from blog post URL (Firecrawl + HTTP fallback) |
| `tools/analyze_tone.py` | Analyze writing style and tone using Claude with structured extraction |
| `tools/generate_twitter.py` | Generate Twitter thread matching source tone (280 chars/tweet) |
| `tools/generate_linkedin.py` | Generate LinkedIn post with professional formatting (target 1300 chars) |
| `tools/generate_email.py` | Generate email newsletter section with HTML and plain text (500-800 words) |
| `tools/generate_instagram.py` | Generate Instagram caption with hashtags and emojis (target 1500-2000 chars) |
| `tools/assemble_output.py` | Merge all content into final JSON file and write to output/ |

## Subagents

This system uses specialist subagents defined in `.claude/agents/`. Subagents are the DEFAULT delegation mechanism — when the workflow reaches a phase, delegate to the appropriate subagent.

### Available Subagents

| Subagent | Description | Tools | When to Use |
|----------|-------------|-------|-------------|
| `content-scraper-specialist` | Handles web scraping with Firecrawl and HTTP fallback | Bash | When you need to fetch and extract clean content from a blog post URL |
| `tone-analyzer-specialist` | Analyzes source content tone and style with Claude | Bash | When you need to analyze the tone, style, and writing characteristics of content |
| `content-generator-specialist` | Coordinates multi-platform content generation (parallel or sequential) | Bash | When you need to generate platform-optimized content variants from source material |
| `output-assembler-specialist` | Merges all content into final JSON file | Write, Bash | When you need to merge all generated content into the final JSON output file |

### How to Delegate

Subagents are invoked automatically based on their `description` field or explicitly:
```
Use the content-scraper-specialist subagent to fetch the blog post content
Use the tone-analyzer-specialist subagent to analyze the tone
Use the content-generator-specialist subagent to generate all platform variants
Use the output-assembler-specialist subagent to assemble the final output
```

### Subagent Chaining

For this workflow, chain subagents sequentially — each subagent's output becomes the next subagent's input:

1. **content-scraper-specialist** produces `{markdown_content, title, author, ...}` → feeds into
2. **tone-analyzer-specialist** produces `{formality, technical_level, ...}` → feeds into
3. **content-generator-specialist** produces `{twitter: {...}, linkedin: {...}, ...}` → feeds into
4. **output-assembler-specialist** produces `{output_path, total_chars, platform_count}` → final result

The main agent coordinates this chain, reading outputs and delegating to the next subagent.

### Delegation Hierarchy

- **Subagents are the default** for all task delegation. Use them for every workflow phase.
- **Agent Teams is ONLY for parallelization** — when 3+ independent subagent tasks can run concurrently.
- This system **uses Agent Teams** for platform content generation (4 independent tasks). See the Agent Teams section below for details.

## MCP Dependencies

This system uses the following MCPs. Alternatives are listed for flexibility.

| Capability | Primary MCP | Alternative | Fallback |
|-----------|-------------|-------------|----------|
| Web scraping | Firecrawl MCP | Puppeteer MCP / Playwright MCP | HTTP + BeautifulSoup (Python requests) |
| LLM generation | Anthropic MCP | OpenAI MCP | Direct Anthropic API via Python SDK |

**Important**: No MCP is hardcoded. If a listed MCP is unavailable, the system falls back to the alternative or direct API calls. Configure your preferred MCPs in your Claude Code settings.

## Required Secrets

These must be set as GitHub Secrets (for Actions) or environment variables (for CLI):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude API for tone analysis and content generation | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl API for web scraping (optional — HTTP fallback available) | No |

## Agent Teams

This system supports **native Claude Code Agent Teams** for parallel execution. When enabled, a team lead agent coordinates teammate agents that work concurrently on independent tasks. **Agent Teams is a parallelization optimization — subagents remain the default delegation mechanism.**

### How It Works

- **Team Lead**: The `content-generator-specialist` subagent running platform generation. It creates a shared task list, spawns 4 teammates, monitors progress, and merges results.
- **Teammates**: Each handles one platform's content generation. They work in isolation, update their task status, and write output for the team lead to collect.
- **Shared Task List**: Coordination happens through `TaskCreate`, `TaskUpdate`, `TaskList`, and `TaskGet`. Tasks flow: `pending` → `in_progress` → `completed`.

### Parallel Tasks in This System

| Teammate | Task | What It Does |
|----------|------|--------------|
| twitter-generator | Generate Twitter thread | Calls `generate_twitter.py` to produce threaded tweets with numbering, hashtags, and mentions |
| linkedin-generator | Generate LinkedIn post | Calls `generate_linkedin.py` to produce professional post with hook, body, CTA, and hashtags |
| email-generator | Generate email newsletter section | Calls `generate_email.py` to produce subject line, HTML body, plain text, and CTA |
| instagram-generator | Generate Instagram caption | Calls `generate_instagram.py` to produce caption with emojis, line breaks, and hashtags |

### Enabling Agent Teams

Set the environment variable before running:
```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```
- **Locally**: Add to your `.env` file
- **GitHub Actions**: Already set in the workflow YAML
- **To disable**: Remove the variable or set to `0`

### Sequential Fallback

Without Agent Teams enabled, all 4 platforms are generated sequentially by the `content-generator-specialist` calling each tool one-by-one. **Results are identical** — the only difference is execution time. This system is designed to work correctly in both modes.

### Token Cost

- Agent Teams spawns 4 teammate agents for the platform generation phase
- Token usage scales ~4x for that section (each teammate has its own context)
- Sequential execution uses fewer tokens but takes longer
- **Recommendation**: Use Agent Teams in production when speed matters (~$0.09 per run either way). Use sequential for development/debugging.

### Performance Comparison

- **Sequential**: ~52-74 seconds (4 LLM calls in series)
- **Parallel (Agent Teams)**: ~25-37 seconds (4 LLM calls concurrent)
- **Speedup**: ~2x faster with identical results and same API cost

## Agent HQ Usage

To run via GitHub Agent HQ:

1. Create an issue with the title: `Repurpose Blog Post: <URL>`
2. In the issue body, provide:
   ```
   URL: https://example.com/blog/my-post
   Author Handle: johndoe (optional)
   Brand Hashtags: YourBrand, ContentMarketing (optional)
   ```
3. Assign the issue to @claude
4. The agent will process the request and open a draft PR with the output JSON file
5. Review the PR and leave comments with @claude for changes

## CRITICAL Git Rules

These rules apply to ALL agents operating in this repo. Non-negotiable.

### File Tracking
- Agents MUST track which files they created, modified, or deleted during the current session
- ONLY commit files the agent changed in the current session
- ALWAYS use `git add <specific-file-paths>` — NEVER `git add -A` or `git add .`
- Before committing, run `git status` and verify only the agent's files are staged
- If unrelated files appear in status, do NOT stage them — leave them for the human

### Forbidden Operations
These commands are NEVER permitted unless a human explicitly requests them:
- `git reset --hard`
- `git checkout .`
- `git clean -fd`
- `git stash`
- `git add -A`
- `git add .`
- `git commit --no-verify`
- `git push --force` / `git push -f`

### Safe Git Workflow
```
git status                          # 1. See what changed
git add output/*.json               # 2. Stage ONLY output files
git status                          # 3. Verify staging is correct
git commit -m "add: content repurposer output (2026-02-11_1320)"
git pull --rebase                   # 5. Rebase before push
git push                            # 6. Push
```

### Commit Messages
- Include `fixes #<number>` or `closes #<number>` when a related issue exists
- No emojis in commit messages
- Be descriptive but concise — state what changed and why

### Conflict Resolution
- If `git pull --rebase` produces conflicts in files the agent did NOT modify, abort the rebase (`git rebase --abort`) and report the conflict to the human
- NEVER force push to resolve conflicts
- Only resolve conflicts in files the agent personally modified in the current session

### Commit Discipline
- NEVER commit unless explicitly instructed by the human or the workflow completes successfully
- When instructed to commit, follow the Safe Git Workflow above exactly
- One logical change per commit — do not bundle unrelated changes

## Operational Guardrails

These rules govern how agents interact with the codebase. Non-negotiable.

- You MUST read every file you modify in full before editing — no partial reads, no assumptions about content
- NEVER use `sed`, `cat`, `head`, or `tail` to read files — always use proper read tools
- Always ask before removing functionality or code that appears intentional — deletion is not a fix
- When writing tests, run them, identify issues, and iterate until fixed — do not commit failing tests
- NEVER commit unless explicitly instructed by the human or the workflow completes successfully
- When debugging, fix the root cause — do not remove code, skip tests, or disable checks to make errors disappear
- If a file has not been read in the current session, read it before modifying it — stale context leads to broken edits

## Style Rules

- No emojis in commits, issues, or code comments
- No fluff or cheerful filler text — every sentence must carry information
- Technical prose only — be kind but direct
- Keep answers short and concise
- No congratulatory or self-referential language ("Great question!", "I'd be happy to help!")
- Code comments explain why, not what — the code itself should be readable

## Anti-Patterns to Avoid

These are common mistakes that break WAT systems. Non-negotiable.

### Tool Anti-Patterns
- Do not write tools without `try/except` error handling — every tool must handle failures gracefully
- Do not write tools without a `main()` function — every tool must be independently executable
- Do not write tools that require interactive input — all tools must run unattended via CLI args, env vars, or stdin
- Do not catch bare `except:` — always catch specific exception types
- Do not hardcode API keys, tokens, or credentials in tool code — use environment variables
- Do not ignore tool exit codes — exit 0 on success, non-zero on failure

### Workflow Anti-Patterns
- Do not write workflow steps without failure modes — every step must define what can go wrong
- Do not write workflow steps without fallbacks — every failure mode must have a recovery action
- Do not skip validation because "it should work" — run all validation levels before packaging
- Do not create circular dependencies between workflow steps
- Do not design steps that silently swallow errors — log every failure with context

### Subagent Anti-Patterns
- Do not create subagents that call other subagents — only the main agent delegates
- Do not give subagents more tools than they need — principle of least privilege
- Do not write vague subagent descriptions — Claude uses these for automatic routing
- Do not use underscores in subagent names — always lowercase-with-hyphens

### Agent Teams Anti-Patterns
- Do not use Agent Teams when fewer than 3 independent tasks exist — the overhead is not justified
- Do not design teammates that depend on each other's output — they must be independent
- Do not skip the sequential fallback — every system must work without Agent Teams enabled
- Do not let teammates coordinate directly — all coordination goes through the team lead

### Git Anti-Patterns
- Do not use `git add -A` or `git add .` — stage only specific files
- Do not commit unless explicitly instructed by a human or the workflow completes
- Do not force push to resolve conflicts
- Do not commit .env files, credentials, or API keys

### Integration Anti-Patterns
- Do not create MCP-dependent tools without HTTP/API fallbacks
- Do not hardcode webhook URLs — use environment variables or secrets
- Do not skip secret validation in GitHub Actions — check required secrets exist before running
- Do not use `@latest` for pinned action versions in GitHub Actions

## Troubleshooting

- **Scraping fails with 404**: The blog post URL is incorrect or the page has been removed
- **Scraping fails with paywall**: Content is behind authentication — Firecrawl and HTTP both fail
- **Tone analysis returns low confidence (< 0.7)**: Content is too short, too technical, or ambiguous in style
- **Platform generation fails with rate limit**: Anthropic API rate limit exceeded — wait and retry
- **Character count exceeded**: Generated content is longer than platform limit — tool truncates automatically
- **Twitter thread is single tweet**: Content is short enough to fit in 280 chars — tool generates 1-tweet thread
- **Instagram hashtags rejected**: Hashtag contains spaces, special chars, or uppercase — tool validates and fixes
- **Tool fails with missing dependency**: Run `pip install -r requirements.txt` to install all dependencies
- **MCP not available**: Check your Claude Code MCP configuration or use the HTTP fallback (tools handle this)
- **Subagent not found**: Ensure `.claude/agents/` directory exists and contains the subagent .md files. Run `/agents` in Claude Code to verify.
- **Agent Teams not working**: Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` or disable and use sequential mode

## Platform-Specific Constraints

### Twitter
- **Character limit**: 280 per tweet (STRICT)
- **Thread format**: Numbered (1/N, 2/N, etc.)
- **Hook**: First tweet grabs attention
- **CTA**: Last tweet has call-to-action
- **Hashtags**: 2-3 total (distributed across thread)
- **Mentions**: Suggest @industry_leaders (without @ in JSON)

### LinkedIn
- **Character limit**: 3000 max, 1300 target for visibility
- **Hook**: First 1-2 sentences before "see more" button
- **Format**: Short paragraphs with line breaks
- **CTA**: Question or invitation to comment
- **Hashtags**: 3-5 industry-relevant

### Email
- **Subject line**: 40-60 chars, compelling and clear
- **Body**: 500-800 words (newsletter section, not full article)
- **Format**: H2/H3 headings, short paragraphs, bullet points
- **CTA**: Link back to full article
- **Output**: Both HTML and plain text versions

### Instagram
- **Character limit**: 2200 max, 1500-2000 target
- **Hook**: First line before "more" button
- **Format**: Line breaks every 2-3 sentences
- **Emojis**: 3-5 strategically placed (not excessive)
- **Hashtags**: 10-15 (mix of popular and niche)
- **Format**: Lowercase, alphanumeric + underscores only

## Cost & Performance

**Per Run**:
- Firecrawl API: $0.01-0.02 (1 scrape)
- Claude API: ~$0.09 (1 tone analysis + 4 platform generations)
- **Total**: ~$0.10-0.11 per blog post

**Execution Time**:
- Sequential mode: ~52-74 seconds
- Agent Teams mode: ~25-37 seconds

**Token Usage**:
- Scraping: No tokens (external API)
- Tone analysis: ~1,000 input + 200 output tokens
- Each platform: ~2,000 input + 600 output tokens
- **Total**: ~10,000 tokens per run (~$0.09 with Claude Sonnet 4)

## Success Criteria

✅ Source content extracted (≥ 100 chars)
✅ Tone analysis returns confidence ≥ 0.5
✅ At least 2/4 platforms generate successfully
✅ All character counts within platform limits
✅ Output JSON file written to `output/` directory
✅ File committed to repository

## Example Usage

### CLI
```bash
export ANTHROPIC_API_KEY=your_key
export FIRECRAWL_API_KEY=your_key
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

claude workflow.md --input '{
  "blog_url": "https://example.com/blog/my-post",
  "author_handle": "johndoe",
  "brand_hashtags": "YourBrand,ContentMarketing"
}'
```

### GitHub Actions (Manual Trigger)
1. Go to Actions tab
2. Select "Content Repurposer — WAT System"
3. Click "Run workflow"
4. Enter blog URL, optional author handle and hashtags
5. Click "Run workflow"
6. Check run logs and output file in `output/` directory

### GitHub Agent HQ (Issue-Driven)
1. Create issue: "Repurpose Blog Post: https://example.com/blog/my-post"
2. Body: "Author Handle: johndoe\nBrand Hashtags: YourBrand, ContentMarketing"
3. Assign to @claude
4. Review draft PR when ready
5. Merge or request changes
