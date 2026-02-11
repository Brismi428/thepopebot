# RSS Digest Monitor

Daily email digest system that monitors multiple RSS/Atom feeds, tracks new posts, and delivers formatted HTML summaries via SMTP. Runs autonomously on GitHub Actions with Git-persisted state.

## Features

- ✅ **Multi-feed monitoring** — Track any number of RSS/Atom feeds
- ✅ **Stateful deduplication** — Never sends the same post twice
- ✅ **HTML email digest** — Beautiful, grouped by feed, with plain-text fallback
- ✅ **Graceful failure handling** — One broken feed doesn't stop the whole run
- ✅ **Zero infrastructure** — Runs on GitHub Actions, state in Git
- ✅ **Daily schedule** — Automatic delivery at 8 AM UTC
- ✅ **Manual trigger** — On-demand digests via GitHub Actions UI

## Quick Start

### 1. Clone or Copy This System

```bash
git clone <your-repo-url>
cd rss-digest-monitor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Your Feeds

Edit `config/feeds.json`:

```json
{
  "feeds": [
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "tags": ["tech"]},
    {"name": "GitHub Blog", "url": "https://github.blog/feed/", "tags": ["dev"]}
  ]
}
```

### 4. Set Up SMTP (Gmail Example)

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"
4. Set GitHub Secrets (Settings → Secrets and variables → Actions):
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `your-email@gmail.com`
   - `SMTP_PASS` = `your-16-char-app-password`
   - `SMTP_FROM` = `RSS Digest <your-email@gmail.com>`
   - `SMTP_TO` = `recipient@example.com`

### 5. Run

**Scheduled (Automatic):**
- Commits to `main` activate the workflow
- Runs daily at 8:00 AM UTC
- Check Actions tab for run history

**Manual:**
- Go to Actions → RSS Digest Monitor → Run workflow
- Optional: Enable "force_send" to test email even if no new posts

## Execution Paths

This system supports three ways to run:

### 1. GitHub Actions (Recommended)

Scheduled or manual execution via `.github/workflows/monitor.yml`:

- **Daily at 8 AM UTC** (automatic)
- **Manual dispatch** via Actions UI
- **Commits state** back to repository
- **Zero local setup** required

### 2. Claude Code CLI

Run the workflow directly from the terminal:

```bash
# Set environment variables (or use .env file)
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASS=your-app-password
export SMTP_FROM="RSS Digest <your-email@gmail.com>"
export SMTP_TO=recipient@example.com

# Execute workflow
claude workflow.md
```

### 3. GitHub Agent HQ

Assign an issue to @claude for system modifications or troubleshooting:

```
@claude Debug why the GitHub Blog feed is failing in the last 3 runs
```

See `CLAUDE.md` for complete Claude Code instructions.

## How It Works

1. **Load State** — Reads last run timestamp and seen post GUIDs from `state/rss_state.json`
2. **Fetch Feeds** — Retrieves all feeds from `config/feeds.json`, handles per-feed errors
3. **Filter New Posts** — Compares posts against state (GUID + timestamp filtering)
4. **Generate Digest** — Groups posts by feed, creates HTML email with plain-text fallback
5. **Send Email** — Delivers digest via SMTP with TLS and retry logic
6. **Update State** — Persists new timestamp and GUIDs (only if email succeeds)
7. **Commit State** — Pushes updated state and run log to Git

**Key Design:** State is ONLY updated after successful email send. If email fails, posts retry on the next run. This prevents losing track of posts during transient failures.

## File Structure

```
rss-digest-monitor/
├── .claude/
│   └── agents/              # Specialist subagent definitions
├── .github/
│   └── workflows/
│       └── monitor.yml      # GitHub Actions workflow (daily cron)
├── config/
│   └── feeds.json           # RSS feed list (edit this!)
├── logs/
│   └── YYYY-MM-DD_run.json  # Run summaries (auto-generated)
├── state/
│   └── rss_state.json       # Persistent state (auto-generated)
├── tools/
│   ├── load_state.py        # State loading
│   ├── fetch_rss_feeds.py   # RSS fetching and parsing
│   ├── filter_new_posts.py  # Deduplication
│   ├── generate_html_digest.py  # HTML email generation
│   ├── send_email_smtp.py   # SMTP delivery
│   └── save_state.py        # State persistence
├── CLAUDE.md                # Claude Code operating instructions
├── workflow.md              # Workflow definition
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md                # This file
```

## Configuration

### Adding Feeds

Edit `config/feeds.json`:

```json
{
  "feeds": [
    {
      "name": "Display Name",
      "url": "https://example.com/rss",
      "tags": ["category1", "category2"]
    }
  ]
}
```

Commit and push. The next run will include the new feed.

### Changing Schedule

Edit `.github/workflows/monitor.yml` cron expression:

```yaml
schedule:
  - cron: '0 8 * * *'  # Daily at 8:00 AM UTC
