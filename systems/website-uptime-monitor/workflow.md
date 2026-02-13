# Website Uptime Monitor — Workflow

**System Type:** Monitor > Log (simplified monitoring pattern)  
**Execution Frequency:** Every 5 minutes (configurable via GitHub Actions cron)  
**Runtime:** 2-5 seconds per check

---

## Purpose

This system periodically checks if a target website is responding, measures response time, and maintains a version-controlled CSV log of all checks. GitHub Actions workflow status provides at-a-glance site status (green = up, red = down).

---

## Inputs

| Input | Type | Source | Required | Default | Description |
|-------|------|--------|----------|---------|-------------|
| `URL` | string | Environment variable or workflow input | Yes | - | Target URL to monitor (must include http:// or https://) |
| `TIMEOUT` | integer | Environment variable or workflow input | No | 10 | HTTP request timeout in seconds |

### Example Inputs

```bash
# Local execution
export URL=https://example.com
export TIMEOUT=10

# GitHub Actions dispatch
URL: https://example.com
TIMEOUT: 10
```

---

## Outputs

| Output | Type | Destination | Description |
|--------|------|-------------|-------------|
| `uptime_log.csv` | CSV file | `data/uptime_log.csv` in repo | Append-only log with columns: timestamp, url, status_code, response_time_ms, is_up |
| Exit code | integer | Tool exit code | 0 if site is up, 1 if site is down (sets workflow status) |

### CSV Format

```csv
timestamp,url,status_code,response_time_ms,is_up
2026-02-13T01:13:32Z,https://example.com,200,245,true
2026-02-13T01:18:32Z,https://example.com,200,251,true
2026-02-13T01:23:32Z,https://example.com,500,1032,false
```

---

## Workflow Steps

### Step 1: Check URL

**Purpose:** Make HTTP GET request to target URL, measure response time, determine up/down status.

**Execution:**
1. Read `URL` and `TIMEOUT` from environment variables or CLI arguments
2. Generate ISO 8601 UTC timestamp
3. Execute HTTP GET request with:
   - Timeout: `TIMEOUT` seconds (default 10)
   - Follow redirects: Yes (3xx status codes are considered "up")
   - User-Agent: `WAT-Uptime-Monitor/1.0`
4. Measure elapsed time in milliseconds using high-precision timer
5. Determine status:
   - **UP**: Status code 200-399
   - **DOWN**: Status code 400+, 0 (timeout/connection failure), or any exception

**Success Output:**
- `status_code`: HTTP response code (200, 404, 500, etc.)
- `response_time_ms`: Elapsed time in milliseconds
- `is_up`: Boolean (true if 200-399, false otherwise)

**Failure Modes:**
- **Timeout**: Log as DOWN with status_code=0, response_time=timeout*1000
- **Connection refused**: Log as DOWN with status_code=0
- **DNS failure**: Log as DOWN with status_code=0
- **SSL/TLS error**: Log as DOWN with status_code=0
- **Network error**: Log as DOWN with status_code=0

**Fallback:**
- All failures are logged as DOWN — no crash, no retry on network errors
- The goal is data continuity, not perfection

---

### Step 2: Log to CSV

**Purpose:** Append check result to version-controlled CSV file.

**Execution:**
1. Create `data/` directory if missing
2. **If CSV file does not exist**: Create with headers (`timestamp,url,status_code,response_time_ms,is_up`)
3. **Append row** with check results:
   - Use CSV writer with UTF-8 encoding
   - Use newline handling (`newline=""`) for cross-platform compatibility
   - Format: `timestamp,url,status_code,response_time_ms,is_up`
4. **Retry logic**: If append fails (file locked, disk full), retry up to 3 times with 1-second delay

**Success Output:**
- CSV file updated with new row
- Log message: `Logged to CSV: data/uptime_log.csv`

**Failure Modes:**
- **File locked** (rare due to GitHub Actions concurrency setting): Retry up to 3 times
- **Disk full**: Fail after 3 retries, print error
- **Permission denied**: Fail immediately (configuration error)

**Fallback:**
- If CSV write fails after 3 retries, print result to stdout and exit 1
- Human can manually add the entry from GitHub Actions logs

---

### Step 3: Commit to Git

**Purpose:** Commit updated CSV to repository, creating permanent audit trail.

**Execution:**
1. Stage only the CSV file: `git add data/uptime_log.csv`
2. Check for changes: `git diff --cached --quiet` (exit 0 if no changes)
3. **If changes exist**:
   - Configure git user: `git config user.name` and `git config user.email`
   - Commit with message: `"Uptime check: [UP|DOWN] {url} at {timestamp}"`
   - Push to origin: `git push`
4. **Concurrency handling**:
   - GitHub Actions `concurrency` setting prevents simultaneous runs
   - If push fails due to conflict (rare edge case), pull with rebase and retry

**Success Output:**
- New commit on current branch
- CSV file updated in remote repository
- Git push completes successfully

**Failure Modes:**
- **No changes to commit**: Skip commit step (silent success)
- **Push rejected** (concurrent edit): Pull with rebase, retry push
- **Authentication failure**: Fail with clear error (GITHUB_TOKEN expired or missing)

**Fallback:**
- If push fails after retry, the workflow fails but CSV is still logged locally
- Next successful run will include both entries (git commit includes all unstaged changes)

---

### Step 4: Signal Status

**Purpose:** Exit with appropriate code to set GitHub Actions workflow status.

**Execution:**
1. If `is_up == true`: Exit 0 (success — workflow shows green)
2. If `is_up == false`: Exit 1 (failure — workflow shows red)

**Success Output:**
- Workflow status reflects site status at-a-glance in GitHub Actions UI
- No additional alerting needed — workflow history IS the alert

**Failure Modes:**
- None — this step always succeeds

---

## Execution Paths

### Path 1: Scheduled Cron (Primary)

**Trigger:** GitHub Actions cron expression `*/5 * * * *` (every 5 minutes)

**Flow:**
1. GitHub Actions workflow triggers on schedule
2. Workflow sets `URL` and `TIMEOUT` environment variables
3. Runs tool: `python tools/monitor.py --url $URL --timeout $TIMEOUT`
4. Tool executes Steps 1-4
5. Workflow commits CSV changes
6. Workflow status reflects site status

**Notes:**
- GitHub Actions cron has ±5 minute variance (not a bug, by design)
- Actual check frequency: 5-10 minutes
- Cost: ~1,440 GitHub Actions minutes/month (fits within free tier)

### Path 2: Manual Dispatch (Testing)

**Trigger:** GitHub Actions `workflow_dispatch` with optional URL input

**Flow:**
1. User triggers workflow via Actions UI or API
2. Optionally override default URL in workflow inputs
3. Workflow executes same flow as Path 1
4. Results committed to repo

**Use Cases:**
- Test monitoring setup
- Check alternate URLs ad-hoc
- Force immediate check outside schedule

### Path 3: Local CLI (Development)

**Trigger:** Developer runs tool locally

**Flow:**
```bash
# Set environment variables or use CLI args
python tools/monitor.py --url https://example.com --timeout 10

# Check CSV output
cat data/uptime_log.csv
```

**Use Cases:**
- Test tool logic during development
- Generate sample data
- Debug CSV format issues

**Note:** Local runs do not auto-commit to git

---

## Failure Handling Summary

| Failure | Response | Recovery |
|---------|----------|----------|
| URL timeout | Log as DOWN (status=0, time=timeout*1000) | Continue — next check may succeed |
| Network error | Log as DOWN (status=0) | Continue — transient failures expected |
| CSV write failure | Retry 3x, then fail | Print to stdout, exit 1 — human adds entry from logs |
| Git push conflict | Pull with rebase, retry | Rare — concurrency setting prevents this |
| All failures | Tool exits 1 | Workflow fails (shows red), next run continues |

**Design Philosophy:** Data continuity over perfection. Log everything, even failures. Git history is the source of truth.

---

## Extension Points

### Add Alerting
Modify `.github/workflows/monitor.yml` to send alerts on failure:
```yaml
- name: Notify on failure
  if: failure()
  uses: actions/send-slack-notification
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    message: "🚨 Site is DOWN: ${{ env.URL }}"
```

### Monitor Multiple URLs
Use GitHub Actions matrix strategy:
```yaml
strategy:
  matrix:
    url:
      - https://example.com
      - https://anothersite.com
      - https://thirdsite.com
```

### Add Authentication
Modify tool to accept auth credentials:
```bash
python tools/monitor.py \
  --url https://example.com \
  --auth-user $USERNAME \
  --auth-pass $PASSWORD
```

### Change Check Frequency
Edit cron expression in `.github/workflows/monitor.yml`:
```yaml
# Every 15 minutes
- cron: '*/15 * * * *'

# Every hour
- cron: '0 * * * *'

# Every day at 9 AM UTC
- cron: '0 9 * * *'
```

---

## Success Criteria

✅ URL check completes in < 10 seconds (typical: 2-5s)  
✅ CSV log appends without corruption  
✅ Git commit includes only CSV file  
✅ Workflow status reflects site status (green=up, red=down)  
✅ Response time measured in milliseconds  
✅ Timestamp in ISO 8601 UTC format  
✅ All execution paths produce identical CSV format  
✅ System handles concurrent runs gracefully  

---

## Maintenance

**CSV file growth:** At 288 checks/day (every 5 minutes), CSV grows ~50KB/year. Git handles this easily for decades.

**GitHub Actions minutes:** ~1,440 minutes/month for 5-minute checks. Well within free tier (2,000/month for private repos, unlimited for public repos).

**No secrets required:** Public URL monitoring needs no authentication. Add `BASIC_AUTH_USER` and `BASIC_AUTH_PASS` secrets if monitoring authenticated endpoints.
