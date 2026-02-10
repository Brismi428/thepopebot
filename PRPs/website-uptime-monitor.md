name: "website-uptime-monitor"
description: |

## Purpose
WAT System PRP (Product Requirements Prompt) — A minimal uptime monitoring system that checks a single website URL on a schedule and logs status to a local CSV file.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a GitHub Actions-powered system that monitors a single website's uptime by making HTTP requests every 5 minutes and logging the results to a CSV file in the repository. The system should be simple, self-contained, and require no external services beyond GitHub Actions runtime.

## Why
- **Visibility**: Provides historical uptime data for a single critical URL
- **Simplicity**: No dependencies on external monitoring SaaS or complex infrastructure
- **Auditability**: Git history tracks every status check with full commit log
- **Cost**: Zero cost — runs entirely on GitHub Actions free tier

## What
A scheduled GitHub Actions workflow that:
1. Sends an HTTP GET request to the configured URL
2. Measures response time in milliseconds
3. Records status code, response time, timestamp, and up/down status
4. Appends the record to a CSV file in the repository
5. Commits the updated CSV file back to the repo
6. Runs automatically every 5 minutes via cron schedule

### Success Criteria
- [x] System checks the configured URL every 5 minutes via GitHub Actions
- [x] Records status code, response time (ms), ISO timestamp, and up/down status to CSV
- [x] CSV file grows with each check (one row per check)
- [x] No manual intervention required — fully autonomous
- [x] Works with any HTTP/HTTPS URL
- [x] Handles timeouts and errors gracefully
- [x] All three execution paths work: CLI (manual test), GitHub Actions (scheduled), Agent HQ (manual trigger)

---

## Inputs
[What goes into the system. Be specific about format, source, and any validation requirements.]

```yaml
- name: "target_url"
  type: "string (URL)"
  source: "config/monitor.json or environment variable MONITOR_URL"
  required: true
  description: "The URL to monitor (http:// or https://)"
  example: "https://example.com"
  validation: "Must be valid HTTP/HTTPS URL"

- name: "timeout_seconds"
  type: "integer"
  source: "config/monitor.json or environment variable TIMEOUT_SECONDS"
  required: false
  default: 10
  description: "HTTP request timeout in seconds"
  example: "10"
```

## Outputs
[What comes out of the system. Where do results go?]

```yaml
- name: "uptime_log.csv"
  type: "CSV file"
  destination: "logs/uptime_log.csv (committed to repo)"
  description: "Append-only log of all uptime checks with headers: timestamp,url,status_code,response_time_ms,is_up"
  example: |
    timestamp,url,status_code,response_time_ms,is_up
    2026-02-10T19:05:00Z,https://example.com,200,145,true
    2026-02-10T19:10:00Z,https://example.com,200,132,true
    2026-02-10T19:15:00Z,https://example.com,503,5021,false
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://docs.python-requests.org/en/latest/"
  why: "HTTP requests library for fallback implementation (timeout handling, status codes)"

- url: "https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule"
  why: "GitHub Actions cron syntax and schedule trigger behavior"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide HTTP request capabilities (Fetch MCP)"

- doc: "library/patterns.md"
  why: "Select the best workflow pattern for this system (simplified Monitor > Detect > Alert)"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns for HTTP requests and CSV logging"
```

### Workflow Pattern Selection
```yaml
pattern: "Monitor > Detect > Alert (simplified to Monitor > Log)"
rationale: "This is a monitoring system but without the alert component. The workflow is: check URL → evaluate status → log result. No detection logic needed (every check is logged), no alert mechanism required."
modifications: "Remove Detect and Alert phases. The pattern becomes: Monitor > Log. Every check produces a log entry regardless of status."
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "HTTP GET request"
    primary_mcp: "fetch"
    alternative_mcp: "none"
    fallback: "Direct HTTP via Python requests library (preferred for simplicity)"
    secret_name: "none (public HTTP only)"

  - name: "CSV file write (append)"
    primary_mcp: "filesystem"
    alternative_mcp: "none"
    fallback: "Python csv module (stdlib)"
    secret_name: "none"

  - name: "Git commit and push"
    primary_mcp: "git"
    alternative_mcp: "none"
    fallback: "Git CLI via subprocess in GitHub Actions"
    secret_name: "GITHUB_TOKEN (auto-provided by Actions)"
```

