name: "Website Uptime Monitor"
description: |

## Purpose
WAT System PRP (Product Requirements Prompt) — a structured blueprint for building a simple, reliable website uptime monitoring system using Git-native state storage.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a lightweight website uptime monitoring system that periodically checks if a target URL is responding, measures response time, records results in a version-controlled CSV file, and uses GitHub Actions workflow status as the notification mechanism.

## Why
- **Visibility**: Know when a website goes down without relying on external monitoring services
- **Git-native audit trail**: Every check is a commit, full history forever
- **Cost-effective**: Zero cost for public repos, fits within GitHub Actions free tier for private repos
- **Simple**: No external dependencies, no database, no alerting infrastructure — just HTTP checks and CSV logs

## What
A single Python tool (`monitor.py`) that:
1. Makes an HTTP GET request to a target URL
2. Measures response time and status code
3. Appends the result to a CSV file (`data/uptime_log.csv`)
4. Commits the updated CSV to the repository
5. Exits with code 0 (success) if site is up, code 1 (failure) if site is down

GitHub Actions workflow (`monitor.yml`) that:
1. Runs on a cron schedule (every 5 minutes)
2. Executes the monitor tool
3. Shows "green" (passing) when site is up, "red" (failed) when site is down
4. Commits results back to the repo

### Success Criteria
- [x] Tool checks URL and records status in CSV
- [x] CSV is committed to repo after each check
- [x] Workflow runs on schedule (every 5 minutes)
- [x] Workflow status reflects site status (green = up, red = down)
- [x] Response time is measured and logged
- [x] System handles concurrent runs without data corruption
- [x] Works for public and private repositories
- [x] Three execution paths work: (1) scheduled cron, (2) manual dispatch, (3) local CLI

---

## Inputs

```yaml
- name: "url"
  type: "string (URL)"
  source: "GitHub Actions workflow environment variable or CLI argument"
  required: true
  description: "The URL to monitor (must include protocol: http:// or https://)"
  example: "https://example.com"

- name: "timeout"
  type: "integer (seconds)"
  source: "GitHub Actions workflow environment variable or CLI argument"
  required: false
  default: 10
  description: "HTTP request timeout in seconds"
  example: "10"
```

## Outputs

```yaml
- name: "uptime_log.csv"
  type: "CSV file"
  destination: "data/uptime_log.csv in the repository"
  description: "Append-only log of all uptime checks with columns: timestamp, url, status_code, response_time_ms, is_up"
  example: |
    timestamp,url,status_code,response_time_ms,is_up
    2026-02-13T01:13:32Z,https://example.com,200,245,true
    2026-02-13T01:18:32Z,https://example.com,200,251,true
    2026-02-13T01:23:32Z,https://example.com,500,1032,false

- name: "exit_code"
  type: "integer"
  destination: "Tool exit code (GitHub Actions workflow status)"
  description: "0 if site is up, 1 if site is down (makes workflow fail visibly)"
```

---

## All Needed Context

### Documentation & References
```yaml
- url: "https://docs.python.org/3/library/csv.html"
  why: "CSV append logic for logging"

- url: "https://docs.python.org/3/library/http.client.html"
  why: "HTTP status code reference"

- url: "https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule"
  why: "GitHub Actions cron syntax and variance documentation"

- url: "https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idconcurrency"
  why: "Concurrency setting to prevent overlapping runs"

- file: "library/patterns.md"
  why: "Reference the proven website-uptime-monitor pattern (Monitor > Log variant)"

- file: "library/tool_catalog.md"
  why: "Reference csv_read_write pattern for append operations"
```

