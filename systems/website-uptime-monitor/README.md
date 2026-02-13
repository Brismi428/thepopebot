# Website Uptime Monitor

A lightweight, Git-native uptime monitoring system that checks website availability, measures response time, and maintains a version-controlled CSV log of all checks.

## Features

- ✅ **Simple**: Single Python tool, zero external monitoring services
- ✅ **Git-native**: Every check is a commit, full history forever
- ✅ **Cost-effective**: Fits within GitHub Actions free tier
- ✅ **Visual**: Workflow status shows site status at a glance (green = up, red = down)
- ✅ **Precise**: Millisecond-level response time tracking
- ✅ **Reliable**: Handles timeouts, network errors, and concurrent runs gracefully
- ✅ **Extensible**: Easy to add alerting, multiple URLs, or custom metrics

## Quick Start

### 1. Deploy to GitHub

1. **Create a new repository** or use an existing one
2. **Copy these files** to your repository:
   ```
   .github/workflows/monitor.yml
   tools/monitor.py
   requirements.txt
   CLAUDE.md
   workflow.md
   ```
3. **Configure URL** (Settings → Secrets and variables → Actions → Variables):
   - Add variable: `MONITOR_URL` = `https://example.com`
4. **Push to GitHub** — the workflow starts automatically

### 2. Run Locally (Testing)

```bash
# Clone repository
git clone <your-repo-url>
cd website-uptime-monitor

# Install dependencies
pip install -r requirements.txt

# Run a check
python tools/monitor.py --url https://example.com

# View results
cat data/uptime_log.csv
```

### 3. View Results

- **GitHub Actions UI**: Go to Actions tab to see workflow status
- **CSV file**: Check `data/uptime_log.csv` for historical data
- **Git history**: Every check is a commit with timestamp

## Execution Paths

This system supports three execution modes:

### Path 1: Scheduled Cron (Primary)

**Automatic checks every 5 minutes via GitHub Actions**

```yaml
# Configured in .github/workflows/monitor.yml
schedule:
  - cron: '*/5 * * * *'
```

**Setup:**
1. Set `MONITOR_URL` repository variable
2. Push to GitHub
3. Checks run automatically

**Notes:**
- GitHub Actions cron has ±5 minute variance
- Actual frequency: 5-10 minutes
- Cost: ~1,440 GitHub Actions minutes/month (within free tier)

### Path 2: Manual Dispatch (Testing)

**Trigger checks on-demand via GitHub Actions UI or API**

**Via GitHub UI:**
1. Go to Actions tab
2. Select "Website Uptime Monitor"
3. Click "Run workflow"
4. Optionally override URL and timeout

**Via GitHub CLI:**
```bash
gh workflow run monitor.yml \
  -f url=https://example.com \
  -f timeout=10
```

**Use cases:**
- Test monitoring setup
- Check alternate URLs ad-hoc
- Force immediate check outside schedule

### Path 3: Local CLI (Development)

**Run checks locally during development**

```bash
python tools/monitor.py \
  --url https://example.com \
  --timeout 10 \
  --csv-path data/uptime_log.csv
```

**Use cases:**
- Test tool logic during development
- Generate sample data
- Debug CSV format issues

**Note:** Local runs do not auto-commit to Git

## Configuration

### Basic Configuration

Set these repository variables in GitHub:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `MONITOR_URL` | Target URL to monitor | `https://example.com` | Yes |
| `MONITOR_TIMEOUT` | Request timeout in seconds | `10` | No (default: 10) |

### Advanced Configuration

**Change check frequency:**
Edit `.github/workflows/monitor.yml`:
```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes
  - cron: '0 * * * *'     # Every hour
  - cron: '0 9 * * *'     # Daily at 9 AM UTC
```

**Monitor multiple URLs:**
Option 1: Create separate workflows for each URL
Option 2: Use GitHub Actions matrix strategy (see CLAUDE.md)

**Add authentication:**
See CLAUDE.md for instructions on monitoring authenticated endpoints

## Output Format

### CSV Log: `data/uptime_log.csv`

```csv
timestamp,url,status_code,response_time_ms,is_up
2026-02-13T01:13:32Z,https://example.com,200,245,true
2026-02-13T01:18:32Z,https://example.com,200,251,true
2026-02-13T01:23:32Z,https://example.com,500,1032,false
```