### Known Gotchas & Constraints
```
# CRITICAL: GitHub Actions cron is not exact — expect ±5 minute variance under load
# CRITICAL: Minimum cron frequency is every 5 minutes (*/5 * * * *)
# CRITICAL: HTTP timeout must be set — default to 10s to prevent hanging jobs
# CRITICAL: CSV must be opened in append mode with newline='' to prevent blank rows on Windows
# CRITICAL: Git commit must use --amend or separate commits to avoid balloon repo size (use separate commits for audit trail)
# CRITICAL: Status codes >= 400 are considered "down", < 400 are "up" (except timeouts → down)
# CRITICAL: CSV headers must be written only if file doesn't exist
# CRITICAL: Timestamp must be ISO 8601 format with UTC timezone (isoformat())
# CRITICAL: Response time should be in milliseconds (multiply elapsed seconds by 1000)
# CRITICAL: GitHub Actions requires git config user.email and user.name before commit
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents: []
# No subagents needed — this system is a single simple task that doesn't benefit from delegation.
# The main agent can handle the entire workflow: make HTTP request → log to CSV → commit.
```

### Agent Teams Analysis
```yaml
independent_tasks: []
independent_task_count: 0
recommendation: "Sequential execution"
rationale: "Only one task: check URL and log result. No parallelization opportunity. Agent Teams overhead (spawning, coordination, merging) would add complexity with no benefit."

sequential_rationale: "Single linear workflow with one HTTP request and one file write. No independent tasks exist."
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "*/5 * * * *  # Every 5 minutes"
    description: "Main uptime check — runs every 5 minutes automatically"

  - type: "workflow_dispatch"
    config: "Manual trigger with optional URL override input"
    description: "Allows manual test runs and one-off checks of different URLs"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "Load Configuration"
    description: "Read target URL and timeout from config/monitor.json or environment variables"
    subagent: null
    tools: []
    inputs: "config/monitor.json, env vars"
    outputs: "target_url (str), timeout_seconds (int)"
    failure_mode: "Config file missing or malformed JSON"
    fallback: "Use environment variable MONITOR_URL and TIMEOUT_SECONDS with defaults"

  - name: "Execute HTTP Check"
    description: "Send HTTP GET request to target URL with timeout, measure response time"
    subagent: null
    tools: ["check_url.py"]
    inputs: "target_url, timeout_seconds"
    outputs: "status_code (int), response_time_ms (float), is_up (bool), timestamp (str)"
    failure_mode: "Timeout, DNS failure, connection refused, SSL error"
    fallback: "Record as 'down' with status_code=0, response_time=timeout*1000"

  - name: "Append to CSV Log"
    description: "Append the check result to logs/uptime_log.csv (create with headers if doesn't exist)"
    subagent: null
    tools: ["check_url.py"]
    inputs: "timestamp, target_url, status_code, response_time_ms, is_up"
    outputs: "Updated logs/uptime_log.csv"
    failure_mode: "File write permission error, disk full"
    fallback: "Log error to stderr and exit non-zero (GitHub Actions will show failed run)"

  - name: "Commit and Push"
    description: "Stage logs/uptime_log.csv, commit with timestamp message, push to main branch"
    subagent: null
    tools: []
    inputs: "Updated CSV file"
    outputs: "New commit in main branch"
    failure_mode: "Git push conflict (simultaneous runs), auth failure"
    fallback: "Pull with rebase, retry push once. If still fails, log error and exit (GitHub Actions notifications will alert)"
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "check_url.py"
    purpose: "Make HTTP GET request to URL, measure response time, determine up/down status, append result to CSV"
    catalog_pattern: "rest_client (simplified) + csv_read_write (append mode)"
    inputs:
      - "target_url: str — The URL to check (from CLI arg, env var, or config file)"
      - "timeout: int — Request timeout in seconds (default 10)"
      - "csv_path: str — Path to CSV log file (default logs/uptime_log.csv)"
    outputs: "CSV row appended; prints JSON summary to stdout for logging"
    dependencies: ["requests"]
    mcp_used: "none (requests library is simpler than Fetch MCP for this use case)"
    error_handling: "Try/except on requests.get() — catch Timeout, ConnectionError, RequestException. Log all errors as 'down' status with status_code=0"
```

