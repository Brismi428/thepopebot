# WAT Systems Factory — Quick Reference

## What This Is

The WAT Systems Factory is a meta-system that builds complete, deployable AI agent systems. Given a problem description, it generates everything needed to run autonomously: Python tools, workflow definitions, subagent configurations, GitHub Actions, and documentation.

Every system runs on GitHub — no cloud infrastructure needed. Systems execute via GitHub Actions (cron, manual trigger, or webhook) and use Git as their persistence layer.

## Build Pipeline Overview

```
User describes problem
  → PRP generated (Product Requirements Prompt)
  → Confidence scored (1-10)
  → If >= 8: auto-build
  → If < 8: clarify ambiguity flags, then build
  → Complete system in systems/{name}/
  → 3-level validation (syntax, unit, integration)
```

## Generated System Structure

Every system the factory builds contains:

| File/Dir | Purpose |
|----------|---------|
| `CLAUDE.md` | Operating instructions the agent follows at runtime |
| `workflow.md` | Step-by-step process definition |
| `tools/` | Python tool files (each is a standalone script) |
| `.claude/agents/` | Specialist subagent definitions (YAML frontmatter + system prompt) |
| `.github/workflows/` | GitHub Actions for automated execution |
| `requirements.txt` | Python dependencies |
| `README.md` | Setup guide covering all 3 execution paths |
| `.env.example` | Required environment variables (secrets template) |
| `.gitignore` | Standard exclusions |
| `VALIDATION.md` | Test results from 3-level validation |

## The 14 Workflow Patterns (Summary)

| # | Pattern | Use When |
|---|---------|----------|
| 1 | Scrape > Process > Output | Pulling structured data from websites |
| 2 | Research > Analyze > Report | Multi-source research synthesis |
| 3 | Monitor > Detect > Alert | Watching for changes over time |
| 4 | Intake > Enrich > Deliver | Augmenting incoming data with external sources |
| 5 | Generate > Review > Publish | AI content creation with quality gates |
| 6 | Listen > Decide > Act | Event-driven reactions to webhooks/triggers |
| 7 | Collect > Transform > Store | ETL pipelines using Git as data store |
| 8 | Fan-Out > Process > Merge | Parallel decomposition of independent tasks |
| 9 | Issue > Execute > PR | GitHub issue-driven task queue |
| 10 | n8n Import > Translate > Deploy | Converting n8n workflows to WAT systems |
| 11 | Content Transformation with Tone Matching | Rewriting content to match brand voice |
| 12 | Sequential State Management | Pipelines with persistent state between runs |
| 13 | Multi-Source Weekly Monitor | Tracking changes across sources with diffs |
| 14 | Multi-Stage Content Generation | Content pipelines with review scoring and auto-publish |

Patterns are composable. A system can combine multiple patterns.

## Subagent Architecture

Every system uses specialist subagents as the DEFAULT delegation mechanism. The main agent delegates phases to subagents; subagents do NOT call other subagents.

Typical subagent count: 3-6 per system.

Common specialist roles:
- **search-specialist** — web discovery, data collection
- **scrape-specialist** — content extraction from URLs
- **content-validator-specialist** — pre-publish validation
- **publisher-specialist** — platform API operations with retry
- **fallback-handler-specialist** — error classification and recovery
- **report-generator-specialist** — aggregate results into reports
- **reviewer-specialist** — multi-dimensional quality scoring

## Agent Teams (Parallelization)

Agent Teams is for parallelization ONLY, not delegation. Use when:
- 3+ truly independent tasks exist (no data dependencies between them)
- Tasks are identical in structure (e.g., process 7 posts independently)
- Speedup matters (typically 2-7x wall-time improvement, same token cost)

Do NOT use Agent Teams for:
- Tasks with fewer than 3 items
- Tasks that depend on each other
- Delegation to specialists (use subagents instead)

## Three Execution Paths (All Mandatory)

Every system must support all three:

1. **CLI** — Run locally for development/testing
2. **GitHub Actions** — Automated via cron, manual trigger, or webhook
3. **Agent HQ** — Issue-driven execution (create GitHub issue → system runs)

## Key Rules

- System names: `lowercase-with-dashes`
- Secrets: NEVER hardcoded, always referenced by env var name
- Every MCP integration must have an HTTP/API fallback
- Git discipline: NEVER use `git add -A` or `git add .` — always specific paths
- Tools must handle their own retries internally
- All tools must be unattended (no interactive input)

## Real Systems Built (Examples)

| System | Pattern | What It Does |
|--------|---------|-------------|
| lead-gen-machine | Intake > Enrich > Deliver | B2B lead enrichment via Apollo, Hunter, Brave |
| competitor-monitor | Monitor > Detect > Alert | Weekly competitor tracking with snapshot diffs |
| content-repurposer | Content Transformation | Blog-to-social media content with tone matching |
| instagram-publisher | Generate > Review > Publish | Instagram queue processor with 2-step Graph API |
| weekly-instagram-content-publisher | Multi-Stage Content Gen | Weekly content packs with quality gates and auto-publish |
| invoice-generator | Sequential State Management | Auto-incrementing invoices with PDF generation |
| rss-digest-monitor | Monitor > Detect > Alert | RSS feed tracking with email delivery |
| csv-to-json-converter | Collect > Transform > Store | ETL with type inference and schema detection |
| marketing-pipeline | Intake > Enrich > Deliver | Multi-API lead enrichment pipeline |
| website-uptime-checker | Monitor > Detect > Alert | HTTP health monitoring with alerting |

## Capabilities and Limitations

**CAN do:**
- Build complete autonomous systems running on GitHub Actions
- Generate Python tools, workflows, subagents, GitHub Actions
- Use any REST API via Python
- Convert n8n workflows to WAT systems
- Parallel execution via Agent Teams (3+ independent tasks)
- Self-improve from every build (updates patterns and tool catalog)

**CANNOT do:**
- Frontend UIs or web apps
- Mobile apps
- Direct cloud deployment (AWS/GCP/Azure) — deploys to GitHub
- Real-time streaming — batch/scheduled/event-driven only
- Replace databases — uses Git or integrates with external DBs
- Run continuously — trigger-based only