**Columns:**
- `timestamp`: ISO 8601 UTC timestamp
- `url`: Target URL that was checked
- `status_code`: HTTP status code (0 if request failed)
- `response_time_ms`: Response time in milliseconds
- `is_up`: Boolean (true for 2xx-3xx, false otherwise)

### Workflow Status

- **Green (passing)**: Site is UP (last check returned 2xx-3xx)
- **Red (failing)**: Site is DOWN (4xx, 5xx, timeout, or connection error)

## Data Analysis

### Command Line

**Uptime percentage:**
```bash
TOTAL=$(tail -n +2 data/uptime_log.csv | wc -l)
UP=$(grep ",true$" data/uptime_log.csv | wc -l)
echo "scale=2; $UP / $TOTAL * 100" | bc
```

**Average response time:**
```bash
tail -n +2 data/uptime_log.csv | \
  cut -d',' -f4 | \
  awk '{sum+=$1} END {print sum/NR " ms"}'
```

**Find downtime events:**
```bash
grep ",false$" data/uptime_log.csv
```

### Python/Pandas

```python
import pandas as pd

df = pd.read_csv('data/uptime_log.csv')

# Uptime percentage
uptime_pct = (df['is_up'].sum() / len(df)) * 100
print(f"Uptime: {uptime_pct:.2f}%")

# Average response time (successful checks only)
avg_time = df[df['is_up']]['response_time_ms'].mean()
print(f"Avg response time: {avg_time:.0f}ms")

# Recent downtime
downtime = df[~df['is_up']].tail(10)
```

## Troubleshooting

### Workflow Always Fails

**Check:**
1. Verify `MONITOR_URL` includes protocol (`https://`, not `example.com`)
2. Confirm URL is accessible from GitHub Actions (not behind firewall)
3. Check timeout setting (too low = false negatives)
4. Review GitHub Actions logs for specific error

### CSV File Not Updating

**Check:**
1. Verify workflow is running (Actions tab)
2. Check for git push errors in workflow logs
3. Ensure repository has "Read and write permissions" (Settings → Actions → General)

### Git Push Conflicts

**Symptom:** Workflow fails at "Commit results" step  
**Cause:** Rare race condition with concurrent runs  
**Fix:** Workflow includes retry logic — should self-resolve

## Cost & Performance

### GitHub Actions Minutes
- **Checks per month:** ~8,640 (every 5 minutes)
- **Minutes per check:** < 1 minute
- **Total:** ~1,440 minutes/month
- **Free tier:** 2,000 minutes/month (private repos), unlimited (public repos)

### CSV File Size
- **Growth rate:** ~30KB/day, ~10MB/year
- **Time to 100MB:** 10+ years at current rate
- **Recommendation:** Archive annually if needed

### Response Time
- **Typical check duration:** 2-5 seconds
- **Includes:** HTTP request + CSV write + Git commit

## Extensions

### Add Slack Alerting

Edit `.github/workflows/monitor.yml`:
```yaml
- name: Notify Slack
  if: steps.check.outcome == 'failure'
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"🚨 Site DOWN: ${{ env.URL }}"}'
```

### Add Dashboard

Create `tools/generate_dashboard.py`:
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/uptime_log.csv')
# Generate charts and save to docs/dashboard.html
# Serve via GitHub Pages
```

### Monitor Multiple Sites

Use GitHub Actions matrix strategy:
```yaml
strategy:
  matrix:
    site:
      - url: https://site1.com
        name: site1
      - url: https://site2.com
        name: site2
```

## Documentation

- **`CLAUDE.md`**: Complete operating instructions for AI agents
- **`workflow.md`**: Detailed step-by-step execution flow
- **`tools/monitor.py`**: Fully commented Python source code

## Requirements

- **Python**: 3.8+
- **Dependencies**: `requests==2.31.0` (auto-installed by GitHub Actions)
- **GitHub Actions**: Enabled on repository
- **Permissions**: Repository write access for commits

## License

This system is part of the WAT Systems Factory. Use freely for any monitoring needs.

## Support

- **Questions**: Check CLAUDE.md for detailed troubleshooting
- **Issues**: Review GitHub Actions logs for execution traces
- **Extensions**: See CLAUDE.md for extension ideas and patterns