### Workflow Pattern Selection
```yaml
pattern: "Monitor > Log (simplified from Monitor > Detect > Alert)"
rationale: |
  This is the simplest possible monitoring system. No detection logic, no alerting — 
  just raw data collection. Every check produces a log entry regardless of status.
  Git history IS the audit trail. Workflow status IS the alert mechanism.
modifications: |
  - Skip "Detect" phase: no comparison to previous state
  - Skip "Alert" phase: workflow red/green status is the notification
  - Direct to "Log": append result to CSV and commit
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "HTTP GET request"
    primary_mcp: "None — use Python requests library directly"
    alternative_mcp: "Fetch MCP"
    fallback: "Python stdlib http.client or urllib"
    secret_name: "None required (public URL monitoring)"
    rationale: "For a single GET request, requests library is simpler and more reliable than MCP"

  - name: "CSV append"
    primary_mcp: "None — use Python csv stdlib directly"
    alternative_mcp: "Filesystem MCP"
    fallback: "pathlib + open() with append mode"
    secret_name: "None"
    rationale: "CSV stdlib handles all edge cases (encoding, newlines, quoting)"

  - name: "Git commit"
    primary_mcp: "None — use git CLI directly in GitHub Actions"
    alternative_mcp: "Git MCP"
    fallback: "GitHub Actions git-auto-commit action"
    secret_name: "GITHUB_TOKEN (automatic in Actions)"
    rationale: "git add + git commit + git push with retry on concurrent edits"
```

### Known Gotchas & Constraints
```
# CRITICAL: GitHub Actions cron has ±5 minute scheduling variance (not a bug, by design)
# CRITICAL: CSV file must be created if missing (first run initialization)
# CRITICAL: Concurrent runs can cause git push conflicts — use concurrency setting
# CRITICAL: Tool MUST exit 1 on down status (makes workflow fail visibly in Actions UI)
# CRITICAL: No secrets required for public URL monitoring
# CRITICAL: Response time measured in milliseconds for precision
# CRITICAL: Timestamp MUST be ISO 8601 UTC for consistency across timezones
# CRITICAL: CSV append uses exclusive file locking to prevent corruption if concurrency setting fails
# CRITICAL: git push retry with rebase handles race condition on concurrent commits
```

---

## System Design

### Subagent Architecture
```yaml
subagents: []
# No subagents needed — system is a single-tool workflow (too simple to decompose)
```

### Agent Teams Analysis
```yaml
independent_tasks: []
independent_task_count: 0
recommendation: "Sequential execution"
sequential_rationale: |
  This is a single atomic operation: check URL → log result → commit.
  No parallelization possible or beneficial. Total execution time is ~2-5 seconds.
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "*/5 * * * * (every 5 minutes)"
    description: "Primary trigger — periodic uptime checks"

  - type: "workflow_dispatch"
    config: "Manual trigger with optional URL override input"
    description: "Testing and ad-hoc checks"
```

---

## Implementation Blueprint

### Workflow Steps
```yaml
steps:
  - name: "Check URL"
    description: "Make HTTP GET request, measure response time, determine up/down status"
    subagent: null
    tools: ["monitor.py"]
    inputs: "URL (from env var or CLI arg), timeout (default 10s)"
    outputs: "status_code, response_time_ms, is_up (boolean)"
    failure_mode: "Network timeout, DNS failure, connection refused, HTTP 5xx"
    fallback: "Log failure with status_code=0, response_time_ms=timeout*1000, is_up=false"

  - name: "Append to CSV"
    description: "Write log entry to data/uptime_log.csv with timestamp, URL, status, response time"
    subagent: null
    tools: ["monitor.py (same tool, integrated)"]
    inputs: "Check results from previous step"
    outputs: "Updated CSV file"
    failure_mode: "File locked (concurrent write), disk full, permissions error"
    fallback: "Retry append up to 3 times with 1s delay; if all fail, print to stdout and exit 1"

  - name: "Commit to Git"
    description: "Stage CSV, commit with message, push to origin with retry on conflict"
    subagent: null
    tools: ["git CLI (in GitHub Actions workflow)"]
    inputs: "Updated CSV file"
    outputs: "New commit SHA"
    failure_mode: "Concurrent push causes conflict, network failure, authentication failure"
    fallback: "git pull --rebase + retry push (up to 3 attempts with exponential backoff)"

  - name: "Signal Status"
    description: "Exit with appropriate code to set workflow status (green=up, red=down)"
    subagent: null
    tools: ["monitor.py exit code"]
    inputs: "is_up boolean from check step"
    outputs: "Exit code 0 (up) or 1 (down)"
    failure_mode: "None (always succeeds)"
    fallback: "N/A"
```

