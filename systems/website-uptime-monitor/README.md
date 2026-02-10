# Website Uptime Monitor

A lightweight, Git-native uptime monitoring system that checks a website URL every 5 minutes and logs results to a CSV file. Runs entirely on GitHub Actions with zero external dependencies.

## Features

- ✅ **Automated checks** — Every 5 minutes via GitHub Actions cron
- ✅ **Historical data** — All checks logged to CSV with Git audit trail
- ✅ **At-a-glance status** — GitHub Actions UI shows up/down status
- ✅ **Zero dependencies** — No external monitoring SaaS required
- ✅ **Cost-free** — Runs on GitHub Actions free tier
- ✅ **Simple CSV output** — Easy to analyze with any spreadsheet or BI tool
- ✅ **Extensible** — Add alerting, multiple URLs, authentication, etc.

## Quick Start

### 1. Deploy to GitHub

```bash
# Clone this repository (or copy these files to your repo)
git clone https://github.com/OWNER/website-uptime-monitor.git
cd website-uptime-monitor

# Push to your own GitHub repository
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

### 2. Configure Monitoring

Go to your repository's **Settings → Secrets and variables → Actions → Variables** and add:

| Variable | Value | Required |
|----------|-------|----------|
| `MONITOR_URL` | `https://example.com` | Yes |
| `TIMEOUT_SECONDS` | `10` | No (default: 10) |

### 3. Monitor

The system starts automatically! Check the **Actions** tab:

- ✅ **Green checkmark** = site is up
- ❌ **Red X** = site is down

View historical data in `logs/uptime_log.csv`.

## Execution Paths

### Path 1: Scheduled (Primary)

Automatic checks every 5 minutes.

- **Setup**: Configure `MONITOR_URL` variable (Step 2 above)
- **Monitoring**: Check Actions tab for workflow runs
- **Data**: View `logs/uptime_log.csv` in the repository

### Path 2: Manual Trigger

Run a one-time check on demand.

**Via GitHub UI:**
1. Go to Actions tab
2. Select "Website Uptime Monitor" workflow
3. Click "Run workflow"
4. Optionally override the URL
5. Click "Run workflow" button

**Via GitHub CLI:**
```bash
gh workflow run monitor.yml \
  --field url="https://example.com" \
  --field timeout="10"
```

### Path 3: Local Testing

Run the tool locally for development.

**Requirements:**
- Python 3.11+
- `pip install -r requirements.txt`

**Usage:**
```bash
export MONITOR_URL="https://example.com"
export TIMEOUT_SECONDS="10"

python tools/check_url.py --url $MONITOR_URL --timeout $TIMEOUT_SECONDS --csv logs/uptime_log.csv
```

### Path 4: GitHub Agent HQ

Request tasks via GitHub Issues (requires `ANTHROPIC_API_KEY` secret).

**Example tasks:**

```markdown
@claude Run a manual check of https://example.org
```

```markdown
@claude Analyze the uptime log for the past week and report downtime patterns
```

See `CLAUDE.md` for full Agent HQ documentation.

## CSV Log Format

`logs/uptime_log.csv` contains one row per check:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp (UTC) |
| `url` | string | The URL that was checked |
| `status_code` | integer | HTTP status code (or 0 if timeout/error) |
| `response_time_ms` | float | Response time in milliseconds |
| `is_up` | boolean | True if status_code < 400, False otherwise |

**Example:**
```csv
timestamp,url,status_code,response_time_ms,is_up
2026-02-10T20:00:00+00:00,https://example.com,200,145.32,True
2026-02-10T20:05:00+00:00,https://example.com,200,132.18,True
2026-02-10T20:10:00+00:00,https://example.com,503,5021.47,False
```

## Data Analysis

### Basic Stats (Bash)

```bash
# Count total checks
wc -l logs/uptime_log.csv

# Count downtime events
grep ",False" logs/uptime_log.csv | wc -l

# Calculate uptime percentage
TOTAL=$(tail -n +2 logs/uptime_log.csv | wc -l)
UP=$(grep ",True" logs/uptime_log.csv | wc -l)
echo "scale=2; $UP / $TOTAL * 100" | bc
```

