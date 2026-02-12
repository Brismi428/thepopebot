# Onboard: WAT Factory Bot Project Orientation

Use this skill when a new Claude Code session needs a quick orientation of the WAT Factory Bot project. It produces a concise project status report covering the codebase rules, built systems, learned patterns, PRPs, infrastructure state, and recent job activity.

## Instructions

When this skill is invoked, perform the following steps and output a single, concise **Project Status Report**.

### Step 1: Project Rules (from CLAUDE.md)

Read `CLAUDE.md` at the repo root. Summarize the key rules in a compact list:

- **Architecture**: Two-layer system (Event Handler + Docker Agent). Do NOT modify `event_handler/`, `.github/workflows/`, `entrypoint.sh`, or `Dockerfile`.
- **Git rules**: Only commit files you changed. Always `git add <specific-files>` -- never `git add -A` or `git add .`. Never use destructive git commands.
- **WAT Framework**: Every system = Workflows (.md) + Agents (Claude Code) + Tools (.py). Systems live in `systems/`. PRPs live in `PRPs/`.
- **Factory workflow**: Intake > Research > Design > Generate > Test > Package > Learn. Use `/generate-prp` then `/execute-prp`.
- **Subagents**: Default delegation mechanism. One per domain. No cross-subagent calls. Defined in `.claude/agents/`.
- **Agent Teams**: Only when 3+ independent tasks exist. Always provide sequential fallback.
- **Style**: No emojis. No fluff. Technical prose only. Code comments explain why, not what.

### Step 2: Systems Inventory

List all directories under `systems/` by reading each system's `CLAUDE.md` (first few lines). Present as a table:

| System | Description | Has PRP | Factory-Built |
|--------|-------------|---------|---------------|
| company-profiler | Scrapes company URLs, extracts business info, outputs structured JSON profiles | No | No (pre-factory) |
| lead-gen-machine | Automated lead gen: find, scrape, score, rank companies matching ICP, output CSV | No | No (pre-factory) |
| marketing-pipeline | Lead enrichment + scoring + segmentation + outreach generation via Apollo/Hunter/Brave | No | No (pre-factory) |
| website-uptime-monitor | Lightweight Git-native uptime monitor, logs status to CSV on schedule | Yes | Yes |
| csv-to-json-converter | Multi-phase CSV to JSON/JSONL conversion with type inference and validation | Yes | Yes |
| rss-digest-monitor | Daily RSS/Atom feed monitor with HTML email digests and Git-persisted state | Yes | Yes |
| content-repurposer | Multi-channel content repurposing: blog posts to Twitter/LinkedIn/email/Instagram | Yes | Yes |
| invoice-generator | JSON to professional PDF invoices with sequential numbering and tax calculation | Yes | Yes |
| competitor-monitor | Weekly competitor website monitoring with change detection and digest reports | Yes | Yes |

**Note**: If new systems have been added since this skill was written, list them by reading their `CLAUDE.md` files. Run `ls systems/` to check.

### Step 3: Learned Patterns & Tool Catalog

Read `library/patterns.md` and `library/tool_catalog.md`. Summarize what has been learned:

**Workflow Patterns** (from `library/patterns.md`):
List the numbered pattern names and one-line summaries. As of last update:

1. Scrape > Process > Output -- Web scraping pipeline
2. Research > Analyze > Report -- Multi-source research synthesis
3. Monitor > Detect > Alert -- Periodic change detection with alerts
4. Intake > Enrich > Deliver -- Data enrichment pipeline
5. Generate > Review > Publish -- Content generation with quality gates
6. Listen > Decide > Act -- Event-driven agent
7. Collect > Transform > Store -- ETL with Git as data store
8. Fan-Out > Process > Merge -- Agent Teams parallelization
9. Issue > Execute > PR -- GitHub Agent HQ task queue
10. n8n Import > Translate > Deploy -- n8n workflow migration
11. Content Transformation with Tone Matching -- Multi-platform content repurposing
12. Sequential State Management Pipeline -- Atomic state persistence across runs
13. Multi-Source Weekly Monitor with Snapshot Comparison -- Scheduled multi-site monitoring

Also list the **Proven Compositions** section (patterns learned from actual builds).

**Tool Catalog** (from `library/tool_catalog.md`):
List the category headers. As of last update (v0.1.0-seed):
Web Scraping & Search, File I/O, API Calls, Data Processing, AI Processing, Notifications, Git Operations, GitHub API, Database Operations, Media Processing, n8n Conversion, Agent Teams Coordination, GitHub Agent HQ Interaction.

**Note**: Read the actual files to report current state -- patterns and tools may have been added since this skill was written.

### Step 4: PRP Status

List all `.md` files in `PRPs/` (excluding `templates/`). For each, note whether a matching system exists in `systems/`:

| PRP | Matching System | Status |
|-----|----------------|--------|
| website-uptime-monitor.md | systems/website-uptime-monitor/ | Built |
| csv-to-json-converter.md | systems/csv-to-json-converter/ | Built |
| rss-digest-monitor.md | systems/rss-digest-monitor/ | Built |
| content-repurposer.md | systems/content-repurposer/ | Built |
| invoice-generator.md | systems/invoice-generator/ | Built |
| competitor-monitor.md | systems/competitor-monitor/ | Built |

**Note**: Run `ls PRPs/*.md` and `ls systems/` to get current state. New PRPs may exist without matching systems (status: Pending Build) or new systems may exist without PRPs (status: Pre-factory).

### Step 5: Infrastructure State

Report on the GitHub and deployment configuration:

- **Repository**: Check `git remote -v` for the repo URL.
- **Current branch**: Run `git branch --show-current`.
- **Recent commits**: Run `git log --oneline -10` to show last 10 commits.
- **GitHub Actions workflows**: List files in `.github/workflows/` -- these are immutable (do not modify).
- **Cron jobs**: Read `operating_system/CRONS.json` and list enabled/disabled jobs.
- **Webhook triggers**: Read `operating_system/TRIGGERS.json` and list configured triggers.
- **Docker image**: Note the Dockerfile exists and is immutable. Check if `IMAGE_URL` is referenced in workflows.

### Step 6: Recent Job Activity

List the 5 most recent job directories in `logs/` (sorted by modification time). For each, read `job.md` to show what the agent was tasked with:

| Job ID | Task Summary |
|--------|-------------|
| (uuid) | (first line of job.md) |

If `SUMMARY.md` exists in the job directory, include a one-line outcome.

### Output Format

Combine all steps into a single report with clear section headers:

```
## WAT Factory Bot -- Project Status Report

### Rules Quick Reference
(compact bullet list from Step 1)

### Systems (N total)
(table from Step 2)

### Learned Patterns (N patterns, N tool categories)
(lists from Step 3)

### PRPs (N total)
(table from Step 4)

### Infrastructure
(details from Step 5)

### Recent Jobs (last 5)
(table from Step 6)

### Summary
- N systems built (M factory-built, K pre-factory)
- N PRPs (all built / some pending)
- N workflow patterns learned
- N tool catalog categories
- Last job: (date and brief description)
```

Keep it concise. This report should orient a new session in under 30 seconds of reading.