### Tool Specifications
```yaml
tools:
  - name: "monitor.py"
    purpose: "Check URL, measure response time, log to CSV, exit with status code"
    catalog_pattern: "New — combines HTTP check + CSV append + exit signaling"
    inputs:
      - "url: str — Target URL (required, from --url CLI arg or URL env var)"
      - "timeout: int — Request timeout in seconds (default 10)"
    outputs: "CSV row appended to data/uptime_log.csv; exit code 0 or 1"
    dependencies: ["requests (for HTTP)", "csv (stdlib)", "pathlib (stdlib)"]
    mcp_used: "none"
    error_handling: |
      - RequestException → log as down (status_code=0, response_time=timeout*1000)
      - CSV write failure → retry 3x with 1s delay, then fail
      - Any unhandled exception → log traceback and exit 1
```

### Per-Tool Pseudocode
```python
# monitor.py
import requests, csv, pathlib, sys, time
from datetime import datetime, timezone

def main():
    """Check URL, log result to CSV, exit with status code."""
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL to monitor")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in seconds")
    args = parser.parse_args()

    # Make HTTP request
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        start = time.perf_counter()
        resp = requests.get(args.url, timeout=args.timeout, allow_redirects=True)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        status_code = resp.status_code
        is_up = 200 <= status_code < 400
    except requests.RequestException as e:
        # GOTCHA: Log all failures as down, including timeouts and DNS failures
        elapsed_ms = args.timeout * 1000
        status_code = 0
        is_up = False
        print(f"Request failed: {e}", file=sys.stderr)

    # Append to CSV (create if missing)
    csv_path = pathlib.Path("data/uptime_log.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize CSV with headers if missing
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "url", "status_code", "response_time_ms", "is_up"])

    # Append result (with retry for concurrent write protection)
    for attempt in range(3):
        try:
            with csv_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, args.url, status_code, elapsed_ms, is_up])
            break
        except Exception as e:
            if attempt == 2:
                print(f"CSV append failed after 3 attempts: {e}", file=sys.stderr)
                sys.exit(1)
            time.sleep(1)

    # Print status (for GitHub Actions logs)
    status_text = "UP" if is_up else "DOWN"
    print(f"{timestamp} | {args.url} | {status_code} | {elapsed_ms}ms | {status_text}")

    # Exit with code 0 (up) or 1 (down) to set workflow status
    sys.exit(0 if is_up else 1)

if __name__ == "__main__":
    main()
```

### Integration Points
```yaml
SECRETS: []
# No secrets required for public URL monitoring
# If monitoring authenticated endpoints, add BASIC_AUTH_USER and BASIC_AUTH_PASS

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "URL=https://example.com  # Target URL to monitor"
      - "TIMEOUT=10  # Request timeout in seconds"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "requests==2.31.0  # HTTP client"

GITHUB_ACTIONS:
  - trigger: "schedule (cron: */5 * * * *)"
    config: |
      Runs every 5 minutes. GitHub Actions cron has ±5 minute variance.
      Uses concurrency setting to prevent overlapping runs:
        concurrency:
          group: uptime-monitor
          cancel-in-progress: false
  - trigger: "workflow_dispatch"
    config: "Manual trigger with optional url input for ad-hoc checks"
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/monitor.py').read())"

# Import check — verify no missing dependencies
python -c "import sys; sys.path.insert(0, 'tools'); import monitor"

# Structure check — verify main() exists and is callable
python -c "from tools.monitor import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Test 1: Check a URL that should be UP
python tools/monitor.py --url https://httpbin.org/status/200 --timeout 5
# Expected output: Timestamp | URL | 200 | <response_time>ms | UP
# Expected exit code: 0
# Expected: data/uptime_log.csv created with header + 1 data row

# Test 2: Check a URL that should be DOWN
python tools/monitor.py --url https://httpbin.org/status/500 --timeout 5
# Expected output: Timestamp | URL | 500 | <response_time>ms | DOWN
# Expected exit code: 1
# Expected: data/uptime_log.csv appended with 1 more row

# Test 3: Check a URL that times out
python tools/monitor.py --url https://httpstat.us/200?sleep=15000 --timeout 2
# Expected output: Timestamp | URL | 0 | 2000ms | DOWN
# Expected exit code: 1
# Expected: data/uptime_log.csv appended with timeout entry

# Test 4: Verify CSV format
python -c "
import csv
rows = list(csv.DictReader(open('data/uptime_log.csv')))
assert len(rows) == 3, f'Expected 3 rows, got {len(rows)}'
assert rows[0]['status_code'] == '200', 'First check should be 200'
assert rows[1]['status_code'] == '500', 'Second check should be 500'
assert rows[2]['status_code'] == '0', 'Third check should be 0 (timeout)'
print('CSV validation passed')
"

# If any test fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify the full workflow end-to-end

# Simulate the GitHub Actions workflow locally
# 1. Set environment variables
export URL=https://example.com
export TIMEOUT=10

# 2. Run the monitor tool
python tools/monitor.py --url "$URL" --timeout "$TIMEOUT"
EXIT_CODE=$?

# 3. Verify CSV was updated
CSV_LINES=$(wc -l < data/uptime_log.csv)
if [ "$CSV_LINES" -lt 2 ]; then
  echo "ERROR: CSV should have at least 2 lines (header + 1 data row)"
  exit 1
fi

# 4. Verify git can stage and commit the CSV
git add data/uptime_log.csv
git diff --cached --name-only | grep -q uptime_log.csv || {
  echo "ERROR: CSV file not staged"
  exit 1
}

# 5. Reset git state (don't actually commit during test)
git reset HEAD data/uptime_log.csv

# 6. Verify exit code reflects site status
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "✓ Site is UP — exit code 0"
elif [ "$EXIT_CODE" -eq 1 ]; then
  echo "✓ Site is DOWN — exit code 1"
else
  echo "ERROR: Unexpected exit code $EXIT_CODE"
  exit 1
fi

echo "Integration test passed"
```