### Per-Tool Pseudocode
```python
# check_url.py
#!/usr/bin/env python3
"""
Uptime monitor tool: Check a URL and log the result to CSV.

Usage:
    python check_url.py --url https://example.com --timeout 10 --csv logs/uptime_log.csv
"""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def main():
    # PATTERN: rest_client (simplified) + csv_read_write (append)
    
    # Step 1: Parse inputs
    parser = argparse.ArgumentParser(description="Check URL uptime and log to CSV")
    parser.add_argument("--url", default=os.getenv("MONITOR_URL"), required=True,
                        help="URL to monitor")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("TIMEOUT_SECONDS", "10")),
                        help="Request timeout in seconds")
    parser.add_argument("--csv", default="logs/uptime_log.csv",
                        help="Path to CSV log file")
    args = parser.parse_args()

    # Step 2: Execute HTTP check
    # GOTCHA: requests.get() can throw multiple exception types
    # GOTCHA: response_time must be in milliseconds
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        start_time = time.monotonic()
        response = requests.get(args.url, timeout=args.timeout, allow_redirects=True)
        elapsed_ms = (time.monotonic() - start_time) * 1000
        
        status_code = response.status_code
        # PATTERN: Status codes < 400 are "up", >= 400 are "down"
        is_up = status_code < 400
        
    except requests.exceptions.Timeout:
        # FALLBACK: Timeout counts as down with response_time = timeout period
        status_code = 0
        elapsed_ms = args.timeout * 1000
        is_up = False
        
    except (requests.exceptions.ConnectionError,
            requests.exceptions.RequestException) as exc:
        # FALLBACK: Any other error counts as down
        status_code = 0
        elapsed_ms = 0
        is_up = False
        print(f"Error checking URL: {exc}", file=sys.stderr)

    # Step 3: Append to CSV
    # CRITICAL: Create logs/ directory if it doesn't exist
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # CRITICAL: Check if file exists to determine if headers are needed
    file_exists = csv_path.exists()
    
    # CRITICAL: Open in append mode with newline='' to prevent blank rows
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Write headers only if file is new
        if not file_exists:
            writer.writerow(["timestamp", "url", "status_code", "response_time_ms", "is_up"])
        
        # Write data row
        writer.writerow([timestamp, args.url, status_code, round(elapsed_ms, 2), is_up])
    
    # Step 4: Output summary to stdout for logging
    # PATTERN: Structured JSON to stdout
    result = {
        "timestamp": timestamp,
        "url": args.url,
        "status_code": status_code,
        "response_time_ms": round(elapsed_ms, 2),
        "is_up": is_up,
        "csv_updated": str(csv_path),
    }
    print(json.dumps(result, indent=2))
    
    # Exit code: 0 if up, 1 if down (for GitHub Actions failure visibility)
    sys.exit(0 if is_up else 1)


if __name__ == "__main__":
    main()
```

### Integration Points
```yaml
SECRETS:
  # No secrets required — monitoring public URLs only

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "MONITOR_URL=https://example.com  # The URL to monitor"
      - "TIMEOUT_SECONDS=10  # HTTP request timeout"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "requests>=2.31.0  # HTTP library"

GITHUB_ACTIONS:
  - trigger: "schedule (*/5 * * * *)"
    config: |
      - Runs check_url.py with --url and --timeout from config or env vars
      - Commits logs/uptime_log.csv after each check
      - Git config user.email and user.name set to github-actions[bot]
      - Uses GITHUB_TOKEN for push authentication
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/check_url.py').read())"

# Import check — verify no missing dependencies (requires requests installed)
python -c "import sys; sys.path.insert(0, 'tools'); import check_url"

# Structure check — verify main() exists
python -c "from tools.check_url import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Test 1: Check a known-good URL (example.com)
python tools/check_url.py --url https://example.com --timeout 10 --csv /tmp/test_uptime.csv
# Expected: status_code=200, is_up=true, response_time_ms > 0
# Expected: /tmp/test_uptime.csv exists with headers and one data row

# Test 2: Check a known-bad URL (non-existent domain)
python tools/check_url.py --url https://nonexistent-domain-12345.com --timeout 5 --csv /tmp/test_uptime.csv
# Expected: status_code=0, is_up=false, response_time_ms >= 0
# Expected: /tmp/test_uptime.csv has two rows (header + first check + this check)

# Test 3: Check a timeout scenario (slow endpoint with short timeout)
python tools/check_url.py --url https://httpbin.org/delay/10 --timeout 2 --csv /tmp/test_uptime.csv
# Expected: status_code=0, is_up=false, response_time_ms ~= 2000
# Expected: /tmp/test_uptime.csv has three rows now

# Test 4: Verify CSV format
head -n 5 /tmp/test_uptime.csv
# Expected: Header row followed by data rows with correct columns

# Test 5: Verify JSON output structure
python tools/check_url.py --url https://example.com --timeout 10 --csv /tmp/test_uptime.csv | jq .
# Expected: Valid JSON with keys: timestamp, url, status_code, response_time_ms, is_up, csv_updated

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify the tool works in the GitHub Actions context

# Simulate the full workflow
mkdir -p logs

# Run check (simulating GitHub Actions environment)
export MONITOR_URL="https://example.com"
export TIMEOUT_SECONDS="10"
python tools/check_url.py --url $MONITOR_URL --timeout $TIMEOUT_SECONDS --csv logs/uptime_log.csv

# Verify CSV was created and has content
test -f logs/uptime_log.csv && echo "✓ CSV file created"
[ $(wc -l < logs/uptime_log.csv) -ge 2 ] && echo "✓ CSV has headers + data"

# Verify CSV format
python -c "
import csv
with open('logs/uptime_log.csv', 'r') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    assert 'timestamp' in row, 'Missing timestamp column'
    assert 'url' in row, 'Missing url column'
    assert 'status_code' in row, 'Missing status_code column'
    assert 'response_time_ms' in row, 'Missing response_time_ms column'
    assert 'is_up' in row, 'Missing is_up column'
    print('✓ CSV format valid')
"

# Run multiple checks to verify append behavior
for i in {1..3}; do
    python tools/check_url.py --url $MONITOR_URL --timeout $TIMEOUT_SECONDS --csv logs/uptime_log.csv
    sleep 1
done

# Verify CSV grew (should have 1 header + 4 data rows now)
[ $(wc -l < logs/uptime_log.csv) -eq 5 ] && echo "✓ CSV append working"

# Verify workflow.md references match actual tool files
[ -f workflow.md ] && grep -q "check_url.py" workflow.md && echo "✓ workflow.md references correct tool"

# Verify CLAUDE.md documents the tool
[ -f CLAUDE.md ] && grep -q "check_url.py" CLAUDE.md && echo "✓ CLAUDE.md documents tool"

# Verify .github/workflows/ YAML is valid (requires yq or Python PyYAML)
python -c "
import yaml
with open('.github/workflows/monitor.yml', 'r') as f:
    data = yaml.safe_load(f)
    assert 'on' in data, 'Missing workflow triggers'
    assert 'schedule' in data['on'], 'Missing schedule trigger'
    print('✓ GitHub Actions workflow YAML valid')
"

echo "Integration test passed"
```

