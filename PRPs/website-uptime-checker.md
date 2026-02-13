name: "Website Uptime Checker"
description: |
  Monitors website availability and logs uptime history to Git-versioned CSV files

## Purpose
WAT System PRP (Product Requirements Prompt) — a structured blueprint that gives the factory enough context to build a complete, working system in one pass.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a GitHub Actions-powered website uptime monitoring system that checks two websites (https://google.com and https://github.com) every 5 minutes, logs all results to a Git-versioned CSV file, and optionally sends Telegram alerts when a site goes down. The system must be simple, reliable, and run autonomously without external infrastructure.

## Why
- **Visibility**: Track website uptime history over time with Git-backed audit trail
- **Reliability**: Catch outages immediately without relying on expensive SaaS monitoring
- **Simplicity**: No external database, no complex setup — just GitHub Actions + CSV + Git
- **Auditability**: Every check is a commit; full history is queryable via Git
- **Cost**: Free tier covers ~8,640 checks/day (3 sites × 288 checks/day) with room to grow

## What
A monitoring system that performs HTTP GET requests to configured URLs every 5 minutes, measures response times, determines up/down status, appends results to a CSV log file, and commits changes to the repository. Optionally sends Telegram notifications when a site transitions from up to down.

### Success Criteria
- [ ] System checks https://google.com and https://github.com every 5 minutes via GitHub Actions cron
- [ ] Each check logs: timestamp, URL, status_code, response_time_ms, up/down status to CSV
- [ ] CSV file is committed to the repo after each check (or batch of checks)
- [ ] Manual workflow_dispatch trigger works for testing
- [ ] CLI execution works locally for development
- [ ] Telegram alert sent when a site goes down (optional enhancement)
- [ ] System runs autonomously via GitHub Actions on schedule
- [ ] Results are committed back to repo
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs
[What goes into the system. Be specific about format, source, and any validation requirements.]

```yaml
- name: "urls"
  type: "list of strings"
  source: "hardcoded in workflow YAML or config file"
  required: true
  description: "List of URLs to monitor"
  example: ["https://google.com", "https://github.com"]

- name: "telegram_chat_id"
  type: "string"
  source: "GitHub Secret TELEGRAM_CHAT_ID"
  required: false
  description: "Telegram chat ID for alerts (optional)"
  example: "123456789"

- name: "telegram_bot_token"
  type: "string"
  source: "GitHub Secret TELEGRAM_BOT_TOKEN"
  required: false
  description: "Telegram bot token for sending alerts (optional)"
  example: "<your-bot-token-from-botfather>"
```

## Outputs
[What comes out of the system. Where do results go?]

```yaml
- name: "uptime_log.csv"
  type: "CSV file"
  destination: "logs/uptime_log.csv (committed to repo)"
  description: "Append-only CSV with columns: timestamp, url, status_code, response_time_ms, is_up"
  example: |
    timestamp,url,status_code,response_time_ms,is_up
    2026-02-13T11:33:00Z,https://google.com,200,145,true
    2026-02-13T11:33:01Z,https://github.com,200,203,true

- name: "telegram_alert"
  type: "Telegram message"
  destination: "Telegram chat (if configured)"
  description: "Alert message sent when site goes down"
  example: "⚠️ ALERT: https://google.com is DOWN (status: 0, no response after 30s timeout)"
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- doc: "config/mcp_registry.md"
  why: "Check Telegram MCP availability and fallback options"

- doc: "library/patterns.md"
  why: "Select Monitor > Detect > Alert pattern, simplified to Monitor > Log"

- doc: "library/tool_catalog.md"
  why: "Reference rest_client and csv_read_write patterns"

- url: "https://docs.python-requests.org/en/latest/user/quickstart/"
  why: "HTTP GET with timeout, exception handling, response time measurement"

- url: "https://core.telegram.org/bots/api#sendmessage"
  why: "Telegram sendMessage API format (fallback if MCP unavailable)"
```

### Workflow Pattern Selection
```yaml
pattern: "Monitor > Log (simplified from Monitor > Detect > Alert)"
rationale: |
  Traditional "Monitor > Detect > Alert" checks for *changes* and only alerts on transitions.
  This system logs *every check* regardless of status, creating a full audit trail.
  Alert functionality is optional.
  
  Key differences from pattern:
  - No state comparison (all checks are logged, not just changes)
  - No "detect" phase (up/down is binary: HTTP 200-299 = up, else = down)
  - Alert is enhancement, not core feature
  
modifications: |
  - Append-only CSV logging (no state file needed)
  - Git commit IS the persistence mechanism
  - Alert on down status (not just state change) — can be added later
  - Simple exit code signaling: tool exits 1 if any site is down
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "HTTP requests"
    primary_mcp: "fetch"
    alternative_mcp: "none"
    fallback: "Python requests library (simpler, more reliable for basic GET)"
    secret_name: "none"

  - name: "CSV append"
    primary_mcp: "filesystem"
    alternative_mcp: "none"
    fallback: "Python csv module (stdlib, no dependencies)"
    secret_name: "none"

  - name: "Telegram notifications"
    primary_mcp: "telegram"
    alternative_mcp: "none"
    fallback: "Telegram Bot API via HTTP POST (requests library)"
    secret_name: "TELEGRAM_BOT_TOKEN"
    additional_secret: "TELEGRAM_CHAT_ID"

  - name: "Git commit"
    primary_mcp: "git"
    alternative_mcp: "none"
    fallback: "git CLI via subprocess (standard in GitHub Actions)"
    secret_name: "GITHUB_TOKEN (automatic in Actions)"
```

### Known Gotchas & Constraints
```
# CRITICAL: GitHub Actions cron is not exact — has ±5 minute variance
# CRITICAL: Requests library timeout must be set (default is infinite)
# CRITICAL: CSV must handle concurrent writes (file locking or GitHub Actions concurrency limit)
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: Git commit must be atomic — stage ONLY the CSV file, not all changes
# CRITICAL: Response time measurement must use time.monotonic() (not time.time()) for accuracy
# CRITICAL: Tool must exit 0 if all sites up, exit 1 if any site down (for GitHub Actions UI)
# CRITICAL: CSV headers must be written if file doesn't exist
# CRITICAL: URLs must include scheme (https://) — requests requires it
# CRITICAL: Status code 0 means connection failed (timeout, DNS error, refused)
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents:
  - name: "monitoring-specialist"
    description: "Delegate when checking website availability, measuring response times, or handling HTTP requests"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Perform HTTP GET requests to target URLs"
      - "Measure response times accurately"
      - "Determine up/down status based on HTTP status codes"
      - "Handle connection timeouts and DNS failures gracefully"
    inputs: "List of URLs to check"
    outputs: "List of check results (timestamp, url, status_code, response_time, is_up)"

  - name: "data-logger-specialist"
    description: "Delegate when appending data to CSV files or managing log file structure"
    tools: "Read, Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Create CSV file with headers if it doesn't exist"
      - "Append new check results to CSV in correct format"
      - "Ensure CSV structure remains valid (no corrupted rows)"
      - "Handle file I/O errors gracefully"
    inputs: "List of check results from monitoring-specialist"
    outputs: "Updated CSV file at logs/uptime_log.csv"

  - name: "alert-specialist"
    description: "Delegate when sending Telegram notifications or handling external alerts (optional, for future enhancement)"
    tools: "Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Send Telegram message when a site goes down"
      - "Format alert message with URL, status, and timestamp"
      - "Handle Telegram API errors gracefully (log but don't fail workflow)"
    inputs: "Down sites list (URL, status_code, timestamp)"
    outputs: "Telegram message sent (or error logged if fails)"
```

### Agent Teams Analysis
```yaml
independent_tasks: []  # Only 2 URLs — not enough to justify Agent Teams overhead

independent_task_count: 0
recommendation: "Sequential execution"
rationale: |
  Two HTTP checks take ~2-4 seconds total (assuming 200-300ms per check + 1s timeout buffer).
  Agent Teams overhead (spawning teammates, merging results) would add 5-10 seconds.
  Sequential execution is faster AND simpler for this use case.
  
  If the URL list grows to 10+, consider Agent Teams parallelization.

sequential_rationale: |
  - Only 2 URLs to check (google.com, github.com)
  - Each check is fast (~200-500ms expected)
  - Total sequential time: ~2-4 seconds
  - Agent Teams setup/teardown would exceed the time saved
  - No data dependencies between checks (but results are collected in one list)
  - Simplicity > premature optimization
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "*/5 * * * *"
    description: "Run every 5 minutes (GitHub Actions cron)"

  - type: "workflow_dispatch"
    config: "No inputs required (URLs hardcoded or in config)"
    description: "Manual trigger for testing"

  - type: "repository_dispatch (optional)"
    config: "Event type: 'check-uptime'"
    description: "External trigger via webhook (for Agent HQ integration)"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "Check Websites"
    description: "Perform HTTP GET requests to each configured URL and measure response times"
    subagent: "monitoring-specialist"
    tools: ["monitor.py"]
    inputs: "List of URLs (from workflow YAML or config.json)"
    outputs: "List of check results: [{timestamp, url, status_code, response_time_ms, is_up}, ...]"
    failure_mode: "Connection timeout, DNS failure, network error"
    fallback: "Record status_code=0, is_up=false, response_time=-1 for failed checks"

  - name: "Log Results"
    description: "Append check results to CSV log file, creating file with headers if it doesn't exist"
    subagent: "data-logger-specialist"
    tools: ["log_results.py"]
    inputs: "Check results list from Step 1"
    outputs: "Updated logs/uptime_log.csv"
    failure_mode: "File write error, permissions issue, disk full"
    fallback: "Log error to stderr, fail workflow (must not lose data)"

  - name: "Send Alerts (Optional)"
    description: "Send Telegram alerts for any sites that are down"
    subagent: "alert-specialist"
    tools: ["telegram_alert.py"]
    inputs: "Filtered list of down sites from Step 1"
    outputs: "Telegram messages sent (one per down site)"
    failure_mode: "Telegram API error, rate limit, invalid token"
    fallback: "Log error to stderr, continue workflow (don't fail on alert failure)"

  - name: "Commit Results"
    description: "Stage CSV file and commit to repository"
    subagent: "none (main agent via git CLI)"
    tools: ["git CLI"]
    inputs: "logs/uptime_log.csv"
    outputs: "Git commit with message 'chore(uptime): log check results [timestamp]'"
    failure_mode: "Git push conflict, network error"
    fallback: "Retry push with rebase (GitHub Actions concurrency handles this)"
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "monitor.py"
    purpose: "Check website availability and measure response time"
    catalog_pattern: "rest_client (simplified — no retry, just timeout)"
    inputs:
      - "urls: list[str] — URLs to check (with scheme, e.g. https://example.com)"
      - "timeout: int = 30 — HTTP request timeout in seconds"
    outputs: "JSON list of check results: [{timestamp, url, status_code, response_time_ms, is_up}, ...]"
    dependencies: ["requests"]
    mcp_used: "none (direct requests library)"
    error_handling: "Catch requests.RequestException, record status_code=0, continue to next URL"

  - name: "log_results.py"
    purpose: "Append check results to CSV file"
    catalog_pattern: "csv_read_write (write-only, append mode)"
    inputs:
      - "results: list[dict] — Check results from monitor.py"
      - "log_file: str = 'logs/uptime_log.csv' — CSV file path"
    outputs: "CSV file updated with new rows"
    dependencies: []  # stdlib only (csv, pathlib)
    mcp_used: "none (direct csv module)"
    error_handling: "Create file with headers if doesn't exist; raise exception on write failure"

  - name: "telegram_alert.py"
    purpose: "Send Telegram alert when a site is down"
    catalog_pattern: "slack_notify (adapted for Telegram)"
    inputs:
      - "down_sites: list[dict] — Sites that are down (filtered from check results)"
      - "bot_token: str — Telegram bot token (from env var)"
      - "chat_id: str — Telegram chat ID (from env var)"
    outputs: "Telegram messages sent (or error logged)"
    dependencies: ["requests"]
    mcp_used: "none (Telegram Bot API via HTTP)"
    error_handling: "Catch requests.RequestException, log error, return success=false (don't fail workflow)"
```

### Per-Tool Pseudocode
```python
# monitor.py
"""
Website uptime monitor tool.

Performs HTTP GET requests to configured URLs and measures response times.
Returns structured JSON with check results for each URL.
"""
import argparse
import json
import logging
import sys
import time
from typing import Any
from datetime import datetime, timezone

import requests

def check_url(url: str, timeout: int = 30) -> dict[str, Any]:
    """
    Check a single URL and return status information.
    
    Returns dict with:
    - timestamp: ISO 8601 timestamp
    - url: the URL checked
    - status_code: HTTP status code (0 if connection failed)
    - response_time_ms: response time in milliseconds (-1 if failed)
    - is_up: bool (true if status code 200-299)
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        start = time.monotonic()
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = (time.monotonic() - start) * 1000  # convert to ms
        
        return {
            "timestamp": timestamp,
            "url": url,
            "status_code": resp.status_code,
            "response_time_ms": round(elapsed, 2),
            "is_up": 200 <= resp.status_code < 300,
        }
    except requests.RequestException as exc:
        logging.error(f"Failed to check {url}: {exc}")
        return {
            "timestamp": timestamp,
            "url": url,
            "status_code": 0,
            "response_time_ms": -1,
            "is_up": False,
        }

def main():
    parser = argparse.ArgumentParser(description="Monitor website uptime")
    parser.add_argument("--urls", nargs="+", required=True, help="URLs to check")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout (seconds)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    results = []
    any_down = False
    
    for url in args.urls:
        logging.info(f"Checking {url}...")
        result = check_url(url, timeout=args.timeout)
        results.append(result)
        
        if not result["is_up"]:
            any_down = True
            logging.warning(f"{url} is DOWN (status: {result['status_code']})")
        else:
            logging.info(f"{url} is UP ({result['response_time_ms']}ms)")
    
    # Output results as JSON to stdout
    print(json.dumps(results, indent=2))
    
    # Exit code: 0 if all up, 1 if any down (for GitHub Actions UI)
    sys.exit(1 if any_down else 0)

if __name__ == "__main__":
    main()


# log_results.py
"""
CSV logging tool for uptime check results.

Appends check results to a CSV file, creating it with headers if it doesn't exist.
"""
import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

FIELDNAMES = ["timestamp", "url", "status_code", "response_time_ms", "is_up"]

def append_results(log_file: Path, results: list[dict[str, Any]]) -> None:
    """Append check results to CSV file."""
    # Create parent directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and has content
    file_exists = log_file.exists() and log_file.stat().st_size > 0
    
    # Open in append mode, write header if new file
    with log_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        
        if not file_exists:
            writer.writeheader()
            logging.info(f"Created new log file: {log_file}")
        
        for result in results:
            writer.writerow(result)
        
        logging.info(f"Appended {len(results)} rows to {log_file}")

def main():
    parser = argparse.ArgumentParser(description="Log uptime check results to CSV")
    parser.add_argument("--results", required=True, help="JSON file or string with check results")
    parser.add_argument("--log-file", default="logs/uptime_log.csv", help="CSV log file path")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Parse results (from file or JSON string)
    try:
        results_path = Path(args.results)
        if results_path.exists():
            results = json.loads(results_path.read_text())
        else:
            results = json.loads(args.results)
    except Exception as exc:
        logging.error(f"Failed to parse results: {exc}")
        sys.exit(1)
    
    # Append to log file
    try:
        log_path = Path(args.log_file)
        append_results(log_path, results)
    except Exception as exc:
        logging.error(f"Failed to write log file: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()


# telegram_alert.py
"""
Telegram alert tool for website downtime notifications.

Sends Telegram messages when monitored sites go down.
Optional: only runs if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.
"""
import argparse
import json
import logging
import os
import sys
from typing import Any

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

def send_alert(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Send a Telegram message.
    
    Returns True on success, False on failure.
    """
    url = TELEGRAM_API.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logging.info("Telegram alert sent successfully")
        return True
    except requests.RequestException as exc:
        logging.error(f"Failed to send Telegram alert: {exc}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Send Telegram alerts for down sites")
    parser.add_argument("--results", required=True, help="JSON file or string with check results")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Get credentials from environment
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        logging.info("Telegram credentials not configured, skipping alerts")
        sys.exit(0)
    
    # Parse results
    try:
        results_path = Path(args.results)
        if results_path.exists():
            results = json.loads(results_path.read_text())
        else:
            results = json.loads(args.results)
    except Exception as exc:
        logging.error(f"Failed to parse results: {exc}")
        sys.exit(1)
    
    # Filter down sites
    down_sites = [r for r in results if not r["is_up"]]
    
    if not down_sites:
        logging.info("All sites are up, no alerts needed")
        sys.exit(0)
    
    # Send alert for each down site
    for site in down_sites:
        status_msg = f"status code {site['status_code']}" if site["status_code"] > 0 else "connection failed"
        message = (
            f"⚠️ <b>WEBSITE DOWN ALERT</b>\n\n"
            f"<b>URL:</b> {site['url']}\n"
            f"<b>Status:</b> {status_msg}\n"
            f"<b>Timestamp:</b> {site['timestamp']}\n"
        )
        send_alert(bot_token, chat_id, message)
    
    logging.info(f"Sent {len(down_sites)} alert(s)")

if __name__ == "__main__":
    main()
```

### Integration Points
```yaml
SECRETS:
  - name: "TELEGRAM_BOT_TOKEN"
    purpose: "Telegram Bot API authentication (optional)"
    required: false

  - name: "TELEGRAM_CHAT_ID"
    purpose: "Telegram chat ID for alerts (optional)"
    required: false

  - name: "GITHUB_TOKEN"
    purpose: "GitHub API authentication for git push (automatic in Actions)"
    required: true (automatic in GitHub Actions)

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "TELEGRAM_BOT_TOKEN=your_bot_token_here  # Optional: Telegram bot token from @BotFather"
      - "TELEGRAM_CHAT_ID=your_chat_id_here      # Optional: Telegram chat ID for alerts"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "requests==2.31.0  # HTTP client for checks and Telegram API"

GITHUB_ACTIONS:
  - trigger: "schedule"
    config: |
      on:
        schedule:
          - cron: '*/5 * * * *'  # Every 5 minutes
        workflow_dispatch:        # Manual trigger
      
      jobs:
        monitor:
          runs-on: ubuntu-latest
          timeout-minutes: 5
          concurrency:
            group: uptime-monitor
            cancel-in-progress: false
          
          steps:
            - uses: actions/checkout@v4
            
            - name: Set up Python
              uses: actions/setup-python@v5
              with:
                python-version: '3.11'
            
            - name: Install dependencies
              run: pip install -r requirements.txt
            
            - name: Check websites
              id: check
              continue-on-error: true  # Don't fail workflow if sites are down
              run: |
                python tools/monitor.py \
                  --urls https://google.com https://github.com \
                  --timeout 30 > /tmp/results.json
            
            - name: Log results
              run: |
                python tools/log_results.py \
                  --results /tmp/results.json \
                  --log-file logs/uptime_log.csv
            
            - name: Send alerts
              if: steps.check.outcome == 'failure'
              env:
                TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
                TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
              run: |
                python tools/telegram_alert.py --results /tmp/results.json
            
            - name: Commit results
              run: |
                git config user.name "github-actions[bot]"
                git config user.email "github-actions[bot]@users.noreply.github.com"
                git add logs/uptime_log.csv
                git commit -m "chore(uptime): log check results $(date -u +%Y-%m-%dT%H:%M:%SZ)" || echo "No changes"
                git pull --rebase origin main || true
                git push
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# monitor.py
python -c "import ast; ast.parse(open('tools/monitor.py').read())"
python -c "import importlib; importlib.import_module('tools.monitor')"
python -c "from tools.monitor import main; assert callable(main)"

# log_results.py
python -c "import ast; ast.parse(open('tools/log_results.py').read())"
python -c "import importlib; importlib.import_module('tools.log_results')"
python -c "from tools.log_results import main; assert callable(main)"

# telegram_alert.py
python -c "import ast; ast.parse(open('tools/telegram_alert.py').read())"
python -c "import importlib; importlib.import_module('tools.telegram_alert')"
python -c "from tools.telegram_alert import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Test monitor.py with real URLs
python tools/monitor.py --urls https://google.com https://github.com --timeout 10 > /tmp/test_results.json
# Expected: JSON array with 2 objects, each with timestamp, url, status_code, response_time_ms, is_up
cat /tmp/test_results.json | python -c "
import json, sys
data = json.load(sys.stdin)
assert len(data) == 2, 'Expected 2 results'
assert all('timestamp' in r and 'url' in r and 'status_code' in r for r in data), 'Missing fields'
print('monitor.py test PASSED')
"

# Test log_results.py with sample data
echo '[{"timestamp":"2026-02-13T11:33:00Z","url":"https://google.com","status_code":200,"response_time_ms":145,"is_up":true}]' > /tmp/sample_results.json
python tools/log_results.py --results /tmp/sample_results.json --log-file /tmp/test_log.csv
# Expected: CSV file created with header and 1 data row
test -f /tmp/test_log.csv && echo "log_results.py test PASSED" || echo "log_results.py test FAILED"

# Test telegram_alert.py without credentials (should skip gracefully)
python tools/telegram_alert.py --results /tmp/sample_results.json
# Expected: Exits 0 with message "Telegram credentials not configured, skipping alerts"
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline

# Full pipeline test
echo "Running full integration test..."

# Step 1: Check URLs
python tools/monitor.py --urls https://google.com https://github.com > /tmp/int_results.json
echo "✓ Step 1: Monitor completed"

# Step 2: Log results
python tools/log_results.py --results /tmp/int_results.json --log-file /tmp/int_log.csv
echo "✓ Step 2: Logging completed"

# Step 3: Verify CSV structure
python -c "
import csv
with open('/tmp/int_log.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    assert len(rows) >= 2, 'Expected at least 2 rows in log'
    assert all(k in rows[0] for k in ['timestamp', 'url', 'status_code', 'response_time_ms', 'is_up']), 'Missing expected columns'
print('✓ Step 3: CSV validation passed')
"

# Step 4: Verify workflow.md references match actual files
test -f tools/monitor.py && echo "✓ monitor.py exists"
test -f tools/log_results.py && echo "✓ log_results.py exists"
test -f tools/telegram_alert.py && echo "✓ telegram_alert.py exists"

echo "Integration test PASSED"
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes and failure notifications
- [ ] .env.example lists all required environment variables
- [ ] .gitignore excludes .env, __pycache__/, credentials
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env
- Do not use `git add -A` or `git add .` — stage only logs/uptime_log.csv
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types (requests.RequestException)
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks — use requests library directly
- Do not design subagents that call other subagents — only the main agent delegates
- Do not use Agent Teams when fewer than 3 independent tasks exist — 2 URLs = sequential
- Do not commit .env files, credentials, or API keys to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not use `git add -A` in the GitHub Actions workflow — only `git add logs/uptime_log.csv`

---

## Confidence Score: 9/10

**Score rationale:**
- **Requirements clarity**: High confidence — problem is specific and well-defined (check 2 URLs every 5 minutes, log to CSV)
- **Technical feasibility**: High confidence — simple HTTP GET + CSV append, no complex APIs or processing
- **Tool patterns**: High confidence — rest_client and csv_read_write patterns from catalog are directly applicable
- **MCP availability**: High confidence — Telegram MCP exists, but fallback to HTTP API is trivial
- **Validation**: High confidence — all validation steps are executable with real URLs (google.com, github.com)
- **Edge cases**: Medium-high confidence — timeout, DNS failure, network errors are handled; CSV append is atomic
- **GitHub Actions**: High confidence — cron trigger is straightforward, concurrency prevents conflicts
- **Minimal dependencies**: High confidence — only `requests` library needed (well-documented, stable)
- **Deduction (-1)**: GitHub Actions cron has ±5 min variance — documented as expected behavior, not a bug

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — all requirements are clear

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/website-uptime-checker.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
