# Marketing Pipeline

A lead enrichment, scoring, segmentation, and outreach generation pipeline. Takes a CSV of leads, enriches each with company data and decision-maker contacts via Apollo/Hunter/Brave, deep-scores on 5 dimensions (0-100), segments into Hot/Warm/Cold tiers, and generates personalized email sequences for outreach and nurture.

## System Overview

- **Type**: WAT System (Workflow, Agent, Tools)
- **Purpose**: Transform raw lead lists into segmented, enriched, actionable pipeline with personalized outreach content
- **Pattern**: Intake > Enrich > Deliver + Generate > Review > Publish

## Execution

This system can be run three ways:

1. **Claude Code CLI**: Run `workflow.md` directly in the terminal
2. **GitHub Actions**: Trigger via Actions UI, API, or weekly cron schedule (Mondays 09:00 UTC)
3. **GitHub Agent HQ**: Assign an issue to @claude with a CSV path or lead data in the body

## Inputs

- **leads_csv** (file path): Path to a CSV file with at minimum a `company_name` column. Optional columns: `website`, `industry`, `location`, `company_size`, `notes`.

Input sources (checked in order):
1. `TASK_INPUT` environment variable
2. `--input` CLI argument
3. Most recent `.csv` file in `input/` directory

Example CSV:
```csv
company_name,website,industry,location,company_size
Acme Corp,https://acme.com,SaaS,San Francisco CA,50-200
WidgetCo,https://widgetco.io,Fintech,New York NY,200-500
```

## Outputs

- **output/enriched_leads_{timestamp}.csv** — Full enriched data for all leads
- **output/hot_leads.csv** — Hot tier leads (score 80+), ready for direct outreach
- **output/warm_leads.csv** — Warm tier leads (score 50-79), nurture sequence
- **output/outreach/emails_{company}.md** — Personalized 3-email cold outreach sequence per hot lead
- **output/nurture/sequence.md** — 5-email nurture drip content for warm leads
- **output/pipeline_summary.json** — Run stats, score distribution, segment breakdown

## Workflow

Follow `workflow.md` for the step-by-step process. Key phases:

1. **Ingest** — Parse, validate, and deduplicate the input CSV
2. **Enrich** — Pull company data, contacts, tech stack, and pain signals via APIs
3. **Score** — Deep-score leads on 5 dimensions (0-100)
4. **Segment** — Sort into Hot (80+), Warm (50-79), Cold (<50) tiers
5. **Generate Outreach** — Personalized 3-email sequences for Hot leads
6. **Generate Nurture** — 5-email drip sequence for Warm leads
7. **Output** — Generate all CSVs and summary JSON
8. **Commit** — Commit results to repo

## Tools

| Tool | Purpose |
|------|---------|
| `tools/ingest_leads.py` | Reads, validates, and deduplicates the input CSV |
| `tools/enrich_leads.py` | Enriches leads via Apollo, Hunter, Brave, and Claude APIs |
| `tools/score_leads.py` | Deep-scores leads on 5 dimensions (0-100) |
| `tools/segment_leads.py` | Segments scored leads into Hot/Warm/Cold tiers |
| `tools/generate_outreach.py` | Generates personalized 3-email cold outreach sequences |
| `tools/generate_nurture.py` | Generates 5-email nurture drip sequence |
| `tools/output_pipeline.py` | Generates all output CSVs and summary JSON |

## Subagents

This system uses specialist subagents defined in `.claude/agents/`. Subagents are the DEFAULT delegation mechanism — when the workflow reaches a phase, delegate to the appropriate subagent.

### Available Subagents

| Subagent | Description | Tools | When to Use |
|----------|-------------|-------|-------------|
| `enrichment-specialist` | Data enrichment via Apollo, Hunter, Brave, Claude | Read, Bash, Grep | Step 2: Enriching leads |
| `scoring-specialist` | Lead scoring and segmentation | Read, Bash, Write | Steps 3-4: Scoring and segmenting |
| `outreach-specialist` | Cold email outreach generation | Read, Bash, Write | Step 5: Generating outreach for Hot leads |
| `nurture-specialist` | Nurture sequence generation | Read, Bash, Write | Step 6: Generating nurture for Warm leads |
| `pipeline-reviewer` | Output quality validation | Read, Bash, Grep, Glob | After Step 7: Validating outputs before commit |