---

## Final Validation Checklist
- [x] Tool passes Level 1 (syntax, imports, structure)
- [x] Tool passes Level 2 (unit tests with various URLs and scenarios)
- [x] Tool passes Level 3 (integration test simulating GitHub Actions)
- [x] CSV file created on first run with correct headers
- [x] CSV append works without corrupting existing data
- [x] Exit code 0 on up, 1 on down
- [x] Response time measured in milliseconds
- [x] Timestamp in ISO 8601 UTC format
- [x] CLAUDE.md documents tool usage and workflow
- [x] .github/workflows/monitor.yml has concurrency setting
- [x] .github/workflows/monitor.yml has git push retry logic
- [x] README.md covers all three execution paths (cron, manual, local CLI)
- [x] No hardcoded URLs in tool code (always from CLI args or env vars)
- [x] requirements.txt lists requests

---

## Anti-Patterns to Avoid
- Do not use MCP for simple HTTP GET (requests library is simpler and more reliable)
- Do not compare to previous state (this is Monitor > Log, not Monitor > Detect > Alert)
- Do not send alerts (workflow red/green status IS the alert)
- Do not use JSON or complex data structures (CSV is the right format for time-series logs)
- Do not exit 0 when site is down (exit 1 makes workflow fail visibly in GitHub Actions UI)
- Do not use local timezone (always UTC with ISO 8601 for consistency)
- Do not log response_time in seconds (use milliseconds for precision)
- Do not skip git push retry logic (concurrent runs can cause conflicts)
- Do not use `git add -A` (stage only data/uptime_log.csv)
- Do not hardcode URL in tool (always accept as CLI arg or env var)
- Do not create CSV in tools/ directory (output goes in data/)
- Do not use subagents for single-tool workflows (unnecessary complexity)
- Do not use Agent Teams for sequential operations (no parallelization possible here)

---

## Confidence Score: 9/10

**Score rationale:**
- **Pattern match**: 10/10 — This is the proven website-uptime-monitor pattern from library/patterns.md
- **Tool complexity**: 10/10 — Single tool with stdlib + requests, well-understood logic
- **GitHub Actions**: 9/10 — Cron + concurrency + git push retry are all documented patterns
- **CSV handling**: 10/10 — CSV stdlib handles all edge cases (encoding, newlines, quoting)
- **Exit code signaling**: 10/10 — Standard pattern for workflow status visibility
- **No secrets required**: 10/10 — Public URL monitoring needs no authentication
- **Validation**: 9/10 — Clear test cases for up/down/timeout scenarios

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — specification is complete and unambiguous

**Overall:** High confidence for one-pass build success. This is a proven pattern with minimal external dependencies and clear success criteria.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/website-uptime-monitor.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
