# Website Uptime Checker

A GitHub Actions-powered monitoring system that checks website availability every 5 minutes, logs all results to a Git-versioned CSV file, and optionally sends Telegram alerts when sites go down.

## Features

- ✅ **Scheduled monitoring** — Checks sites every 5 minutes via GitHub Actions cron
- ✅ **Git-versioned logging** — All results committed to CSV file with full history
- ✅ **Response time tracking** — Measures and logs response times in milliseconds
- ✅ **Optional Telegram alerts** — Get notified when sites go down
- ✅ **Three execution paths** — Scheduled, manual dispatch, or local CLI
- ✅ **No external dependencies** — Just GitHub, Python stdlib, and `requests` library
- ✅ **Cost-effective** — Free on public repos, minimal cost on private repos

## Quick Start

### 1. Deploy to GitHub

```bash
# Clone this repository to your GitHub account
git clone https://github.com/YOUR_USERNAME/website-uptime-checker.git
cd website-uptime-checker

# Push to your GitHub repository
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Configure URLs to Monitor

Edit `.github/workflows/monitor.yml` and update the URL list:

```yaml
URLS="https://google.com https://github.com https://your-site.com"
```

### 3. (Optional) Configure Telegram Alerts

If you want Telegram notifications when sites go down:

1. **Create a Telegram bot:**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow the prompts
   - Save the bot token (e.g., `110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`)

2. **Get your chat ID:**
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat.id` in the JSON response

3. **Add GitHub Secrets:**
   - Go to your repo **Settings** > **Secrets and variables** > **Actions**
   - Click **New repository secret**
   - Add `TELEGRAM_BOT_TOKEN` with your bot token
   - Add `TELEGRAM_CHAT_ID` with your chat ID

### 4. Enable GitHub Actions

- Go to your repo **Actions** tab
- If prompted, click **"I understand my workflows, go ahead and enable them"**
- The workflow will run every 5 minutes automatically

### 5. View Results

Check the `logs/uptime_log.csv` file in your repository. Each commit adds new monitoring data.

Example:
```csv
timestamp,url,status_code,response_time_ms,is_up
2026-02-13T11:33:00Z,https://google.com,200,145.23,true
2026-02-13T11:33:01Z,https://github.com,200,203.45,true
```

---

## Usage

### Execution Path 1: Scheduled (Primary)

The system runs automatically every 5 minutes via GitHub Actions.

- **Trigger:** GitHub Actions cron schedule
- **Frequency:** Every 5 minutes (±5 minute variance expected)
- **Cost:** ~1,440 minutes/month (free on public repos)

No action required — just let it run!

### Execution Path 2: Manual Dispatch

Trigger a check manually for testing:

**Via GitHub UI:**
1. Go to **Actions** tab
2. Select **"Website Uptime Monitor"** workflow
3. Click **"Run workflow"**
4. Optionally override URLs for testing

**Via GitHub API:**
```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/monitor.yml/dispatches \
  -d '{"ref":"main","inputs":{"urls":"https://example.com"}}'
```

### Execution Path 3: Local CLI (Development)

Run checks locally for development/testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional, for Telegram alerts)
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run monitoring workflow
python tools/monitor.py --urls https://google.com https://github.com > /tmp/results.json
python tools/log_results.py --results /tmp/results.json --log-file logs/uptime_log.csv
python tools/telegram_alert.py --results /tmp/results.json  # Optional

# Commit results
git add logs/uptime_log.csv
git commit -m "chore(uptime): manual check $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git push
```

---

## Configuration

### Change Check Frequency

Edit `.github/workflows/monitor.yml`:

```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes instead of 5
```

**Cron format:** `minute hour day month weekday`

Examples:
- `*/5 * * * *` — Every 5 minutes
- `*/15 * * * *` — Every 15 minutes
- `0 * * * *` — Every hour at :00
- `0 */6 * * *` — Every 6 hours

### Add More URLs

Edit `.github/workflows/monitor.yml`:

```yaml
URLS="https://google.com https://github.com https://example.com https://another-site.com"
```

### Add Authentication

If your site requires authentication, modify `tools/monitor.py`:

```python
# Add argument
parser.add_argument("--auth-header", help="Authorization header value")

# Pass to requests
headers = {}
if args.auth_header:
    headers["Authorization"] = args.auth_header

resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
```

Then update the workflow to pass the secret:

```yaml
python tools/monitor.py \
  --urls $URLS \
  --auth-header "Bearer ${{ secrets.API_TOKEN }}" > /tmp/results.json
```

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│              GitHub Actions (Cron Trigger)              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Step 1: Check Websites (monitoring-specialist)         │
│  → tools/monitor.py                                      │
│  → HTTP GET requests with timeout                       │
│  → Measure response times                               │
│  → Output: /tmp/monitor_results.json                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: Log Results (data-logger-specialist)           │
│  → tools/log_results.py                                 │
│  → Append to logs/uptime_log.csv                        │
│  → Create file with headers if needed                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: Send Alerts (alert-specialist, optional)       │
│  → tools/telegram_alert.py                              │
│  → Filter down sites                                    │
│  → Send Telegram messages                               │
│  → Skip if credentials not configured                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: Commit Results (main agent)                    │
│  → git add logs/uptime_log.csv                          │
│  → git commit with timestamp                            │
│  → git push to origin/main                              │
└─────────────────────────────────────────────────────────┘
```

