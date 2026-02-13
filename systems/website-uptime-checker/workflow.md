# Website Uptime Checker — Workflow

A GitHub Actions-powered monitoring system that checks website availability every 5 minutes, logs all results to a Git-versioned CSV file, and optionally sends Telegram alerts when sites go down.

## Inputs

- **urls**: List of URLs to monitor (configured in GitHub Actions workflow)
  - Format: `["https://google.com", "https://github.com"]`
  - Must include scheme (https://)
- **timeout**: HTTP request timeout in seconds (default: 30)
- **telegram_bot_token**: Optional Telegram bot token for alerts (GitHub Secret)
- **telegram_chat_id**: Optional Telegram chat ID for alerts (GitHub Secret)

## Outputs

- **logs/uptime_log.csv**: Append-only CSV file with columns:
  - `timestamp` — ISO 8601 timestamp
  - `url` — The URL checked
  - `status_code` — HTTP status code (0 if connection failed)
  - `response_time_ms` — Response time in milliseconds (-1 if failed)
  - `is_up` — Boolean (true if HTTP 200-299)
- **Telegram alerts**: Optional messages sent when sites go down
- **Git commit**: All results committed to repository

---

## Step 1: Check Websites

Perform HTTP GET requests to each configured URL and measure response times.

**Delegate to:** `monitoring-specialist` subagent

1. For each URL in the configured list:
   - Send HTTP GET request with configured timeout
   - Measure response time using monotonic clock
   - Determine status:
     - **HTTP 200-299**: Site is up
     - **All other codes**: Site is down
     - **Connection failure**: status_code = 0, is_up = false
2. Collect all results into a list of check objects
3. Return results as JSON for next step

**Tool**: `tools/monitor.py`

**Decision point**: **If any site check fails (timeout, DNS error, connection refused)**:
- **Action**: Log the failure as status_code=0, response_time=-1, is_up=false
- **Continue**: Process remaining URLs (don't let one failure kill the batch)

**Failure mode**: All URLs fail to connect (network outage, DNS failure)
**Fallback**: Record all failures with status_code=0, continue to logging step (empty data is still valid data)

---

## Step 2: Log Results

Append check results to CSV log file, creating the file with headers if it doesn't exist.

**Delegate to:** `data-logger-specialist` subagent

1. Check if `logs/uptime_log.csv` exists:
   - **If missing**: Create file with CSV headers (timestamp, url, status_code, response_time_ms, is_up)
   - **If exists**: Open in append mode
2. For each check result from Step 1:
   - Write row to CSV with all fields
3. Close file (ensure data is flushed to disk)
4. Verify write succeeded (file size increased)

**Tool**: `tools/log_results.py`

**Decision point**: **If CSV file is locked or write fails**:
- **Action**: Retry once after 2-second delay
- **If retry fails**: Raise exception (MUST NOT lose data)

**Failure mode**: File write error (permissions, disk full, file locked)
**Fallback**: Retry once, then fail workflow with clear error message. Data loss is unacceptable — fail loudly.

---

## Step 3: Send Alerts (Optional)

Send Telegram alerts for any sites that are down. Only runs if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured.

**Delegate to:** `alert-specialist` subagent

1. Check if Telegram credentials are configured:
   - **If missing**: Skip this step silently (log "Telegram not configured")
   - **If present**: Continue to alert logic
2. Filter check results to only down sites (is_up == false)
3. **If no down sites**: Skip alert sending, log "All sites up"
4. **If down sites exist**:
   - For each down site:
     - Format alert message with URL, status code, timestamp
     - Send via Telegram Bot API
     - Log success or failure
5. Return summary of alerts sent

**Tool**: `tools/telegram_alert.py`

**Decision point**: **If Telegram API call fails (rate limit, network error, invalid token)**:
- **Action**: Log error to stderr, continue workflow
- **Do NOT fail workflow**: Alerting is enhancement, not requirement

**Failure mode**: Telegram API unreachable or returns error
**Fallback**: Log error, skip alerts, continue workflow. Monitoring data is still logged and committed.

---

## Step 4: Commit Results

Stage CSV file and commit to repository with descriptive message.

**No subagent delegation** — Main agent uses git CLI directly

1. Configure git identity (github-actions bot)
2. Stage ONLY `logs/uptime_log.csv` (never `git add -A`)
3. Create commit with message format: `chore(uptime): log check results [timestamp]`
4. Pull with rebase (handle rare concurrent commits)
5. Push to origin/main
6. Verify push succeeded

**Tool**: `git` CLI via GitHub Actions

**Decision point**: **If git push fails (conflict, network error)**:
- **Action**: Pull with rebase and retry push up to 3 times
- **If all retries fail**: Fail workflow (prevents data loss on next run)

**Failure mode**: Git push conflict or network failure
**Fallback**: Retry with backoff. GitHub Actions concurrency setting prevents simultaneous runs, making conflicts rare.

---

## Notes

### Execution Paths

This system supports three execution paths:

1. **Scheduled cron** (primary): Runs every 5 minutes via GitHub Actions schedule trigger
2. **Manual dispatch**: Trigger via GitHub Actions UI or API for testing
3. **Local CLI** (development): Run tools directly with Python for testing

### Cost Considerations

- **GitHub Actions**: ~1,440 minutes/month for 5-minute checks (well within 2,000/month free tier)
- **Storage**: CSV file grows ~150 bytes per check = ~6.5 MB/month (negligible)
- **No LLM costs**: This is a pure monitoring system, no AI calls

### MCP Dependencies

**None**. This system uses only:
- Python stdlib (`csv`, `json`, `pathlib`, `argparse`, `logging`)
- `requests` library for HTTP
- `git` CLI (standard in GitHub Actions)

### Character

This is a **simple, reliable, unglamorous monitoring system**. No fancy features, no complex logic, just:
- Check URLs
- Log results
- Commit to Git
- Optionally alert

The simplicity is the feature. Git history IS the monitoring dashboard.

### Failure Philosophy

- **Data logging failures halt the workflow** — never lose monitoring data
- **Alert failures do NOT halt the workflow** — monitoring continues even if alerts fail
- **Per-URL error isolation** — one failed check doesn't prevent logging others

### Extensibility

To add more URLs, edit `.github/workflows/monitor.yml` and update the `--urls` argument.
To add authentication, modify `tools/monitor.py` to accept auth headers via GitHub Secrets.
To change check frequency, edit the cron expression in the workflow file.
