# {System Name}

{Brief description: what this system does and why.}

## System Overview

- **Type**: WAT System (Workflow, Agent, Tools)
- **Purpose**: {One-sentence purpose}
- **Pattern**: {Pattern name from library/patterns.md}

## Execution

This system can be run three ways:

1. **Claude Code CLI**: Run `workflow.md` directly in the terminal
2. **GitHub Actions**: Trigger via Actions UI, API, or cron schedule
3. **GitHub Agent HQ**: Assign an issue to @claude with task input in the body

## Inputs

- **{input_name}** ({type}): {Description and expected format}

## Outputs

- **{output_name}** ({type}): {Description and where it goes}

## Workflow

Follow `workflow.md` for the step-by-step process. Key phases:

1. {Phase 1 name} — {Brief description}
2. {Phase 2 name} — {Brief description}
3. {Phase N name} — {Brief description}

## Tools

| Tool | Purpose |
|------|---------|
| `tools/{tool_1}.py` | {What it does} |
| `tools/{tool_2}.py` | {What it does} |

## Subagents

This system uses specialist subagents defined in `.claude/agents/`. Subagents are the DEFAULT delegation mechanism — when the workflow reaches a phase, delegate to the appropriate subagent.

### Available Subagents

| Subagent | Description | Tools | When to Use |
|----------|-------------|-------|-------------|
| `{subagent_1}` | {Description} | {tools} | {When this subagent should be invoked} |
| `{subagent_2}` | {Description} | {tools} | {When this subagent should be invoked} |
| `{subagent_3}` | {Description} | {tools} | {When this subagent should be invoked} |

### How to Delegate

Subagents are invoked automatically based on their `description` field or explicitly:
```
Use the {subagent-name} subagent to handle {task description}
```

### Subagent Chaining

For multi-step workflows, chain subagents sequentially — each subagent's output becomes the next subagent's input:

1. **{subagent_1}** produces `{output_1}` → feeds into
2. **{subagent_2}** produces `{output_2}` → feeds into
3. **{subagent_3}** produces `{output_3}` → final result

The main agent coordinates this chain, reading outputs and delegating to the next subagent.

### Delegation Hierarchy

- **Subagents are the default** for all task delegation. Use them for every workflow phase.
- **Agent Teams is ONLY for parallelization** — when 3+ independent subagent tasks can run concurrently.
- This system {uses / does not use} Agent Teams. See the Agent Teams section below for details.

## MCP Dependencies

This system uses the following MCPs. Alternatives are listed for flexibility.

| Capability | Primary MCP | Alternative | Fallback |
|-----------|-------------|-------------|----------|
| {capability} | {MCP name} | {Alt MCP} | {Direct API/HTTP} |

**Important**: No MCP is hardcoded. If a listed MCP is unavailable, the system falls back to the alternative or direct API calls. Configure your preferred MCPs in your Claude Code settings.

## Required Secrets

These must be set as GitHub Secrets (for Actions) or environment variables (for CLI):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution | Yes |
| `{SECRET_NAME}` | {Purpose} | {Yes/No} |

## Agent Teams

{If Agent Teams is recommended — include this section:}

This system supports **native Claude Code Agent Teams** for parallel execution. When enabled, a team lead agent coordinates teammate agents that work concurrently on independent tasks. **Agent Teams is a parallelization optimization — subagents remain the default delegation mechanism.**

### How It Works

- **Team Lead**: The primary agent running the workflow. It creates a shared task list, spawns teammates, monitors progress, and merges results.
- **Teammates**: Each handles one independent task. They work in isolation, update their task status, and write output for the team lead to collect.
- **Shared Task List**: Coordination happens through `TaskCreate`, `TaskUpdate`, `TaskList`, and `TaskGet`. Tasks flow: `pending` → `in_progress` → `completed`.

### Parallel Tasks in This System

| Teammate | Task | What It Does |
|----------|------|--------------|
| {teammate_1} | {task_name} | {Brief description} |
| {teammate_2} | {task_name} | {Brief description} |
| {teammate_3} | {task_name} | {Brief description} |

### Enabling Agent Teams

Set the environment variable before running:
```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```
- **Locally**: Add to your `.env` file
- **GitHub Actions**: Add as a repository secret or environment variable in the workflow YAML
- **To disable**: Remove the variable or set to `0`

### Sequential Fallback

Without Agent Teams enabled, all tasks run sequentially in the order listed above. **Results are identical** — the only difference is execution time. This system is designed to work correctly in both modes.

### Token Cost

- Agent Teams spawns {N} teammate agents for parallel sections
- Token usage scales ~{N}x for those sections (each teammate has its own context)
- Sequential execution uses fewer tokens but takes longer
- **Recommendation**: Use Agent Teams in production when speed matters. Use sequential for development/debugging or when minimizing cost.

{If Agent Teams is NOT recommended — include this instead:}

This system does not use Agent Teams. All tasks are sequential or have dependencies that prevent parallelization. No additional configuration is needed.

## Agent HQ Usage

To run via GitHub Agent HQ:

1. Create an issue with the title: `{Expected title format}`
2. In the issue body, provide:
   ```
   {Expected input format}
   ```
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
- Do not commit unless explicitly instructed by a human
- Do not force push to resolve conflicts
- Do not commit .env files, credentials, or API keys

### Integration Anti-Patterns
- Do not create MCP-dependent tools without HTTP/API fallbacks
- Do not hardcode webhook URLs — use environment variables or secrets
- Do not skip secret validation in GitHub Actions — check required secrets exist before running
- Do not use `@latest` for pinned action versions in GitHub Actions

## Front-End (if applicable)

{If the system has a generated front-end — include this section:}

This system includes an interactive web front-end (Next.js) and API bridge (FastAPI).

### Local Development

```bash
# Terminal 1: Start the API server
pip install -r requirements.txt -r api/requirements.txt
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start the frontend dev server
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check — returns system status |
| POST | `/api/run-pipeline` | Run the full tool pipeline in workflow order |
{For each tool:}
| POST | `/api/{tool-name}` | Run {tool description} |

### Frontend Structure

- `frontend/src/app/(marketing)/` — Landing page, feature overview
- `frontend/src/app/(dashboard)/` — Tool forms, results, pipeline wizard
- `frontend/src/components/` — Reusable UI components (ToolForm, ResultViewer, PipelineWizard)

### Docker Deployment

```bash
docker compose -f docker-compose.frontend.yml up --build
# App available at http://localhost:8000
```

The single container serves both the API (`/api/*`) and the static frontend (`/*`).

### Design Configuration

- `frontend_design.json` — UI design settings (archetype, fonts, palette, hero content)
- `system_interface.json` — Tool schemas (source of truth for form generation and API endpoints)

{If the system does NOT have a front-end — omit this section entirely.}

## Troubleshooting

- **{Common issue 1}**: {Solution}
- **{Common issue 2}**: {Solution}
- **Tool fails with missing dependency**: Run `pip install -r requirements.txt`
- **MCP not available**: Check your Claude Code MCP configuration or use the HTTP fallback
- **Subagent not found**: Ensure `.claude/agents/` directory exists and contains the subagent .md files. Run `/agents` in Claude Code to verify.
- **Frontend build fails**: Run `cd frontend && npm install` then `npm run build`. Check for TypeScript errors.
- **API bridge import error**: Verify tools are import-safe (no `sys.exit()` at module level). Run `python -c "from tools.{tool_name} import main"` to test.
- **CORS error in browser**: Set `CORS_ORIGINS` environment variable to include your frontend URL.
