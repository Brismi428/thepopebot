# Website Uptime Monitor — Operating Instructions

## Identity

You are the Website Uptime Monitor — an autonomous system that periodically checks if a target website is responding, measures response time, and maintains a version-controlled CSV log of all checks.

## Purpose

This system provides lightweight, git-native uptime monitoring for any website. Every check is logged, every log is committed, and GitHub Actions workflow status provides at-a-glance site visibility (green = up, red = down).

## Core Capabilities

- **HTTP health checks**: GET requests with timeout and redirect following
- **Response time measurement**: Millisecond-precision timing
- **CSV logging**: Append-only time-series data in version-controlled file
- **Status signaling**: Exit codes set workflow status (0=up, 1=down)
- **Concurrent execution safety**: File locking + GitHub Actions concurrency settings

## System Design

This is a **Monitor > Log** pattern — the simplest possible monitoring system:
- No detection logic (no comparison to previous state)
- No alerting layer (workflow red/green IS the notification)
- Direct logging: check → CSV → commit

**Why this works:**
- Git history provides complete audit trail
- CSV format is queryable with standard tools
- Workflow status is visible in GitHub UI and available via API
- Zero external dependencies (no monitoring service, no database)

---

## Required Tools & MCPs

### Python Libraries
- **requests** (HTTP client) — required for URL checks
- **csv** (stdlib) — CSV file handling
- **pathlib** (stdlib) — File system operations
- **argparse** (stdlib) — CLI argument parsing
- **logging** (stdlib) — Structured logging

**Installation:** `pip install -r requirements.txt`

### MCPs
**None required.** This system uses Python standard library + requests for maximum reliability. No MCP dependencies.

### Fallback Approaches
- **requests unavailable**: Use stdlib `urllib.request` (less convenient, same functionality)
- **CSV writes failing**: Print to stdout, parse from GitHub Actions logs

---

## Inputs

### Required
| Input | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `URL` | string | Env var, workflow input, or CLI arg | Target URL to monitor (must include protocol) | `https://example.com` |

### Optional
| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `TIMEOUT` | integer | 10 | HTTP request timeout in seconds |
| `CSV_PATH` | string | `data/uptime_log.csv` | Output CSV file path |

### Setting Inputs

**GitHub Actions (scheduled):**
Set repository variables:
- `MONITOR_URL` → Target URL
- `MONITOR_TIMEOUT` → Timeout in seconds (optional)

**GitHub Actions (manual dispatch):**
Use workflow inputs to override defaults for ad-hoc checks.

**Local CLI:**
```bash
python tools/monitor.py --url https://example.com --timeout 10
```

---

## Outputs

### Primary Output: CSV Log
**File:** `data/uptime_log.csv`  
**Format:**
```csv
timestamp,url,status_code,response_time_ms,is_up
2026-02-13T01:13:32Z,https://example.com,200,245,true
2026-02-13T01:18:32Z,https://example.com,200,251,true
```

**Columns:**
- `timestamp`: ISO 8601 UTC timestamp
- `url`: Target URL that was checked
- `status_code`: HTTP status code (0 if request failed)
- `response_time_ms`: Response time in milliseconds
- `is_up`: Boolean (true if 200-399, false otherwise)

### Secondary Output: Exit Code
- **0**: Site is UP (workflow succeeds, shows green)
- **1**: Site is DOWN (workflow fails, shows red)

---

## Execution Instructions

### Running the Workflow

**Scheduled Execution (Primary):**
1. GitHub Actions cron triggers every 5 minutes
2. Workflow reads `MONITOR_URL` from repository variables
3. Tool checks URL, logs to CSV, commits result
4. Workflow status reflects site status

**Manual Execution (Testing):**
```bash
# Via GitHub Actions UI
# - Go to Actions tab
# - Select "Website Uptime Monitor"
# - Click "Run workflow"
# - Optionally override URL and timeout

# Via GitHub CLI
gh workflow run monitor.yml \
  -f url=https://example.com \
  -f timeout=10
```

**Local Execution (Development):**
```bash
# Clone repository
git clone <repo-url>
cd website-uptime-monitor

# Install dependencies
pip install -r requirements.txt

# Run check
python tools/monitor.py --url https://example.com

# View results
cat data/uptime_log.csv
```

### Tool Invocation