### Advanced Analysis (Python)

```python
import pandas as pd

df = pd.read_csv('logs/uptime_log.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Uptime percentage
uptime_pct = (df['is_up'].sum() / len(df)) * 100
print(f"Uptime: {uptime_pct:.2f}%")

# Average response time (when up)
avg_response = df[df['is_up']]['response_time_ms'].mean()
print(f"Avg response time: {avg_response:.2f}ms")

# Daily summary
df['date'] = df['timestamp'].dt.date
daily = df.groupby('date')['is_up'].agg(['sum', 'count'])
daily['uptime_pct'] = (daily['sum'] / daily['count']) * 100
print(daily)
```

## Extending the System

### Add Slack Alerts

Add to `.github/workflows/monitor.yml`:

```yaml
- name: Notify Slack on downtime
  if: steps.check.outputs.exit_code != '0'
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"🚨 Website down: '"$MONITOR_URL"'"}'
```

### Monitor Multiple URLs

Create multiple workflow files with different URLs and schedule offsets:

```yaml
# monitor-site1.yml
on:
  schedule:
    - cron: '*/5 * * * *'  # :00, :05, :10, etc.

# monitor-site2.yml
on:
  schedule:
    - cron: '1-59/5 * * * *'  # :01, :06, :11, etc.
```

### Add Authentication

Modify `tools/check_url.py` to accept auth headers, then pass credentials via GitHub Secrets:

```yaml
- name: Run uptime check
  env:
    AUTH_TOKEN: ${{ secrets.API_AUTH_TOKEN }}
  run: |
    python tools/check_url.py --url $MONITOR_URL --auth-header "Bearer $AUTH_TOKEN"
```

See `CLAUDE.md` for more extension examples.

## Troubleshooting

### Workflow not running every 5 minutes

GitHub Actions cron has ±5 minute variance under load. This is normal and expected.

### CSV file not being committed

Check the Actions logs. The workflow includes retry logic for git push conflicts. If this persists, check for permission issues or concurrent runs.

### All checks showing as "down"

1. Increase `TIMEOUT_SECONDS` if the site is genuinely slow
2. Test the URL locally: `curl -I https://example.com`
3. Check if the target site blocks GitHub Actions IPs

See `CLAUDE.md` for full troubleshooting guide.

## Documentation

- **`CLAUDE.md`** — Full operating instructions for Claude Code
- **`workflow.md`** — Detailed workflow process documentation
- **`tools/check_url.py`** — Tool implementation with inline comments

## Cost & Resource Usage

### GitHub Actions Minutes

- ~48 minutes/day for 5-minute checks
- ~1,440 minutes/month
- **Free tier**: 2,000 minutes/month (private repos), unlimited (public repos)

### Repository Size

- ~100 bytes per check
- ~9.5 MB/month, ~114 MB/year
- Git handles this easily; consider archiving data after 1-2 years

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Cron)                    │
│                     Every 5 minutes                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  tools/check_url.py  │
              │                      │
              │  1. HTTP GET request │
              │  2. Measure response │
              │  3. Append to CSV    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ logs/uptime_log.csv  │
              │ (Git version control)│
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Git commit & push  │
              │   (Audit trail)      │
              └──────────────────────┘
```

## Security

- ✅ No secrets in code (environment variables only)
- ✅ Minimal permissions (default `GITHUB_TOKEN`)
- ✅ No external services (except monitored URL)
- ✅ CSV is public — don't monitor URLs that leak sensitive data

## Support

- **Issues**: Open a GitHub Issue in this repository
- **Agent HQ**: Mention `@claude` in an issue (requires `ANTHROPIC_API_KEY`)
- **Documentation**: See `CLAUDE.md` for detailed operating instructions

## License

Generated by the WAT Systems Factory. Modify and distribute freely.

---

**Status**: Production-ready
**Generated**: 2026-02-10
**Factory Version**: 0.1.0
