# RSS Digest Monitor

Daily email digest system that monitors multiple RSS/Atom feeds, tracks new posts since the last run, and delivers formatted HTML summaries via SMTP. Runs autonomously on GitHub Actions with Git-persisted state.

## System Overview

- **Type**: WAT System (Workflow, Agent, Tools)
- **Purpose**: Automated daily RSS monitoring with email digest delivery
- **Pattern**: Monitor > Collect > Transform > Deliver (with state persistence)

## Execution

This system can be run three ways:

1. **Claude Code CLI**: Run `workflow.md` directly in the terminal with environment variables
2. **GitHub Actions**: Scheduled daily at 8 AM UTC, or manual dispatch via Actions UI
3. **GitHub Agent HQ**: Assign an issue to @claude with task input in the body (for modifications/troubleshooting)

## Inputs

- **config/feeds.json** (JSON): List of RSS/Atom feed URLs with display names and tags
  ```json
  {
    "feeds": [
      {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "tags": ["tech"]},
      {"name": "GitHub Blog", "url": "https://github.blog/feed/", "tags": ["dev"]}
    ]
  }
  ```

- **state/rss_state.json** (JSON, auto-created): Tracks last run timestamp and seen post GUIDs
  ```json
  {
    "last_run": "2026-02-11T08:00:00Z",
    "seen_guids": ["feed_url::post_guid", ...]
  }
  ```

- **Environment Variables**:
  - `SMTP_HOST`: SMTP server hostname (e.g., smtp.gmail.com)
  - `SMTP_PORT`: SMTP port (587 for TLS)
  - `SMTP_USER`: SMTP authentication username
  - `SMTP_PASS`: SMTP authentication password (use App Password for Gmail)
  - `SMTP_FROM`: From address (e.g., "RSS Digest <notify@example.com>")
  - `SMTP_TO`: Comma-separated recipient email addresses

## Outputs

- **HTML Email Digest**: Sent via SMTP to configured recipients. Includes posts grouped by feed, with title (linked), summary, and publish date. Plain-text fallback included.
- **state/rss_state.json**: Updated state file committed to repository after successful email send
- **logs/YYYY-MM-DD_run.json**: Run summary with feed count, new posts, and email status

## Workflow

Follow `workflow.md` for the step-by-step process. Key phases:

1. **Load State** — Read last run timestamp and seen GUIDs, or initialize on first run
2. **Fetch RSS Feeds** — Retrieve and parse multiple feeds with per-feed error handling
3. **Filter New Posts** — Compare against state to identify posts since last run
4. **Generate HTML Digest** — Group by feed, create styled email with plain-text fallback
5. **Send Email via SMTP** — Deliver digest with retry logic and TLS authentication
6. **Update State** — Persist new timestamp and GUIDs to repository (only if email succeeds)
7. **Commit State** — Push updated state and run log to Git

## Tools

| Tool | Purpose |
|------|---------|
| `tools/load_state.py` | Loads RSS state (last_run, seen_guids) or initializes empty state on first run |
| `tools/fetch_rss_feeds.py` | Fetches and parses RSS/Atom feeds using feedparser, handles per-feed errors |
| `tools/filter_new_posts.py` | Filters posts by composite GUID and publish date since last run |
| `tools/generate_html_digest.py` | Generates HTML email with plain-text fallback, grouped by feed |
| `tools/send_email_smtp.py` | Sends email via SMTP with TLS, includes retry logic for transient failures |
| `tools/save_state.py` | Updates state with new timestamp and GUIDs, enforces 10,000 GUID max |

## Subagents

This system uses specialist subagents defined in `.claude/agents/`. Subagents are the DEFAULT delegation mechanism — when the workflow reaches a phase, delegate to the appropriate subagent.

### Available Subagents

| Subagent | Description | Tools | When to Use |
|----------|-------------|-------|-------------|
| `rss-fetcher-specialist` | Fetches and parses RSS/Atom feeds from URLs. Handles HTTP errors, feed parsing, and data normalization. | Read, Bash | Delegate when fetching feeds from config/feeds.json. Handles per-feed failures gracefully. |
| `digest-generator-specialist` | Formats new posts into HTML email digest. Handles grouping, HTML generation, and plain-text fallback. | Read, Write | Delegate when generating email from filtered posts. Returns MIME multipart email object. |
| `state-manager-specialist` | Manages RSS monitoring state. Handles loading, filtering, and saving state with GUID tracking and timestamp management. | Read, Write, Bash | Delegate for state loading (Step 1), post filtering (Step 3), and state saving (Step 6). |

### How to Delegate

Subagents are invoked automatically based on their `description` field or explicitly:
```
Use the rss-fetcher-specialist subagent to fetch all RSS feeds from config/feeds.json
```

### Subagent Chaining

This workflow chains subagents sequentially:

1. **state-manager-specialist** loads state → produces state object
2. **rss-fetcher-specialist** fetches feeds → produces feed results
3. **state-manager-specialist** filters new posts → produces new_posts + new_guids
4. **digest-generator-specialist** generates email → produces MIME email file
5. Main agent sends email → produces send status
6. **state-manager-specialist** updates state → persists to file

The main agent coordinates this chain, reading outputs and delegating to the next subagent.

### Delegation Hierarchy

- **Subagents are the default** for all task delegation. Use them for every workflow phase.
- **Agent Teams is NOT used** in this system. Sequential execution is correct because each step depends on the previous step's output.
- This workflow has clear sequential dependencies: state → fetch → filter → generate → send → update.

## MCP Dependencies

This system uses the following libraries. No MCPs are required, though filesystem MCP can optionally be used for file I/O.