```bash
python tools/monitor.py \
  --url <target-url> \
  [--timeout <seconds>] \
  [--csv-path <path>]
```

**Arguments:**
- `--url`: Required. Target URL with protocol (http:// or https://)
- `--timeout`: Optional. Request timeout in seconds (default: 10)
- `--csv-path`: Optional. Output CSV path (default: data/uptime_log.csv)

**Exit codes:**
- `0`: Site is UP (2xx-3xx status)
- `1`: Site is DOWN (4xx-5xx, timeout, or connection failure)

---

## Workflow Execution

Follow `workflow.md` for the complete step-by-step process:

1. **Check URL** → HTTP GET with timeout, measure response time
2. **Log to CSV** → Append result to data/uptime_log.csv
3. **Commit to Git** → Stage CSV, commit with status message, push
4. **Signal Status** → Exit 0 (up) or 1 (down)

**Workflow runtime:** 2-5 seconds per check  
**Typical flow:** Check completes → CSV updated → Git commit → Push

---

## Configuration

### GitHub Actions Configuration

**Set Repository Variables:**
1. Go to Settings → Secrets and variables → Actions → Variables
2. Add:
   - `MONITOR_URL`: Target URL (e.g., `https://example.com`)
   - `MONITOR_TIMEOUT`: Optional timeout override (default: 10)

**Adjust Check Frequency:**
Edit `.github/workflows/monitor.yml` cron expression:
```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes (current)
  - cron: '*/15 * * * *' # Every 15 minutes
  - cron: '0 * * * *'    # Every hour
```

**Enable Manual Triggers:**
Workflow includes `workflow_dispatch` — no additional setup needed.

### Monitoring Multiple URLs

**Option 1: Multiple Workflows**
- Copy `.github/workflows/monitor.yml` → `monitor-site2.yml`
- Set different repository variables: `MONITOR_URL_SITE2`
- Adjust workflow to read the appropriate variable

**Option 2: Matrix Strategy**
Edit workflow to use GitHub Actions matrix:
```yaml
strategy:
  matrix:
    url:
      - https://site1.com
      - https://site2.com
      - https://site3.com
```

**Option 3: Separate Repositories**
- Deploy this system once per URL to monitor
- Each repo maintains its own CSV log

---

## Secrets & Authentication

### Default: No Secrets Required
Public URL monitoring needs no authentication. The tool makes unauthenticated GET requests.

### Monitoring Authenticated Endpoints
If monitoring requires authentication:

1. **Add GitHub Secrets:**
   - `MONITOR_AUTH_USER`: Username or API key
   - `MONITOR_AUTH_PASS`: Password or token

2. **Modify tool** to accept auth:
   ```python
   # In check_url():
   auth = (os.environ.get('MONITOR_AUTH_USER'), 
           os.environ.get('MONITOR_AUTH_PASS'))
   response = requests.get(url, auth=auth if auth[0] else None, ...)
   ```

3. **Update workflow** to pass secrets:
   ```yaml
   env:
     MONITOR_AUTH_USER: ${{ secrets.MONITOR_AUTH_USER }}
     MONITOR_AUTH_PASS: ${{ secrets.MONITOR_AUTH_PASS }}
   ```

---

## Troubleshooting

### CSV File Not Created
**Symptom:** Tool runs but no CSV file appears  
**Cause:** `data/` directory missing or permissions issue  
**Fix:** Tool creates `data/` automatically. Check GitHub Actions logs for errors.

### Git Push Fails
**Symptom:** Workflow fails at "Commit results" step  
**Cause:** GITHUB_TOKEN expired or insufficient permissions  
**Fix:** Ensure workflow has `contents: write` permission (default for Actions)

### Workflow Always Shows Red
**Symptom:** Every run fails, even when site is up  
**Check:**
1. Verify `MONITOR_URL` includes protocol (`https://`, not `example.com`)
2. Check timeout setting (too low = false negatives)
3. Review GitHub Actions logs for actual error

### Concurrent Run Conflicts
**Symptom:** Git push fails with "rejected" error  
**Cause:** Two workflow runs tried to commit simultaneously  
**Fix:** Workflow includes `concurrency` setting to prevent this. If it still happens, the retry logic handles it.

### CSV Growing Too Large
**Symptom:** CSV file approaching GitHub's 100MB file limit  
**Solution:** At 288 checks/day, CSV grows ~50KB/year. Won't hit 100MB for decades.  
**If needed:** Archive old data periodically:
```bash
# Split CSV by year
grep "^2026" data/uptime_log.csv > archive/uptime_2026.csv
```

---

## Data Analysis

### Query CSV with Command Line Tools

**Count total checks:**
```bash
tail -n +2 data/uptime_log.csv | wc -l
```

**Calculate uptime percentage:**
```bash
# Total checks
TOTAL=$(tail -n +2 data/uptime_log.csv | wc -l)

# Up checks (is_up=true)
UP=$(tail -n +2 data/uptime_log.csv | grep ",true$" | wc -l)

# Calculate percentage
echo "scale=2; $UP / $TOTAL * 100" | bc
```

**Find all downtime events:**
```bash
grep ",false$" data/uptime_log.csv
```

**Average response time:**
```bash
tail -n +2 data/uptime_log.csv | \
  cut -d',' -f4 | \
  awk '{sum+=$1} END {print sum/NR " ms"}'
```

**Recent status (last 10 checks):**
```bash
tail -10 data/uptime_log.csv
```

### Query CSV with Python/Pandas

```python
import pandas as pd

df = pd.read_csv('data/uptime_log.csv')

# Uptime percentage
uptime_pct = (df['is_up'].sum() / len(df)) * 100
print(f"Uptime: {uptime_pct:.2f}%")

# Average response time (only successful checks)
avg_time = df[df['is_up']]['response_time_ms'].mean()
print(f"Avg response time: {avg_time:.0f}ms")

# Downtime events
downtime = df[~df['is_up']]
print(f"Downtime events: {len(downtime)}")
```

---

## Cost & Performance

### GitHub Actions Minutes
- **Check frequency:** Every 5 minutes
- **Checks per day:** 288
- **Checks per month:** ~8,640
- **Minutes per check:** < 1 minute
- **Total monthly cost:** ~1,440 GitHub Actions minutes

**Free tier:**
- Public repos: Unlimited
- Private repos: 2,000 minutes/month (this system uses ~72% of free tier)

### CSV File Size
- **Bytes per row:** ~100 bytes
- **Rows per day:** 288
- **Growth rate:** ~30KB/day, ~10MB/year
- **Git repo impact:** Minimal (Git handles text files efficiently)

### Response Time
- **Typical:** 100-500ms (depends on target site)
- **Max:** Set by `TIMEOUT` parameter (default 10s)
- **Tool overhead:** < 100ms (CSV write + git operations)

---

## Extension Ideas

### Add Alerting
**Slack notification on downtime:**
```yaml
- name: Notify Slack
  if: steps.check.outcome == 'failure'
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"🚨 Site DOWN: ${{ env.URL }}"}'
```

### Add Dashboard
Generate HTML dashboard from CSV:
```python
# tools/generate_dashboard.py
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/uptime_log.csv')
# ... generate charts ...
# Save to docs/dashboard.html
# Commit to repo, serve via GitHub Pages
```

### Add More Metrics
Extend CSV with:
- DNS resolution time
- TLS handshake time
- First byte time (TTFB)
- Content length

---

## Maintenance

### Regular Tasks
- **None required.** System is fully autonomous.

### Periodic Tasks
- **Quarterly:** Review CSV file size, archive if needed
- **Annually:** Review uptime statistics, adjust alerting thresholds

### Version Updates
- **Python dependencies:** `pip install --upgrade -r requirements.txt`
- **GitHub Actions:** Actions update automatically (using `@v4`, `@v5` tags)

---

## Success Indicators

✅ CSV file grows by 288 rows/day  
✅ Workflow runs complete in < 5 seconds  
✅ Git commits include only CSV file (no other files)  
✅ Workflow status matches site status (green=up, red=down)  
✅ No concurrent run conflicts  
✅ Response times logged accurately  
✅ Downtime events captured  

---

## Support & Documentation

- **Workflow steps:** See `workflow.md` for detailed execution flow
- **Tool source:** `tools/monitor.py` (fully commented)
- **GitHub Actions:** `.github/workflows/monitor.yml` (annotated)
- **CSV format:** Standard CSV with UTF-8 encoding (Excel/Sheets compatible)

**Questions or issues?** Check GitHub Actions logs for detailed execution traces. Every run is fully logged.