### Specialist Subagents

This system uses **three specialist subagents** for delegation:

- **monitoring-specialist** — HTTP health checks, response time measurement
- **data-logger-specialist** — CSV file operations, data integrity
- **alert-specialist** — Telegram notifications, graceful error handling

Each subagent has:
- Focused responsibilities
- Minimal tool access (Read, Write, Bash)
- Detailed error handling instructions
- Clear inputs and outputs

See `.claude/agents/` directory for full subagent definitions.

---

## Cost & Performance

### GitHub Actions Minutes

- **Per run:** 1-2 minutes (setup, checks, commit, push)
- **Runs per month:** ~8,640 (288 runs/day × 30 days)
- **Minutes per month:** ~8,640-17,280 minutes

**Free tier limits:**
- **Public repos:** Unlimited minutes
- **Private repos:** 2,000 minutes/month

**If you exceed the free tier (private repos only):**
- Cost: $0.008/minute
- ~$138/month for checks every 5 minutes

**Recommendation for private repos:** Use a longer interval (every 15-30 minutes) to stay within free tier.

### Storage

- **Per check:** ~150 bytes per URL
- **Per month:** ~6.5 MB (2 URLs × 288 checks/day × 30 days)
- **Per year:** ~78 MB

Negligible for Git. No pruning needed.

### Token Cost

**Zero**. This system makes no LLM API calls. Pure monitoring logic.

---

## Troubleshooting

### Sites Always Show as Down

**Symptoms:** All checks report `status_code: 0`, `is_up: false`

**Possible causes:**
- Network outage on GitHub Actions runner
- DNS resolution failure
- URLs missing scheme (must be `https://example.com`, not `example.com`)

**Fix:**
1. Check URL format in workflow YAML
2. Verify sites are actually up: `curl -I https://google.com`
3. Check GitHub Actions status page

### CSV File Not Updating

**Symptoms:** Workflow succeeds but no new rows in CSV

**Possible causes:**
- Git commit had no changes
- File write failed silently

**Fix:**
1. Check workflow logs for `log_results.py` output
2. Verify file exists: `git log -- logs/uptime_log.csv`
3. Look for error messages in workflow logs

### Telegram Alerts Not Sending

**Symptoms:** Sites are down but no messages received

**Possible causes:**
- Secrets not configured
- Invalid bot token or chat ID
- Bot blocked by user

**Fix:**
1. Verify secrets are set in **Settings** > **Secrets**
2. Test manually: `curl -X POST https://api.telegram.org/bot$TOKEN/sendMessage -d "chat_id=$CHAT_ID&text=test"`
3. Check workflow logs for Telegram API errors

**Expected:** If Telegram is not configured, the workflow logs "Telegram credentials not configured, skipping alerts" and continues. This is normal.

### Git Push Conflicts

**Symptoms:** Workflow fails at "Commit results" step

**Possible causes:**
- Two workflow runs overlapped (rare)
- Manual edits to CSV on another branch

**Fix:**
The workflow includes `git pull --rebase` to auto-resolve most conflicts. If it persists, manually resolve the conflict.

---

## File Structure

```
website-uptime-checker/
├── .github/workflows/
│   └── monitor.yml              # GitHub Actions workflow
├── .claude/agents/
│   ├── monitoring-specialist.md # HTTP check specialist
│   ├── data-logger-specialist.md # CSV logging specialist
│   └── alert-specialist.md       # Telegram alert specialist
├── tools/
│   ├── monitor.py               # HTTP health check tool
│   ├── log_results.py           # CSV logging tool
│   └── telegram_alert.py        # Telegram alert tool
├── logs/
│   └── uptime_log.csv           # Monitoring results (Git-versioned)
├── workflow.md                  # System workflow documentation
├── CLAUDE.md                    # Operating instructions for Claude
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## Extending the System

### Add More Alert Channels

Create new tools:
- `tools/slack_alert.py` — Slack webhook integration
- `tools/discord_alert.py` — Discord webhook integration
- `tools/email_alert.py` — SMTP email alerts

Call them in the workflow after `telegram_alert.py`.

### Add More Monitoring Checks

Extend `monitor.py` to check:
- SSL certificate expiry
- DNS resolution time
- HTTP header validation
- Response body content matching

### Add Alerting Logic

Implement alert throttling to avoid spam:
- Alert when site first goes down
- Send reminder every 30 minutes
- Alert when site recovers

Requires state tracking (last alert time per URL).

---

## License

This system is part of the WAT Systems Factory project.

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review workflow logs in the **Actions** tab
3. Read `CLAUDE.md` for detailed operating instructions
4. Open an issue in the repository

---

**Built with the WAT Systems Factory** — Autonomous AI agent systems powered by Claude Code and GitHub Actions.
