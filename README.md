# WAT Factory Bot

**Autonomous AI agent that builds complete AI-powered systems from natural language.**

Chat with it on Telegram. Ask it to build you a system. It generates the spec, builds the code, tests it, and delivers a deployable package -- all autonomously.

---

## What Is This?

The WAT Factory Bot merges two systems:

1. **thepopebot** -- An autonomous AI agent template with Telegram chat, cron scheduling, webhook triggers, and Docker-based job execution via GitHub Actions
2. **WAT Systems Factory** -- A meta-system that generates complete, deployable AI agent systems from natural language descriptions

The result: a bot you can talk to on Telegram that can chat, handle tasks, run background jobs -- AND build entire WAT systems (Workflows, Agents, Tools) when you say "build me a [anything]".

---

## How It Works

### Simple Chat & Tasks

```
You: "What's the weather in NYC?"
Bot: [searches web, responds]

You: "Create a job to update the README"
Bot: [presents job description, gets approval, creates job]
Bot: [notifies you when done]
```

### Building Systems

```
You: "Build me a lead generation system"
Bot: "What problem are you solving? What goes in? What comes out?"
You: [describe requirements]
Bot: [generates PRP spec, asks for approval]
Bot: [builds complete WAT system: workflow, tools, GitHub Actions, docs]
Bot: "Done! System is at systems/lead-gen-system/"
```

### Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ┌─────────────────┐         ┌─────────────────┐                     │
│  │  Event Handler  │ ──1──►  │     GitHub      │                     │
│  │  (Telegram +    │         │ (job/* branch)  │                     │
│  │   webhooks)     │         └────────┬────────┘                     │
│  └────────▲────────┘                  │                              │
│           │                  2. Docker Agent runs                     │
│           │                     (builds systems,                     │
│           │                      executes tasks)                     │
│           │                           │                              │
│           │                  3. PR with results                      │
│           │                           │                              │
│           5. Notification    4. Auto-merge                           │
│           └───────────────────────────┘                              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## What's a WAT System?

Every system the factory builds follows the WAT framework:

| Component | Format | Role |
|-----------|--------|------|
| **Workflows** | Markdown (.md) | Natural language process instructions |
| **Agents** | Claude Code | The AI brain that executes workflows |
| **Tools** | Python (.py) | Executable actions |

Generated systems are self-contained and include: `workflow.md`, `tools/`, `.github/workflows/`, `CLAUDE.md`, `README.md`, `requirements.txt`, `.env.example`.

---

## Get Started

### Prerequisites

| Requirement | Install |
|-------------|---------|
| **Node.js 18+** | [nodejs.org](https://nodejs.org) |
| **npm** | Included with Node.js |
| **Git** | [git-scm.com](https://git-scm.com) |
| **GitHub CLI** | [cli.github.com](https://cli.github.com) |
| **ngrok*** | [ngrok.com](https://ngrok.com/download) |

*\*ngrok is only required for local development.*

### Three Steps

**Step 1** -- Fork this repository and enable GitHub Actions in the Actions tab.

**Step 2** -- Clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/thepopebot.git
cd thepopebot
```

**Step 3** -- Run the setup wizard:

```bash
npm run setup
```

The wizard handles everything: prerequisites, GitHub PAT, API keys, secrets, Telegram bot setup, server startup, and webhook registration.

### Configure ALLOWED_PATHS

For factory-generated systems to auto-merge, set this GitHub repository variable:

**Settings > Secrets and variables > Actions > Variables**

| Variable | Value |
|----------|-------|
| `ALLOWED_PATHS` | `/systems,/library,/PRPs,/logs,/factory` |

This allows the bot's jobs to commit factory output (generated systems, pattern library updates, PRPs) in addition to logs.

---

## Project Structure

```
/
├── event_handler/           # Telegram bot + webhook server (Node.js)
├── operating_system/        # Bot personality, chat prompts, cron/trigger configs
├── factory/                 # WAT Systems Factory build engine
│   ├── workflow.md          # The factory's build process
│   ├── tools/               # Factory tools (Python)
│   └── templates/           # Templates for generated artifacts
├── library/                 # Learned patterns and reusable tools
├── PRPs/                    # Product Requirements Prompts (system specs)
├── systems/                 # Output: completed WAT systems
├── config/                  # MCP registry, GitHub config
├── converters/              # n8n-to-WAT converters
├── .claude/commands/        # Claude Code slash commands (/generate-prp, /execute-prp)
├── .claude/skills/          # Reusable skill modules
├── .github/workflows/       # GitHub Actions (job lifecycle)
├── logs/                    # Job logs
├── setup/                   # Setup wizard
├── INITIAL.md               # Simple intake template for system requests
└── CLAUDE.md                # Full operating instructions for AI assistants
```

---

## Docs

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Complete operating instructions (agent architecture + factory) |
| [Architecture](docs/ARCHITECTURE.md) | Two-layer design, file structure, API endpoints |
| [Configuration](docs/CONFIGURATION.md) | Environment variables, GitHub secrets, repo variables |
| [Customization](docs/CUSTOMIZATION.md) | Personality, skills, operating system files |
| [Auto-Merge](docs/AUTO_MERGE.md) | Auto-merge controls, ALLOWED_PATHS configuration |
| [Factory Workflow](factory/workflow.md) | The factory's build process |
| [Pattern Library](library/patterns.md) | Proven workflow patterns |
| [Tool Catalog](library/tool_catalog.md) | Reusable tool patterns |

---

## Factory Capabilities

### Build from Prompt
Describe a problem on Telegram. The bot generates a PRP (spec), builds the system, tests it, and delivers a complete package.

### PRP Workflow
Two-step process: `/generate-prp` creates a detailed specification, `/execute-prp` builds the system from it. The PRP catches ambiguity before code generation starts.

### Pattern Library
The factory learns from every build. Proven patterns (Scrape > Process > Output, Monitor > Detect > Alert, etc.) are cataloged and reused.

### n8n Conversion
Paste an n8n workflow JSON. The factory translates it into a WAT system that runs on GitHub Actions.

### Self-Improvement
After every build, the factory updates its pattern library and tool catalog.

---

## Security

- API keys live in GitHub Secrets -- never in code
- The `env-sanitizer` extension prevents the LLM from accessing protected credentials
- All changes go through PRs with auto-merge path controls
- Everything is versioned in Git -- rollback is always possible

---

*Built with thepopebot + WAT Systems Factory*
