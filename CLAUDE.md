# WAT Factory Bot

This document explains the WAT Factory Bot codebase for AI assistants working on this project. The WAT Factory Bot merges two systems: **thepopebot** (autonomous AI agent with Telegram chat, cron scheduling, and Docker-based job execution) and the **WAT Systems Factory** (a meta-system that builds deployable AI agent systems from natural language descriptions).

The bot can chat, handle tasks, run autonomous jobs -- AND build complete WAT systems (Workflows, Agents, Tools) when asked.

---

## Part 1: Agent Architecture (thepopebot)

### Two-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       WAT Factory Bot Architecture                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────┐                                                   │
│   │  Event Handler   │                                                   │
│   │  ┌────────────┐  │         1. create-job                            │
│   │  │  Telegram  │  │ ─────────────────────────►  ┌──────────────────┐ │
│   │  │   Cron     │  │                             │      GitHub      │ │
│   │  │   Chat     │  │ ◄─────────────────────────  │  (job/* branch)  │ │
│   │  └────────────┘  │   5. update-event-handler.yml calls             │ │
│   │                  │      /github/webhook        └────────┬─────────┘ │
│   └──────────────────┘                                      │           │
│            │                                                │           │
│            │                           2. run-job.yml       │           │
│            ▼                              triggers          │           │
│   ┌──────────────────┐                                      │           │
│   │ Telegram notifies│                                      ▼           │
│   │ user of job done │                         ┌──────────────────────┐ │
│   └──────────────────┘                         │    Docker Agent      │ │
│                                                │  ┌────────────────┐  │ │
│                                                │  │ 1. Clone       │  │ │
│                                                │  │ 2. Run Pi      │  │ │
│                                                │  │ 3. Commit      │  │ │
│                                                │  │ 4. Create PR   │  │ │
│                                                │  └────────────────┘  │ │
│                                                └──────────┬───────────┘ │
│                                                           │             │
│                                                           │ 3. PR opens │
│                                                           ▼             │
│                                                ┌──────────────────────┐ │
│                                                │       GitHub         │ │
│                                                │    (PR opened)       │ │
│                                                │ 4. auto-merge.yml    │ │
│                                                │ 5. update-event-     │ │
│                                                │    handler.yml       │ │
│                                                └──────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
/
├── .github/workflows/
│   ├── auto-merge.yml           # Auto-merges job PRs (checks AUTO_MERGE + ALLOWED_PATHS)
│   ├── docker-build.yml         # Builds and pushes Docker image to GHCR
│   ├── run-job.yml              # Runs Docker agent when job/* branch created
│   └── update-event-handler.yml # Notifies event handler when PR opened
├── .claude/
│   ├── commands/                # Slash commands for Claude Code
│   │   ├── generate-prp.md     # /generate-prp -- creates PRP from problem description
│   │   └── execute-prp.md      # /execute-prp -- builds system from PRP
│   └── skills/                  # Reusable skill modules
├── .pi/
│   ├── extensions/              # Pi extensions (env-sanitizer for secret filtering)
│   └── skills/                  # Custom skills for the Pi agent
├── config/                      # MCP registry, GitHub config
├── converters/                  # n8n-to-WAT format converters
├── docs/                        # Additional documentation
├── event_handler/               # Event Handler orchestration layer (DO NOT MODIFY)
│   ├── server.js                # Express HTTP server (webhooks, Telegram, GitHub)
│   ├── actions.js               # Shared action executor (agent, command, http)
│   ├── cron.js                  # Cron scheduler (loads CRONS.json)
│   ├── cron/                    # Working directory for command-type cron jobs
│   ├── triggers.js              # Webhook trigger middleware (loads TRIGGERS.json)
│   ├── triggers/                # Working directory for command-type trigger scripts
│   ├── claude/
│   │   ├── index.js             # Claude API integration for chat
│   │   ├── tools.js             # Tool definitions (create_job, get_job_status)
│   │   └── conversation.js      # Chat history management
│   └── tools/
│       ├── create-job.js        # Job creation via GitHub API
│       ├── github.js            # GitHub REST API helper + job status
│       └── telegram.js          # Telegram bot integration
├── factory/                     # WAT Systems Factory build engine
│   ├── workflow.md              # The factory's own build process
│   ├── tools/                   # Factory tool implementations (Python)
│   └── templates/               # Templates for generated artifacts
├── library/                     # Learned patterns and reusable tool catalog
│   ├── patterns.md              # Proven workflow patterns
│   └── tool_catalog.md          # Reusable tool patterns
├── operating_system/            # Agent character and behavior
│   ├── SOUL.md                  # Agent personality and identity
│   ├── CHATBOT.md               # Telegram chat system prompt
│   ├── JOB_SUMMARY.md           # Job completion summary prompt
│   ├── HEARTBEAT.md             # Periodic check instructions
│   ├── CRONS.json               # Scheduled job definitions
│   └── TRIGGERS.json            # Webhook trigger definitions
├── PRPs/                        # Product Requirements Prompts
│   ├── templates/
│   │   └── prp_base.md          # Base PRP template
│   └── {system-name}.md         # Generated PRPs (one per system request)
├── systems/                     # Output: completed WAT systems
│   └── {system}/                # Each system is self-contained
├── setup/                       # Interactive setup wizard
├── logs/                        # Per-job directories (job.md + session logs)
├── INITIAL.md                   # Simple intake template for system requests
├── Dockerfile                   # Container definition (DO NOT MODIFY)
├── entrypoint.sh                # Container startup script (DO NOT MODIFY)
└── SECURITY.md                  # Security documentation
```

### Key Files

| File | Purpose |
|------|---------|
| `operating_system/SOUL.md` | Agent personality and identity |
| `operating_system/CHATBOT.md` | System prompt for Telegram chat |
| `operating_system/JOB_SUMMARY.md` | Prompt for summarizing completed jobs |
| `logs/<JOB_ID>/job.md` | The specific task for the agent to execute |
| `Dockerfile` | Builds the agent container (Node.js 22, Playwright, Pi) |
| `entrypoint.sh` | Container startup script - clones repo, runs agent, commits results |
| `.pi/extensions/env-sanitizer/` | Filters secrets from LLM's bash subprocess environment |
| `factory/workflow.md` | The factory's build process for generating WAT systems |
| `library/patterns.md` | Proven workflow patterns for system generation |
| `library/tool_catalog.md` | Reusable tool patterns |
| `PRPs/templates/prp_base.md` | Base PRP template for system specifications |
| `INITIAL.md` | Simple intake template for non-technical users |

### Event Handler Layer

The Event Handler is a Node.js Express server that provides orchestration capabilities.

**DO NOT MODIFY** any files in `event_handler/`, `.github/workflows/`, `entrypoint.sh`, or `Dockerfile`.

#### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook` | POST | Generic webhook for job creation (requires API_KEY) |
| `/telegram/webhook` | POST | Telegram bot webhook for conversational interface |
| `/telegram/register` | POST | Register Telegram webhook URL |
| `/github/webhook` | POST | Receives notifications from GitHub Actions |
| `/jobs/status` | GET | Check status of a running job |

#### Components

- **server.js** - Express HTTP server handling all webhook routes
- **cron.js** - Loads CRONS.json and schedules jobs using node-cron
- **triggers.js** - Loads TRIGGERS.json and returns Express middleware for webhook triggers
- **claude/** - Claude API integration for Telegram chat with tool use
- **tools/** - Job creation, GitHub API, and Telegram utilities

#### Action Types: `agent`, `command`, and `http`

Both cron jobs and webhook triggers use the same shared dispatch system (`event_handler/actions.js`). Every action has a `type` field -- `"agent"` (default), `"command"`, or `"http"`.

| | `agent` | `command` | `http` |
|---|---------|-----------|--------|
| **Uses LLM** | Yes -- spins up Pi in a Docker container | No -- runs a shell command directly | No -- makes an HTTP request |
| **Thinking** | Can reason, make decisions, write code | No thinking, just executes | No thinking, just sends a request |
| **Runtime** | Minutes to hours (full agent lifecycle) | Milliseconds to seconds | Milliseconds to seconds |
| **Cost** | LLM API calls + GitHub Actions minutes | Free (runs on event handler) | Free (runs on event handler) |

If the task needs to *think*, use `agent`. If it just needs to *do*, use `command`. If it needs to *call an external service*, use `http`.

##### Type: `agent` (default)

Creates a full Docker Agent job via `createJob()`. This pushes a `job/*` branch to GitHub, which triggers `run-job.yml` to spin up the Docker container with Pi. The `job` string is passed directly as-is to the LLM as its task prompt (written to `logs/<JOB_ID>/job.md` on the job branch).

**Best practice:** Keep the `job` field short. Put detailed task instructions in a dedicated markdown file in `operating_system/` and reference it by path:

```json
"job": "Read the file at operating_system/MY_TASK.md and complete the tasks described there."
```

##### Type: `command`

Runs a shell command directly on the event handler server. No Docker container, no GitHub branch, no LLM. Working directories:
- **Crons**: `event_handler/cron/`
- **Triggers**: `event_handler/triggers/`

##### Type: `http`

Makes an HTTP request to an external URL. No Docker container, no LLM.

**Outgoing body logic:**
- `GET` requests skip the body entirely
- `POST` (default) sends `{ ...vars }` if no incoming data, or `{ ...vars, data: <incoming payload> }` when triggered by a webhook

### Cron Jobs

Cron jobs are defined in `operating_system/CRONS.json` and loaded by `event_handler/cron.js` at startup using `node-cron`.

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Display name for logging | Yes |
| `schedule` | Cron expression (e.g., `*/30 * * * *`) | Yes |
| `type` | `agent` (default), `command`, or `http` | No |
| `job` | Task description for agent type | For `agent` |
| `command` | Shell command for command type | For `command` |
| `url` | Target URL for http type | For `http` |
| `enabled` | Set to `false` to disable without deleting | No |

### Webhook Triggers

Webhook triggers are defined in `operating_system/TRIGGERS.json` and loaded by `event_handler/triggers.js` as Express middleware. They fire actions when existing endpoints are hit.

Template tokens for `job` and `command` strings:
- `{{body}}` -- full request body as JSON
- `{{body.field}}` -- a specific field from the body
- `{{query}}` / `{{query.field}}` -- query string params
- `{{headers}}` / `{{headers.field}}` -- request headers

### Environment Variables (Event Handler)

| Variable | Description | Required |
|----------|-------------|----------|
| `API_KEY` | Authentication key for /webhook endpoint | Yes |
| `GH_TOKEN` | GitHub PAT for creating branches/files | Yes |
| `GH_OWNER` | GitHub repository owner | Yes |
| `GH_REPO` | GitHub repository name | Yes |
| `PORT` | Server port (default: 3000) | No |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather | For Telegram |
| `TELEGRAM_WEBHOOK_SECRET` | Secret for webhook validation | No |
| `GH_WEBHOOK_SECRET` | Secret for GitHub Actions webhook auth | For notifications |
| `ANTHROPIC_API_KEY` | Claude API key for chat functionality | For chat |
| `EVENT_HANDLER_MODEL` | Claude model for chat (default: claude-sonnet-4) | No |

### Docker Agent Layer

The Dockerfile creates a container with Node.js 22, Pi coding agent, Playwright + Chromium, and Git + GitHub CLI.

#### Runtime Flow (entrypoint.sh)

1. Extract Job ID from branch name (job/uuid -> uuid) or generate UUID
2. Start headless Chrome (CDP on port 9222)
3. Decode `SECRETS` from base64, parse JSON, export each key as env var (filtered from LLM's bash)
4. Decode `LLM_SECRETS` from base64, parse JSON, export each key as env var (LLM can access these)
5. Configure Git credentials via `gh auth setup-git`
6. Clone repository branch to `/job`
7. Run Pi with SOUL.md + job.md as prompt
8. Save session log to `logs/{JOB_ID}/`
9. Commit all changes
10. Create PR via `gh pr create` (auto-merge handled by `auto-merge.yml`)

### GitHub Actions

GitHub Actions automate the job lifecycle. **DO NOT MODIFY** these workflow files.

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `docker-build.yml` | Push to `main` | Builds Docker image, pushes to GHCR |
| `run-job.yml` | `job/*` branch created | Runs Docker agent container |
| `auto-merge.yml` | PR opened from `job/*` | Checks ALLOWED_PATHS, merges PR |
| `update-event-handler.yml` | After auto-merge completes | Notifies event handler |

#### GitHub Repository Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GH_WEBHOOK_URL` | Event handler URL | -- |
| `AUTO_MERGE` | Set to `false` to disable auto-merge | Enabled |
| `ALLOWED_PATHS` | Comma-separated path prefixes for auto-merge | `/logs` |
| `IMAGE_URL` | Full Docker image path | Not set (uses `stephengpope/thepopebot:latest`) |
| `MODEL` | Anthropic model ID for the Pi agent | Not set (Pi default) |

**IMPORTANT:** For the WAT Factory Bot, set `ALLOWED_PATHS` to `/systems,/library,/PRPs,/logs,/factory` so that factory-generated system files can be auto-merged.

### How Credentials Work

Credentials are passed via base64-encoded JSON in the `SECRETS` environment variable. The `env-sanitizer` extension filters these from the LLM's bash subprocess. For credentials the LLM needs access to (browser logins, skill API keys), use `LLM_SECRETS` instead.

### The Operating System

Files in `operating_system/` define the agent's character and behavior:

- **SOUL.md** - Personality, identity, and values
- **CHATBOT.md** - System prompt for Telegram chat
- **JOB_SUMMARY.md** - Prompt for summarizing completed jobs
- **HEARTBEAT.md** - Self-monitoring behavior
- **CRONS.json** - Scheduled job definitions
- **TRIGGERS.json** - Webhook trigger definitions

### Session Logs

Each job gets its own directory at `logs/{JOB_ID}/` containing job.md and session logs (.jsonl).

### Markdown File Includes

Markdown files in `operating_system/` support `{{filepath}}` include syntax, powered by `event_handler/utils/render-md.js`. Paths resolve relative to the repo root. Recursive includes supported with circular protection.

---

## Part 2: WAT Systems Factory

The WAT Systems Factory is a meta-system that builds deployable AI agent systems. Every system it produces follows the WAT framework (Workflows, Agents, Tools) and runs autonomously via GitHub Actions.

### WAT Framework

Three components make up every WAT system:

- **Agent**: Claude Code. The AI brain that executes workflows, makes decisions, and runs tools.
- **Workflows**: Markdown (.md) files. Natural language process instructions.
- **Tools**: Python (.py) files. Executable actions the agent performs.

### Factory Build Process

To build a new WAT system, follow `factory/workflow.md`:

1. **Intake** -- Receive PRP file, problem description, or n8n JSON
2. **Research** -- Check MCP registry and tool catalog
3. **Design** -- Architect the workflow, identify subagents, analyze Agent Teams
4. **Generate Workflow** -- Write workflow.md
5. **Generate Tools** -- Write Python tools
5b. **Generate Subagents** -- Write .claude/agents/ files
6. **Generate GitHub Actions** -- Create .github/workflows/ files
7. **Generate CLAUDE.md** -- Write operating instructions
8. **Test** -- 3-level validation gates (syntax, unit, integration)
9. **Package** -- Bundle into self-contained system
10. **Learn** -- Extract patterns, update library

### PRP Workflow (Recommended Intake Path)

The PRP (Product Requirements Prompt) is a structured intake layer. It expands a simple problem description into a comprehensive, validated specification before the factory builds anything.

**Step 1: Generate PRP** -- Takes a problem description, researches patterns/tools/MCPs, designs subagent architecture, produces a full PRP at `PRPs/{system-name}.md` with a confidence score (1-10).

**Step 2: Review, then Build** -- Reads the PRP, validates confidence score (halts if below 7/10), checks ambiguity flags, executes `factory/workflow.md`, runs 3-level validation, packages into `systems/{system-name}/`.

### WAT Framework Rules

#### Workflow Rules
- All workflows MUST be Markdown (.md) files
- Use clear headers (##) for each phase
- Every workflow must declare: **Inputs**, **Outputs**, **Failure Modes**, and **Fallback Steps**

#### Tool Rules
- All tools MUST be Python (.py) files
- Every tool MUST have: module-level docstring, `main()` function, `try/except` error handling, logging, type hints
- Tools must be independently executable: `python tool_name.py`

#### System Rules
Every generated WAT system MUST be a self-contained repo containing:
- `CLAUDE.md`, `workflow.md`, `tools/`, `.claude/agents/`, `.github/workflows/`, `requirements.txt`, `README.md`, `.env.example`, `.gitignore`

### Subagent Rules

Custom subagents are the DEFAULT delegation mechanism in every WAT system. Each system gets specialist subagent definitions as `.claude/agents/` markdown files.

- One subagent per domain
- Minimal tool access (principle of least privilege)
- Detailed system prompts
- Naming: `{function}-specialist`, `{function}-agent`, `{function}-reviewer`
- No cross-subagent calls -- only the main agent delegates

### Agent Teams Rules

Agent Teams is for parallel multi-agent execution. Use the **3+ Independent Tasks Rule**: if the system has 3+ tasks with no data dependencies, recommend Agent Teams. Otherwise, sequential execution is sufficient.

- ALWAYS provide a sequential fallback
- Each teammate gets a focused, scoped task
- The team lead merges results and does final quality control

### Self-Improvement Mechanism

The factory learns from every system it builds:
1. After each build, update `library/patterns.md` with new patterns
2. After each build, update `library/tool_catalog.md` with new tools
3. Track what works and what fails

### Quality Standards

#### Tool Quality Gates
- Every tool must have `try/except` error handling
- Every tool must log via `logging`
- Every tool must have clear docstrings
- Every tool should exit 0 on success, non-zero on failure

#### Workflow Quality Gates
- Every workflow must define failure modes and fallbacks
- Every workflow must declare inputs and outputs

### File References (Factory)

| File | Purpose |
|------|---------|
| `INITIAL.md` | Simple intake template -- fill out and generate PRP |
| `.claude/commands/generate-prp.md` | Slash command: generates PRP from problem description |
| `.claude/commands/execute-prp.md` | Slash command: builds WAT system from PRP |
| `PRPs/templates/prp_base.md` | Base template for generated PRPs |
| `factory/workflow.md` | The factory's build process |
| `factory/templates/*` | Templates for generated artifacts |
| `factory/tools/*` | Factory tool implementations |
| `config/mcp_registry.md` | Available MCPs and capabilities |
| `library/patterns.md` | Proven workflow patterns |
| `library/tool_catalog.md` | Reusable tool patterns |
| `converters/n8n_node_map.md` | n8n node to WAT mapping reference |

---

## Part 3: Operational Rules

### CRITICAL Git Rules

- ONLY commit files the agent changed in the current session
- ALWAYS use `git add <specific-file-paths>` -- NEVER `git add -A` or `git add .`
- Before committing, run `git status` and verify only the agent's files are staged
- NEVER commit unless explicitly instructed by the human
- NEVER use `git reset --hard`, `git checkout .`, `git clean -fd`, `git stash`, `git push --force`

### Style Rules

- No emojis in commits, issues, or code comments
- No fluff or cheerful filler text
- Technical prose only -- be kind but direct
- Keep answers short and concise
- Code comments explain why, not what

### Anti-Patterns to Avoid

- Do not hardcode API keys, tokens, or credentials
- Do not use `git add -A` or `git add .`
- Do not skip validation because "it should work"
- Do not catch bare `except:` -- always catch specific exception types
- Do not build tools that require interactive input
- Do not create MCP-dependent tools without HTTP/API fallbacks
- Do not design subagents that call other subagents
- Do not use Agent Teams when fewer than 3 independent tasks exist
- Do not build from a PRP with unresolved ambiguity flags
- Do not modify a PRP during build execution

### Files That Must NOT Be Modified

These files are part of the core agent infrastructure and must not be changed:
- `event_handler/**` -- All event handler code
- `.github/workflows/**` -- All GitHub Actions workflows
- `entrypoint.sh` -- Container startup script
- `Dockerfile` -- Container definition