```

Examples:
- Every 6 hours: `0 */6 * * *`
- Weekdays only: `0 8 * * 1-5`
- Twice daily: `0 8,20 * * *`

### Customizing Email Style

Edit the HTML template in `tools/generate_html_digest.py`. The template uses inline CSS for maximum email client compatibility.

## Troubleshooting

### No email received

1. Check spam/junk folder
2. Verify SMTP secrets are set correctly in GitHub
3. Check GitHub Actions logs for "Email sent successfully"
4. Test with manual dispatch + force_send enabled

### Duplicate posts in digest

- State file may not be committing properly
- Check `state/rss_state.json` exists and has recent `last_run`
- Verify Git commits are pushing (check repository commit history)

### Feed not updating

- Check feed URL in `config/feeds.json` is correct
- View `logs/YYYY-MM-DD_run.json` for per-feed errors
- Some feeds may be rate-limited or temporarily down (this is expected)

### State file growing too large

- Default maximum: 10,000 GUIDs
- Current size logged in each run: "state file size: X KB"
- Reduce max by passing `--max-guids 5000` to `save_state.py`

## Monitoring

**Check run status:**
- GitHub Actions → Workflow runs (green = success, red = failure)
- `logs/YYYY-MM-DD_run.json` — Detailed run summaries
- `state/rss_state.json` — Current GUID count and last_run timestamp

**Run summary example:**
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

## SMTP Providers

### Gmail

**Setup:**
1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use `smtp.gmail.com:587` with TLS

### Outlook / Office 365

**Setup:**
1. Use `smtp.office365.com:587`
2. Enable "authenticated SMTP" in account settings
3. Use your full email as username

### Custom SMTP

Any SMTP server with TLS support works:
- Set `SMTP_HOST` and `SMTP_PORT`
- Provide valid credentials
- Ensure TLS is enabled on port 587 or 465

## Cost

- **GitHub Actions**: Free tier includes 2,000 minutes/month (private repos) or unlimited (public repos)
- **This workflow**: ~3-5 minutes per day = ~90-150 minutes/month
- **Storage**: Minimal (state file + logs under 1 MB)
- **Email**: Uses your existing SMTP account (Gmail, etc.)

**Result:** Effectively free for most users.

## Security

- SMTP credentials stored as GitHub Secrets (encrypted at rest)
- `.env` file excluded from Git via `.gitignore`
- State file contains only public post GUIDs (no sensitive data)
- TLS encryption for SMTP connections
- No API keys or tokens exposed in logs

## Development

### Local Testing

1. Copy `.env.example` to `.env` and fill in values
2. Export variables: `export $(cat .env | xargs)`
3. Run individual tools:
   ```bash
   python tools/load_state.py state/rss_state.json
   python tools/fetch_rss_feeds.py config/feeds.json
   ```
4. Or run full workflow: `claude workflow.md`

### Adding New Features

1. Edit the tool (e.g., `tools/generate_html_digest.py`)
2. Update `CLAUDE.md` if the workflow changes
3. Test locally with `.env` file
4. Commit and push
5. Manual dispatch to test on GitHub Actions

## Credits

Built using the **WAT Systems Factory** — a meta-system for generating GitHub-native autonomous agent systems from natural language descriptions.

**Pattern**: Monitor > Collect > Transform > Deliver (with state persistence)

## License

[Your License Here]