### How to Delegate

Subagents are invoked automatically based on their `description` field, or explicitly:
```
Use the enrichment-specialist subagent to enrich the ingested leads
Use the scoring-specialist subagent to score and segment the enriched leads
Use the outreach-specialist subagent to generate outreach for hot leads
Use the nurture-specialist subagent to generate nurture sequence for warm leads
Use the pipeline-reviewer subagent to validate all outputs
```

### Subagent Chaining

The pipeline chains subagents sequentially:

1. **enrichment-specialist** produces `output/enriched_leads.json` -> feeds into
2. **scoring-specialist** produces `output/scored_leads.json` and `output/segmented_leads.json` -> feeds into
3. **outreach-specialist** produces `output/outreach/emails_*.md` (independent)
4. **nurture-specialist** produces `output/nurture/sequence.md` (independent)
5. **pipeline-reviewer** validates all outputs

Steps 3 and 4 are independent and can run in parallel with Agent Teams.

### Delegation Hierarchy

- **Subagents are the default** for all task delegation in this system.
- **Agent Teams is optional** — Steps 5 and 6 (outreach + nurture generation) can run in parallel.
- **Parallelization opportunity**: Per-lead enrichment in Step 2 can also be parallelized.

## MCP Dependencies

This system uses the following MCPs. Alternatives are listed for flexibility.

| Capability | Primary MCP | Alternative | Fallback |
|-----------|-------------|-------------|----------|
| Company enrichment | — (Apollo.io HTTP API) | — | Brave Search + Claude |
| Email verification | — (Hunter.io HTTP API) | — | Apollo contacts only |
| Web search/research | Brave Search MCP | Google Custom Search | Direct HTTP |
| Email generation | Claude (built-in) | — | Manual email writing |
| Pain signal analysis | Claude (built-in) | — | Keyword matching |

**Important**: No MCP is hardcoded. Apollo and Hunter are accessed via direct HTTP API calls. If any API is unavailable, the system degrades gracefully with reduced data quality.

## Required Secrets

These must be set as GitHub Secrets (for Actions) or environment variables (for CLI):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution, email generation, pain signal analysis | Yes |
| `APOLLO_API_KEY` | Apollo.io company enrichment and contact discovery | No (Brave+Claude fallback) |
| `HUNTER_API_KEY` | Hunter.io email verification and discovery | No (Apollo contacts only) |
| `BRAVE_API_KEY` | Brave Search for company research | No (reduced research quality) |
| `GITHUB_TOKEN` | Committing results and issue management | Yes (auto-provided in Actions) |

### Local Environment Setup

For CLI execution, copy `.env.example` to `.env` and fill in your actual API keys:

```bash
cp .env.example .env
# Edit .env with your real values
```

**NEVER commit `.env` to version control.** The `.gitignore` already excludes it.

## Scoring Dimensions

Leads are scored 0-100 across 5 dimensions:

| Dimension | Max Points | What It Measures |
|-----------|-----------|------------------|
| Company Size Fit | 20 | Does the company size match the target range? |
| Tech Stack Compatibility | 25 | Do they use automation tools (n8n, Zapier, Make, etc)? |
| Budget Signals | 20 | Job postings for ops roles, recent funding, growth indicators |
| Decision Maker Accessibility | 15 | Direct emails found, LinkedIn profiles, multiple contacts |
| Pain Signal Detection | 20 | Hiring for ops, manual process complaints, automation-seeking |

### Tier Thresholds

| Tier | Score Range | Action |
|------|-------------|--------|
| Hot | 80-100 | Direct personalized outreach (3-email sequence) |
| Warm | 50-79 | Educational nurture drip (5-email sequence) |
| Cold | 0-49 | Archive for later review |

## Agent Teams

This system supports **native Claude Code Agent Teams** for parallel execution of Steps 5 and 6 (outreach + nurture generation). These steps are fully independent — outreach needs Hot leads, nurture needs Warm leads, and they share no data.

### Parallel Tasks in This System