| Capability | Primary | Alternative | Fallback |
|-----------|---------|-------------|----------|
| RSS/Atom feed parsing | `feedparser` (Python library) | None | Direct XML parsing (not recommended) |
| Email delivery | `smtplib` (Python stdlib) | None | N/A |
| State persistence | `json` + `pathlib` (Python stdlib) | `@anthropic/filesystem-mcp` | N/A |

**Important**: This system uses standard Python libraries, not MCPs. It works out-of-the-box with only Python and the dependencies in `requirements.txt`.

## Required Secrets

These must be set as GitHub Secrets (for Actions) or environment variables (for CLI):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Code execution | Yes (for Claude Code) |
| `SMTP_HOST` | SMTP server hostname | Yes |
| `SMTP_PORT` | SMTP server port | Yes |
| `SMTP_USER` | SMTP authentication username | Yes |
| `SMTP_PASS` | SMTP authentication password | Yes |
| `SMTP_FROM` | From address for digest emails | Yes |
| `SMTP_TO` | Comma-separated recipient addresses | Yes |

## Agent Teams

**This system does NOT use Agent Teams.** The workflow has sequential dependencies — each step requires the previous step's output. Agent Teams would add complexity and cost without reducing wall-clock time.

For example:
- Filter new posts DEPENDS ON fetched feeds
- Generate digest DEPENDS ON filtered posts
- Update state DEPENDS ON successful email send

**Sequential execution is the correct design.**

## Failure Handling

| Failure Scenario | Behavior |
|------------------|----------|
| Single feed unreachable | Log error, continue with other feeds. One feed failure does NOT kill the run. |
| State file corrupted | Initialize empty state, log warning, process all posts (may duplicate once). |
| No new posts | Silent run — update state, skip email send. This is expected behavior. |
| SMTP authentication fails | Retry once with 30s delay. If fails again, exit non-zero. Do NOT update state. |
| Email send fails | Exit non-zero. Do NOT update state. Posts retry on next run. |
| State write fails | Exit non-zero, log error. State not committed. Posts retry on next run. |
| Git push fails | Log error, exit 0. State saved locally, will sync on next run. |

**Critical Rule:** Never update state before email is successfully sent. If email fails, posts MUST retry on the next run.

## Setup

### 1. Configure Feeds

Create or edit `config/feeds.json` with your feed list:
```json
{
  "feeds": [
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "tags": ["tech", "news"]},
    {"name": "GitHub Blog", "url": "https://github.blog/feed/", "tags": ["dev", "github"]},
    {"name": "Python Insider", "url": "https://blog.python.org/feeds/posts/default", "tags": ["python"]}
  ]
}
```

### 2. Set Secrets

For GitHub Actions:
1. Go to repository Settings → Secrets and variables → Actions
2. Add the required secrets listed above

For CLI:
1. Create a `.env` file (see `.env.example`)
2. Export variables: `export $(cat .env | xargs)`

### 3. Run

**GitHub Actions (recommended):**
- Scheduled: Runs daily at 8 AM UTC automatically
- Manual: Go to Actions → RSS Digest Monitor → Run workflow

**CLI:**
```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASS=your-app-password
export SMTP_FROM="RSS Digest <your-email@gmail.com>"
export SMTP_TO=recipient@example.com

claude workflow.md
```

## Gmail Setup

If using Gmail, you MUST use an App Password, not your account password:

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"
4. Use this 16-character password as `SMTP_PASS`

## Troubleshooting

**No email received:**
- Check spam folder
- Verify SMTP credentials are correct
- Check GitHub Actions logs for send status
- Look for "Email sent successfully" in logs

**Duplicate posts in digest:**
- State file may be corrupted or not committing
- Check `state/rss_state.json` exists and has `seen_guids`
- Verify Git commits are pushing (check repository commits)

**Feed not updating:**
- Check if feed URL is correct
- Look for feed errors in `logs/YYYY-MM-DD_run.json`
- Failed feeds are logged but don't stop the run

**State file growing too large:**
- Default maximum is 10,000 GUIDs
- Current size shown in logs: "state file size: X KB"
- Consider reducing max if file exceeds 500 KB

## Monitoring

Check run status:
- **GitHub Actions**: View workflow runs in Actions tab
- **Logs**: Review `logs/YYYY-MM-DD_run.json` for summaries
- **State**: Inspect `state/rss_state.json` for GUID count and last_run

Run summary JSON:
```json
{
  "timestamp": "2026-02-11T08:05:23Z",
  "feeds_checked": 5,
  "feeds_failed": 1,
  "new_posts": 12,
  "email_sent": true,
  "failed_feeds": ["https://broken-feed.example/rss"]
}
```

## Customization

**Change schedule:** Edit `.github/workflows/monitor.yml` cron expression

**Change email style:** Edit `tools/generate_html_digest.py` HTML template

**Change GUID limit:** Pass `max_guids` argument to `save_state.py` (default: 10000)

**Add more feeds:** Edit `config/feeds.json` and commit

## Success Criteria

- [ ] System fetches multiple RSS/Atom feeds without failing if one is down
- [ ] New posts correctly identified by comparing against state file
- [ ] Email digest sent via SMTP with HTML formatting, grouped by feed
- [ ] Each digest entry includes: feed name, title (linked), summary, date
- [ ] State file updated and committed after successful email send
- [ ] System runs autonomously via GitHub Actions daily at 8 AM UTC
- [ ] If no new posts, no email sent (silent run with state update)
- [ ] All three execution paths work: CLI, GitHub Actions, manual dispatch
