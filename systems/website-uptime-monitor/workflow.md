# Website Uptime Monitor — Workflow

## Purpose

Monitor a single website URL on a 5-minute schedule and log status to a CSV file. This system provides historical uptime data with full Git audit trail, running entirely on GitHub Actions with zero external dependencies.

## Inputs

- `MONITOR_URL` (environment variable) — The URL to monitor (http:// or https://). Required.
- `TIMEOUT_SECONDS` (environment variable) — HTTP request timeout in seconds. Default: 10.
- Alternatively, read from `config/monitor.json` if present (optional config file approach).

## Outputs

- `logs/uptime_log.csv` — Append-only CSV file with headers: `timestamp`, `url`, `status_code`, `response_time_ms`, `is_up`
- Each check appends one row to the CSV
- CSV is committed to the repository after each check
- Git history provides full audit trail of all uptime checks

## Failure Modes

| Step | Failure Mode | Fallback |
|------|--------------|----------|
| Load Configuration | Config file missing or malformed | Use environment variables with defaults |
| Execute HTTP Check | Timeout, DNS failure, connection refused, SSL error | Record as "down" with status_code=0 |
| Append to CSV Log | File write permission error, disk full | Log error to stderr, exit non-zero (GitHub Actions shows failure) |
| Commit and Push | Git push conflict (simultaneous runs) | Pull with rebase, retry push once. If still fails, log error and exit. |

---

## Step 1: Load Configuration

**Objective:** Determine the target URL and timeout value.

**Process:**
1. Check for environment variables: `MONITOR_URL` and `TIMEOUT_SECONDS`
2. If `MONITOR_URL` is not set, check for `config/monitor.json`
3. Parse config file if present: `{"url": "https://example.com", "timeout": 10}`
4. Validate that URL is a valid HTTP/HTTPS URL
5. Default timeout to 10 seconds if not specified

**Outputs:**
- `target_url` (string) — The URL to check
- `timeout_seconds` (integer) — Request timeout in seconds

**Failure Handling:**
- If both env var and config file are missing, exit with error code 1 and clear message
- If URL format is invalid, exit with error code 1

---

## Step 2: Execute HTTP Check

**Objective:** Send an HTTP GET request to the target URL and measure response time.

**Process:**
1. Record current timestamp in ISO 8601 format with UTC timezone: `datetime.now(timezone.utc).isoformat()`
2. Start timer using `time.monotonic()` for high-precision elapsed time measurement
3. Send HTTP GET request using `requests.get(url, timeout=timeout_seconds, allow_redirects=True)`
4. Capture response:
   - **Success**: Record status code and calculate elapsed time in milliseconds
   - **Timeout**: Catch `requests.exceptions.Timeout`, set status_code=0, elapsed_ms=timeout*1000
   - **Connection Error**: Catch `requests.exceptions.ConnectionError`, set status_code=0, elapsed_ms=0
   - **Other Request Errors**: Catch `requests.exceptions.RequestException`, set status_code=0, elapsed_ms=0
5. Determine `is_up` status:
   - `status_code < 400` → `is_up = true`
   - `status_code >= 400` → `is_up = false`
   - `status_code == 0` (timeout or error) → `is_up = false`

**Outputs:**
- `timestamp` (string) — ISO 8601 timestamp with UTC timezone
- `status_code` (integer) — HTTP status code, or 0 if timeout/error
- `response_time_ms` (float) — Response time in milliseconds, rounded to 2 decimal places
- `is_up` (boolean) — True if status_code < 400, False otherwise

**Failure Handling:**
- All HTTP exceptions are caught and recorded as "down" status
- No exception crashes the script — every check produces a log entry

---

## Step 3: Append to CSV Log

**Objective:** Write the check result to the CSV log file.

**Process:**
1. Ensure `logs/` directory exists: `mkdir -p logs` or `Path('logs').mkdir(parents=True, exist_ok=True)`
2. Check if `logs/uptime_log.csv` exists
   - **If file does not exist**: Create it and write header row: `timestamp,url,status_code,response_time_ms,is_up`
   - **If file exists**: Skip header (already written)
3. Open file in append mode with `newline=''` (prevents blank rows on Windows)
4. Write data row with values from Step 2: `timestamp,url,status_code,response_time_ms,is_up`
5. Close file

**Outputs:**
- Updated `logs/uptime_log.csv` with one new row appended

**Failure Handling:**
- If directory creation fails (permission error), log to stderr and exit non-zero
- If file write fails (disk full, permission error), log to stderr and exit non-zero
- File is opened with explicit encoding `utf-8` to ensure cross-platform compatibility

---

## Step 4: Commit and Push

**Objective:** Commit the updated CSV file to the repository.

**This step is handled by GitHub Actions, not by the tool itself.**

**Process:**
1. Configure Git credentials: `git config user.email "github-actions[bot]@users.noreply.github.com"`
2. Configure Git username: `git config user.name "github-actions[bot]"`
3. Stage the updated CSV file: `git add logs/uptime_log.csv`
4. Commit with descriptive message: `git commit -m "Uptime check: [URL] [status] at [timestamp]"`
5. Push to main branch: `git push`

**Outputs:**
- New commit in the repository's main branch
- CSV file is version-controlled and auditable via Git history

**Failure Handling:**
- If push fails due to conflict (simultaneous workflow runs):
  - Pull with rebase: `git pull --rebase`
  - Retry push: `git push`
  - If retry fails, log error to stderr and exit non-zero (GitHub Actions will show failed run)
- Git authentication uses `GITHUB_TOKEN` (automatically provided by GitHub Actions)

---

## Exit Codes

The `check_url.py` tool uses exit codes to signal success/failure:

- **Exit 0** — URL is up (status_code < 400)
- **Exit 1** — URL is down (status_code >= 400 or timeout/error)

This allows GitHub Actions to show the workflow run as "failed" when the monitored site is down, providing at-a-glance status visibility in the Actions UI.

---

## Execution Paths

### Path 1: GitHub Actions (Scheduled — Primary)

Automated execution every 5 minutes via cron schedule.

```bash
# Triggered by: .github/workflows/monitor.yml schedule
# Environment: GitHub Actions runner (Ubuntu)
# Secrets: GITHUB_TOKEN (auto-provided)

# The workflow:
# 1. Checks out the repository
# 2. Sets up Python 3.11
# 3. Installs dependencies (requests)
# 4. Runs: python tools/check_url.py --url $MONITOR_URL --timeout $TIMEOUT_SECONDS --csv logs/uptime_log.csv
# 5. Commits and pushes logs/uptime_log.csv
# 6. Shows success/failure status based on tool exit code
```

### Path 2: GitHub Actions (Manual — Testing)

Manual trigger for testing or one-off checks.

```bash
# Triggered by: workflow_dispatch in GitHub Actions UI
# Optional input: Override URL for one-time check
# Same process as scheduled execution
```

### Path 3: Claude Code CLI (Local Testing)

Local execution for development and testing.

```bash
# Environment: Local machine with Python and requests installed

# Set environment variables
export MONITOR_URL="https://example.com"
export TIMEOUT_SECONDS="10"

# Run the tool directly
python tools/check_url.py --url $MONITOR_URL --timeout $TIMEOUT_SECONDS --csv logs/uptime_log.csv

# Check the CSV
cat logs/uptime_log.csv

# Optionally commit manually
git add logs/uptime_log.csv
git commit -m "Manual uptime check"
```

---

## Monitoring Best Practices

1. **Check the GitHub Actions page** — Each workflow run shows whether the site is up or down. Failed runs (red X) indicate downtime.

2. **Review the CSV file** — The `logs/uptime_log.csv` file provides historical data. Use Git history to see when downtime occurred:
   ```bash
   git log --oneline -- logs/uptime_log.csv
   ```

3. **Analyze downtime patterns** — Export the CSV and analyze in a spreadsheet or BI tool to identify patterns (time of day, duration, frequency).

4. **Adjust timeout** — If you're monitoring a slow endpoint, increase `TIMEOUT_SECONDS` to avoid false negatives.

5. **Add alerting** — For real-time alerts, integrate with GitHub Actions notifications, Slack, or Discord (extend the workflow with a notification step).

6. **Multiple URLs** — To monitor multiple sites, create multiple workflow files (one per site) with different schedule offsets to avoid GitHub Actions rate limits.

---

## Notes

- **GitHub Actions cron is not exact** — Expect ±5 minute variance under load. This is a GitHub platform limitation, not a bug in the workflow.

- **Rate limits** — GitHub Actions free tier allows 2,000 minutes/month for private repos, unlimited for public repos. At 5-minute intervals, this system uses ~8,640 checks/month (144 checks/day × 30 days). Each check takes ~10 seconds, consuming ~1,440 minutes/month. This fits within the free tier.

- **Repository size** — CSV grows by ~100 bytes per check. At 8,640 checks/month, that's ~850 KB/month or ~10 MB/year. The repo will remain small for years of continuous monitoring.

- **Data retention** — Git history retains all checks forever. To prune old data, periodically squash commits or archive old data to a separate file.

- **Security** — This system does not handle authentication. To monitor authenticated endpoints, add authentication headers to the `check_url.py` tool and pass credentials via GitHub Secrets.