| Teammate | Task | What It Does |
|----------|------|--------------|
| Outreach Generator | Generate outreach sequences | Creates personalized 3-email sequences for each Hot lead |
| Nurture Generator | Generate nurture sequence | Creates 5-email drip informed by Warm lead characteristics |

### Enabling Agent Teams

Set the environment variable before running:
```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```
- **Locally**: Add to your `.env` file
- **GitHub Actions**: Add as a repository secret or environment variable
- **To disable**: Remove the variable or set to `0`

### Sequential Fallback

Without Agent Teams enabled, Steps 5 and 6 run sequentially. **Results are identical** — the only difference is execution time.

### Token Cost

- Agent Teams spawns 2 teammate agents for Steps 5-6
- Token usage scales ~2x for those sections (each teammate has its own context)
- Sequential execution uses fewer tokens but takes longer
- **Recommendation**: Use Agent Teams when processing 5+ Hot leads for meaningful time savings

## Agent HQ Usage

To run via GitHub Agent HQ:

1. Create an issue with the title: `Pipeline: Process {description} leads`
2. In the issue body, provide either:
   - A path to a CSV in the repo: `input/my_leads.csv`
   - Or CSV content directly (the agent will save it to a temp file)
3. Assign the issue to @claude
4. The agent will process the request and open a draft PR with results
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
git add path/to/file1 path/to/file2 # 2. Stage ONLY your files
git status                          # 3. Verify staging is correct
git commit -m "descriptive message"  # 4. Commit with clear message
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
- NEVER commit unless explicitly instructed by the human
- When instructed to commit, follow the Safe Git Workflow above exactly
- One logical change per commit — do not bundle unrelated changes

## Operational Guardrails

These rules govern how agents interact with the codebase. Non-negotiable.

- You MUST read every file you modify in full before editing — no partial reads, no assumptions about content
- NEVER use `sed`, `cat`, `head`, or `tail` to read files — always use proper read tools
- Always ask before removing functionality or code that appears intentional — deletion is not a fix
- When writing tests, run them, identify issues, and iterate until fixed — do not commit failing tests
- NEVER commit unless explicitly instructed by the human
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

### Tool Anti-Patterns
- Do not write tools without `try/except` error handling
- Do not write tools without a `main()` function
- Do not write tools that require interactive input
- Do not catch bare `except:` — always catch specific exception types
- Do not hardcode API keys, tokens, or credentials
- Do not ignore tool exit codes

### Workflow Anti-Patterns
- Do not write workflow steps without failure modes
- Do not write workflow steps without fallbacks
- Do not skip validation
- Do not create circular dependencies
- Do not silently swallow errors

### Subagent Anti-Patterns
- Do not create subagents that call other subagents
- Do not give subagents more tools than they need
- Do not write vague subagent descriptions
- Do not use underscores in subagent names

### Git Anti-Patterns
- Do not use `git add -A` or `git add .`
- Do not commit unless explicitly instructed
- Do not force push to resolve conflicts
- Do not commit .env files, credentials, or API keys

### Integration Anti-Patterns
- Do not create MCP-dependent tools without HTTP/API fallbacks
- Do not hardcode webhook URLs
- Do not skip secret validation in GitHub Actions
- Do not use `@latest` for pinned action versions

## Troubleshooting

- **No leads found in CSV**: Check that the CSV has a `company_name` column (case-insensitive)
- **All leads scoring low**: Enrichment may have failed — check API keys are set. Low enrichment = low scores.
- **No Hot leads**: Scores below 80 across the board may indicate the lead list doesn't match the scoring criteria. Try adjusting thresholds with `--hot-threshold 70`
- **Apollo API errors**: Verify `APOLLO_API_KEY` is valid. The system will fall back to Brave+Claude.
- **Hunter API errors**: Not critical — Apollo provides contacts too. System continues without Hunter.
- **Outreach generation fails**: Requires `ANTHROPIC_API_KEY`. Check it's set and has sufficient quota.
- **Tool fails with missing dependency**: Run `pip install -r requirements.txt`
- **MCP not available**: This system uses direct HTTP API calls, not MCPs. No MCP configuration needed.
- **Subagent not found**: Ensure `.claude/agents/` directory exists and contains the subagent .md files.