---

## Final Validation Checklist
- [ ] tools/check_url.py passes Level 1 (syntax, imports, structure)
- [ ] tools/check_url.py passes Level 2 (unit tests with various URLs)
- [ ] Pipeline passes Level 3 (CSV creation, append, format validation)
- [ ] workflow.md has failure modes and fallbacks for HTTP errors
- [ ] CLAUDE.md documents the tool, CSV schema, and execution paths
- [ ] .github/workflows/monitor.yml has schedule trigger (*/5 * * * *)
- [ ] .github/workflows/monitor.yml has timeout-minutes set (default 5 minutes)
- [ ] .github/workflows/monitor.yml configures git user.email and user.name
- [ ] .github/workflows/monitor.yml commits and pushes logs/uptime_log.csv
- [ ] .env.example lists MONITOR_URL and TIMEOUT_SECONDS
- [ ] .gitignore excludes .env (but NOT logs/ — we want the CSV committed)
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded URLs in code (use config or env vars)
- [ ] requirements.txt lists requests
- [ ] logs/ directory is created automatically by the tool
- [ ] CSV headers are written only on first run (file creation)

---

## Anti-Patterns to Avoid
- Do not hardcode the target URL in the code — use config or environment variables
- Do not use `git add -A` in the workflow — stage only `logs/uptime_log.csv`
- Do not skip error handling for HTTP requests — handle Timeout, ConnectionError, RequestException
- Do not forget to set git config user.email and user.name in GitHub Actions
- Do not use bare `except:` — catch specific exception types
- Do not forget newline='' when opening CSV in append mode (prevents blank rows on Windows)
- Do not write CSV headers on every append (check if file exists first)
- Do not forget to create logs/ directory (use mkdir -p or Path.mkdir(parents=True, exist_ok=True))
- Do not make CSV path absolute — keep it relative to repo root for portability
- Do not ignore GitHub Actions cron variance — document that checks may not be exactly every 5 minutes
- Do not set timeout too high (keeps Actions job alive unnecessarily) or too low (false negatives)
- Do not exit 0 on failure — exit non-zero when is_up=false so GitHub Actions shows failed status
- Do not use blocking HTTP clients without timeout (always set timeout parameter)
- Do not forget timezone on timestamp — use datetime.now(timezone.utc)
- Do not log response body (bloats CSV) — only log metadata (status code, time)

---

## Confidence Score: 9/10

**Score rationale:**
- **Requirements clarity**: High confidence — requirements are explicit, simple, and testable
- **Technical feasibility**: High confidence — straightforward HTTP request + CSV append, no complex dependencies
- **Tool reusability**: High confidence — check_url.py follows standard patterns from tool_catalog.md (rest_client + csv_read_write)
- **GitHub Actions integration**: High confidence — cron triggers are well-documented, git commit/push is standard
- **Edge case handling**: High confidence — error scenarios (timeout, DNS failure, SSL error) are documented with fallbacks
- **Validation coverage**: High confidence — three-level validation gates cover syntax, functionality, and integration

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — all requirements are clear and specific

**Proceed to build: YES — no ambiguities detected, confidence score >= 7/10**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```bash
/execute-prp PRPs/website-uptime-monitor.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
