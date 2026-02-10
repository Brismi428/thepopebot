# GitHub Configuration & Conventions

GitHub is the runtime, distribution, and versioning backbone for all WAT systems. This document defines the conventions and patterns used across the factory and all generated systems.

---

## GitHub Actions Workflow Structure

Every WAT system's GitHub Actions workflow follows this structure:

```yaml
name: "system-name — WAT System"

on:
  # At least one trigger is required
  workflow_dispatch:    # Manual trigger with inputs
  schedule:            # Cron-based recurring
  repository_dispatch: # API/webhook trigger

permissions:
  contents: write      # To commit results back
  issues: write        # For failure notifications
  pull-requests: write # For Agent HQ PR creation

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 15  # REQUIRED — always set a timeout

    steps:
      - uses: actions/checkout@v4        # Pin versions, never @latest
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - name: Execute via Claude Code
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          # ... other secrets
        run: npx @anthropic-ai/claude-code --print "..."
      - name: Commit results
        run: git add ... && git commit ... && git push
      - name: Notify on failure
        if: failure()
        run: gh issue create ...
```

### Rules
- Always pin action versions (`@v4`, `@v5`) — never use `@latest`
- Always set `timeout-minutes` on every job
- Always include a failure notification step
- Always validate required secrets before execution
- Always use `--print` flag with Claude Code for non-interactive execution

---

## Secret Naming Conventions

All secrets follow these rules:

| Convention | Example | Notes |
|-----------|---------|-------|
| UPPERCASE | `FIRECRAWL_API_KEY` | Always uppercase |
| UNDERSCORED | `BRAVE_SEARCH_API_KEY` | Underscores between words |
| DESCRIPTIVE | `SUPABASE_URL` | Name indicates the service and type |
| SUFFIXED | `_API_KEY`, `_TOKEN`, `_URL`, `_SECRET` | Common suffixes by type |

### Standard Secret Names

| Secret | Purpose | Used By |
|--------|---------|---------|
| `ANTHROPIC_API_KEY` | Claude Code execution | All systems |
| `GITHUB_TOKEN` | GitHub API (auto-provided in Actions) | All systems |
| `GITHUB_PAT` | GitHub API (cross-repo, elevated permissions) | Systems that manage other repos |
| `FIRECRAWL_API_KEY` | Firecrawl web scraping | Web scraping systems |
| `BRAVE_SEARCH_API_KEY` | Brave Search API | Research/search systems |
| `OPENAI_API_KEY` | OpenAI API | AI processing systems |
| `SUPABASE_URL` | Supabase project URL | Database systems |
| `SUPABASE_KEY` | Supabase anon/service key | Database systems |
| `SLACK_WEBHOOK_URL` | Slack notifications | Notification systems |
| `SLACK_BOT_TOKEN` | Slack Bot API | Slack integration systems |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API | Telegram systems |
| `AIRTABLE_API_KEY` | Airtable API | Airtable systems |
| `NOTION_API_KEY` | Notion API | Notion systems |
| `STRIPE_API_KEY` | Stripe API | Payment systems |
| `GOOGLE_CREDENTIALS` | Google APIs (JSON blob) | Google service systems |

### How Secrets Flow
1. User adds secrets in GitHub repo **Settings > Secrets and variables > Actions**
2. GitHub Actions injects them as environment variables: `${{ secrets.SECRET_NAME }}`
3. Python tools access them via `os.environ["SECRET_NAME"]`
4. Nothing is ever written to files or logs

---

## Branch Strategy

| Branch | Purpose | Protection |
|--------|---------|-----------|
| `main` | Stable, production-ready factory and systems | Protected — requires PR review |
| `system/{name}` | New WAT system being built | Created by factory dispatch, merged via PR |
| `improve/{date}-cycle` | Self-improvement updates | Created by self-improve workflow, merged via PR |
| `agent-hq/issue-{N}` | Agent HQ task results | Created by agent_hq workflow, merged via PR |

### Rules
- Never commit directly to `main` — always use PRs
- Feature branches are automatically created by GitHub Actions workflows
- Branch names use lowercase-with-dashes
- Branches are prefixed by their purpose (`system/`, `improve/`, `agent-hq/`)

---

## Trigger Patterns

### workflow_dispatch — Manual Trigger with Inputs

Use when: Users need to trigger on-demand with parameters.

```yaml
on:
  workflow_dispatch:
    inputs:
      param_name:
        description: "Description of the parameter"
        required: true
        type: string  # string, boolean, choice, environment
```

Access in steps: `${{ github.event.inputs.param_name }}`

### schedule — Cron-Based Recurring

Use when: Systems need to run on a regular schedule.

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"  # Every Monday at 9 AM UTC
```

Common cron patterns:
| Schedule | Cron | Notes |
|----------|------|-------|
| Every hour | `0 * * * *` | |
| Daily at midnight | `0 0 * * *` | UTC |
| Weekly Monday 9 AM | `0 9 * * 1` | UTC |
| Monthly 1st | `0 0 1 * *` | First of month |
| Every 6 hours | `0 */6 * * *` | |

### repository_dispatch — API/Webhook Trigger

Use when: External systems (n8n, Zapier, custom scripts) need to trigger the workflow.

```yaml
on:
  repository_dispatch:
    types: [system-name-run]
```

Trigger via API:
```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{"event_type": "system-name-run", "client_payload": {"task_input": "..."}}'
```

Access payload: `${{ github.event.client_payload.task_input }}`

### n8n as External Trigger

To trigger a WAT system from n8n:
1. Use n8n's **HTTP Request** node
2. Method: POST
3. URL: `https://api.github.com/repos/OWNER/REPO/dispatches`
4. Headers: `Authorization: Bearer {PAT}`, `Accept: application/vnd.github.v3+json`
5. Body: `{"event_type": "system-name-run", "client_payload": {"task_input": "..."}}`

---

## Committing Results Back

Systems commit their output back to the repo using this pattern:

```bash
git config user.name "WAT System: system-name"
git config user.email "wat-system@users.noreply.github.com"
git add output/
if git diff --cached --quiet; then
  echo "No changes to commit"
else
  git commit -m "run: system-name results $(date +%Y-%m-%d_%H%M)"
  git push
fi
```

### Rules
- Use `GITHUB_TOKEN` for commits within the same repo (auto-provided by Actions)
- Use a `GITHUB_PAT` for cross-repo commits or elevated permissions
- Always check if there are changes before committing (avoid empty commits)
- Use descriptive commit messages with the system name and timestamp
- Git user name should identify the system (e.g., "WAT System: company-profiler")

---

## GitHub Agent HQ Integration

GitHub Agent HQ allows Claude to operate as a native agent inside repositories.

### How It Works
1. A user creates an issue or mentions `@claude` in a comment
2. GitHub triggers the `agent_hq.yml` workflow
3. Claude Code runs inside the Actions container, reads the issue/comment, and executes
4. Results are committed and a draft PR is opened
5. Reviewers can iterate by commenting with `@claude`

### Requirements
- `CLAUDE.md` at repo root — Agent HQ uses this for context
- `agent_hq.yml` workflow responding to `issues` and `issue_comment` events
- Issue body must be structured enough for the agent to parse as input
- Output must go into reviewable PRs, not just logs

### Issue Format Convention
```markdown
## Task
{Description of what to do}

## Input
{Specific parameters, URLs, data}

## Expected Output
{What the result should look like}
```
