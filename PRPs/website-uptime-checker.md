name: "Website Uptime Checker"
description: |
  A lightweight, Git-native website uptime monitoring system that periodically checks if a target website is responding, measures response time, and maintains a version-controlled CSV log of all checks. GitHub Actions workflow status provides at-a-glance site visibility (green = up, red = down).

---

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
Build a simple, reliable website uptime monitoring system that:
- Checks if a website is responding via HTTP/HTTPS GET requests
- Measures response time in milliseconds
- Logs all checks to a version-controlled CSV file
- Signals status via GitHub Actions workflow status (green=up, red=down)
- Runs autonomously on a schedule (default: every 5 minutes)
- Requires zero external monitoring services or databases

## Why
- **Simplicity**: No complex detection logic, no external dependencies, no monitoring SaaS subscription
- **Git-native audit trail**: Every check is committed, full history is preserved, diffs show status changes
- **At-a-glance status**: GitHub Actions UI shows workflow status (green/red) without opening logs
- **Zero cost**: Fits within GitHub Actions free tier for public repos; minimal minutes for private repos
- **Self-contained**: All data lives in the repository — no external state to manage

## What
From the perspective of a user deploying this system:

1. **Setup**: Configure target URL as GitHub repository variable
2. **Schedule**: System runs every 5 minutes (configurable cron expression)
3. **Check**: System makes HTTP GET request, measures response time, determines up/down status
4. **Log**: Result is appended to CSV file and committed to repository
5. **Signal**: Workflow shows green (site up) or red (site down) in Actions UI
6. **Query**: User can query CSV for uptime percentage, average response time, downtime events

### Success Criteria
- [ ] System successfully checks target URL and logs result to CSV
- [ ] CSV file contains columns: timestamp, url, status_code, response_time_ms, is_up
- [ ] Workflow exit code reflects site status (0=up, 1=down)
- [ ] CSV file is committed after each check with descriptive commit message
- [ ] System runs autonomously via GitHub Actions on schedule
- [ ] All three execution paths work: local CLI, GitHub Actions cron, GitHub Actions manual dispatch
- [ ] No secrets required for public URL monitoring
- [ ] Concurrent execution prevented (GitHub Actions concurrency setting)
- [ ] Git push retry logic handles rare concurrent commits

---

## Inputs
What goes into the system. Be specific about format, source, and any validation requirements.

```yaml
- name: "URL"
  type: "string"
  source: "GitHub repository variable, workflow dispatch input, or CLI argument"
  required: true
  description: "Target URL to monitor. Must include protocol (http:// or https://)"
  example: "https://example.com"
  validation:
    - "Must start with http:// or https://"
    - "Must be a valid URL format"

- name: "TIMEOUT"
  type: "integer"
  source: "GitHub repository variable, workflow dispatch input, or CLI argument"
  required: false
  description: "HTTP request timeout in seconds"
  example: "10"
  default: 10
  validation:
    - "Must be positive integer"
    - "Reasonable range: 5-60 seconds"

- name: "CSV_PATH"
  type: "string"
  source: "CLI argument only (GitHub Actions uses default)"
  required: false
  description: "Output CSV file path for local testing"
  example: "data/uptime_log.csv"
  default: "data/uptime_log.csv"
```

## Outputs
What comes out of the system. Where do results go?

```yaml
- name: "uptime_log.csv"
  type: "CSV file"
  destination: "data/uptime_log.csv (committed to repository)"
  description: "Append-only time-series log of all uptime checks"
  format: |
    timestamp,url,status_code,response_time_ms,is_up
    2026-02-13T01:13:32Z,https://example.com,200,245,true
  columns:
    - "timestamp: ISO 8601 UTC timestamp of check"
    - "url: Target URL that was checked"
    - "status_code: HTTP status code (0 if request failed)"
    - "response_time_ms: Response time in milliseconds"
    - "is_up: Boolean (true if 200-399, false otherwise)"

- name: "exit_code"
  type: "integer"
  destination: "Tool exit code (sets GitHub Actions workflow status)"
  description: "0 if site is UP, 1 if site is DOWN"
  example: "0"
  notes:
    - "Exit code 0 → workflow shows green"
    - "Exit code 1 → workflow shows red"
    - "Provides at-a-glance status visibility"

- name: "git_commit"
  type: "commit"
  destination: "Repository main branch"
  description: "Commit containing updated CSV file"
  message_format: "Check {URL}: {STATUS} ({RESPONSE_TIME}ms) at {TIMESTAMP}"
  example: "Check https://example.com: UP (245ms) at 2026-02-13T01:13:32Z"
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- doc: "systems/website-uptime-monitor/"
  why: "A similar system already exists — use as reference for proven patterns"

- doc: "library/patterns.md"
  why: "Monitor > Log pattern is documented here (simplified from Monitor > Detect > Alert)"

- doc: "library/tool_catalog.md"
  why: "HTTP request pattern and CSV writing pattern are cataloged"

- url: "https://docs.python-requests.org/en/master/"
  why: "Official requests library documentation for HTTP client"

- url: "https://docs.python.org/3/library/csv.html"
  why: "Python stdlib CSV module documentation"

- url: "https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions"
  why: "GitHub Actions workflow syntax for cron scheduling and concurrency settings"
```

### Workflow Pattern Selection
```yaml
pattern: "Monitor > Log (simplified from Monitor > Detect > Alert)"
rationale: |
  This is the simplest possible monitoring system:
  - No detection logic (no comparison to previous state)
  - No alerting layer (workflow red/green IS the notification)
  - Direct logging: check → CSV → commit
  
  The Monitor > Log pattern is perfect for:
  - Raw data collection without interpretation
  - Git history as audit trail
  - Workflow status as primary notification mechanism
  - Zero external dependencies

modifications: "None needed — this is the canonical implementation of Monitor > Log"
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "HTTP GET requests"
    primary_mcp: "None"
    alternative_mcp: "None"
    fallback: "Python requests library (direct implementation, no MCP needed)"
    secret_name: "None (public URL monitoring requires no authentication)"
    notes:
      - "requests library is more reliable than Fetch MCP for simple GET requests"
      - "Fewer dependencies = fewer failure modes"

  - name: "CSV file writing"
    primary_mcp: "None"
    alternative_mcp: "None"
    fallback: "Python csv stdlib module"
    secret_name: "None"
    notes:
      - "stdlib csv module is the right tool — no MCP needed"
      - "Append-only writes with proper encoding handling"

  - name: "Git operations"
    primary_mcp: "None"
    alternative_mcp: "None"
    fallback: "git CLI via subprocess (GitHub Actions provides git automatically)"
    secret_name: "GITHUB_TOKEN (automatically provided by GitHub Actions)"
    notes:
      - "GitHub Actions includes git and authenticates via GITHUB_TOKEN"
      - "Git operations handled by workflow, not by Python tools"

dependencies:
  - "requests==2.31.0  # HTTP client"
  - "No other dependencies — uses Python stdlib for everything else"
```

### Known Gotchas & Constraints
```
# CRITICAL: GitHub Actions cron has ±5 minute variance — this is normal, not a bug
# CRITICAL: GITHUB_TOKEN has limited lifetime — workflow must complete within token expiry
# CRITICAL: CSV file will grow ~30KB/day at 5-minute intervals — plan for yearly archiving
# CRITICAL: GitHub Actions free tier: unlimited for public repos, 2,000 minutes/month for private
# CRITICAL: Concurrent workflow runs can cause git push conflicts — use concurrency setting
# CRITICAL: Exit code 0 = success = site UP; exit code 1 = failure = site DOWN (counterintuitive)
# CRITICAL: URL must include protocol (https://example.com not example.com)
# CRITICAL: Redirects (3xx) are followed and considered UP if final response is 2xx-3xx
# CRITICAL: Timeouts result in status_code=0 and is_up=false
# CRITICAL: CSV append must happen BEFORE git commit to ensure data continuity
# CRITICAL: Never use git add -A or git add . — stage only data/uptime_log.csv
```

---

## System Design

### Subagent Architecture
This system is simple enough that subagents are NOT needed. The main agent executes all steps sequentially. Subagents add overhead without benefit for a single-tool, linear workflow.

```yaml
subagents: []
rationale: |
  This system has:
  - One tool (monitor.py)
  - One workflow step (check → log → commit)
  - No branching logic or parallel execution
  - No domain-specific expertise required
  
  Subagent overhead (delegation, context switching) would slow execution without adding value.
  Main agent direct execution is the correct pattern for simple linear workflows.
```

### Agent Teams Analysis
```yaml
independent_tasks: []
independent_task_count: 0
recommendation: "Sequential execution"
rationale: |
  This system checks ONE URL per execution. There are no independent tasks to parallelize.
  
  Even if monitoring MULTIPLE URLs:
  - GitHub Actions matrix strategy is the right tool (not Agent Teams)
  - Each matrix job runs independently in parallel
  - No LLM coordination needed
  
  Agent Teams overhead is not justified when GitHub Actions provides built-in parallelization.

sequential_rationale: |
  The workflow is inherently sequential:
  1. Check URL (depends on: nothing)
  2. Log to CSV (depends on: check result)
  3. Commit to Git (depends on: CSV write)
  
  Each step MUST complete before the next can start. No parallelization possible.
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "*/5 * * * *  # Every 5 minutes"
    description: "Primary execution path — automated periodic checks"
    notes:
      - "GitHub Actions cron has ±5 minute variance"
      - "Variance is expected behavior, not a bug"
      - "Adjust frequency via cron expression: */15, */30, 0 *, etc."

  - type: "workflow_dispatch"
    config:
      inputs:
        url:
          description: "Target URL to check (overrides repository variable)"
          required: false
          default: ""
        timeout:
          description: "Request timeout in seconds"
          required: false
          default: "10"
    description: "Manual trigger for testing or ad-hoc checks"

  - type: "push (future enhancement)"
    config: "paths: ['.github/workflows/monitor.yml', 'tools/monitor.py']"
    description: "Auto-test when workflow or tool is modified"
    notes:
      - "Not included in v1 — add after initial deployment"
```

---

## Implementation Blueprint

### Workflow Steps
Ordered list of workflow phases. Each step becomes a section in workflow.md.

```yaml
steps:
  - name: "Check URL"
    description: "Make HTTP GET request to target URL, measure response time, determine up/down status"
    subagent: "None (main agent direct execution)"
    tools: ["monitor.py"]
    inputs:
      - "URL: Target URL from environment variable or CLI argument"
      - "TIMEOUT: Request timeout from environment variable or CLI argument"
    outputs:
      - "status_code: HTTP response code (200, 404, 500, etc.)"
      - "response_time_ms: Elapsed time in milliseconds"
      - "is_up: Boolean (true if 200-399, false otherwise)"
      - "timestamp: ISO 8601 UTC timestamp of check"
    failure_mode: "Timeout, connection refused, DNS failure, SSL/TLS error, network error"
    fallback: "Log as DOWN with status_code=0 — no crash, no retry"

  - name: "Log to CSV"
    description: "Append check result to data/uptime_log.csv (create file if missing)"
    subagent: "None"
    tools: ["monitor.py (same tool, integrated step)"]
    inputs:
      - "Check result from Step 1"
      - "CSV_PATH: Output file path"
    outputs:
      - "Updated CSV file with new row appended"
    failure_mode: "Disk full, permissions error, directory missing"
    fallback: "Create data/ directory automatically; print error and exit 1 if write fails"

  - name: "Commit to Git"
    description: "Stage CSV file, commit with descriptive message, push to repository"
    subagent: "None"
    tools: ["GitHub Actions workflow step (not Python tool)"]
    inputs:
      - "Updated data/uptime_log.csv"
      - "Check result metadata (URL, status, response time, timestamp)"
    outputs:
      - "Git commit on main branch"
      - "Commit message: 'Check {URL}: {STATUS} ({RESPONSE_TIME}ms) at {TIMESTAMP}'"
    failure_mode: "Git push conflict (concurrent runs), GITHUB_TOKEN expired, branch protection"
    fallback: |
      - Concurrency setting prevents concurrent runs
      - Retry with rebase if push fails (rare edge case)
      - Fail workflow if token expired (requires human intervention)

  - name: "Signal Status"
    description: "Exit with code 0 (up) or 1 (down) to set workflow status"
    subagent: "None"
    tools: ["monitor.py exit code"]
    inputs:
      - "is_up boolean from Step 1"
    outputs:
      - "Exit code: 0 if is_up=true, 1 if is_up=false"
      - "Workflow status: success (green) or failure (red)"
    failure_mode: "None — exit code always set correctly"
    fallback: "N/A"
```

### Tool Specifications
For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.

```yaml
tools:
  - name: "monitor.py"
    purpose: "Check website URL via HTTP GET, measure response time, log to CSV, exit with status code"
    catalog_pattern: "HTTP client (requests) + CSV write (stdlib csv) — both are catalog patterns"
    inputs:
      - "--url: string (required) — Target URL with protocol (http:// or https://)"
      - "--timeout: integer (optional, default 10) — Request timeout in seconds"
      - "--csv-path: string (optional, default 'data/uptime_log.csv') — Output CSV file path"
    outputs: |
      - Appends row to CSV: timestamp,url,status_code,response_time_ms,is_up
      - Prints JSON to stdout: {"timestamp": "...", "url": "...", "status_code": 200, ...}
      - Exit code: 0 if up, 1 if down
    dependencies:
      - "requests==2.31.0  # HTTP client"
      - "Python stdlib: csv, pathlib, argparse, logging, time"
    mcp_used: "None"
    error_handling: |
      - All exceptions caught (requests.RequestException, ConnectionError, Timeout, etc.)
      - Exceptions logged as DOWN with status_code=0
      - CSV write failure logs error and exits 1
      - Tool NEVER crashes — always produces CSV row and exit code
```

### Per-Tool Pseudocode
```python
# monitor.py
def main():
    # PATTERN: HTTP client + CSV append
    # Step 1: Parse inputs
    args = parse_args()  # argparse: --url, --timeout, --csv-path
    
    # Validate URL includes protocol
    if not args.url.startswith(('http://', 'https://')):
        logging.error("URL must include protocol (http:// or https://)")
        sys.exit(1)
    
    # Step 2: Check URL
    timestamp = datetime.utcnow().isoformat() + 'Z'
    try:
        start = time.perf_counter()
        response = requests.get(
            args.url,
            timeout=args.timeout,
            allow_redirects=True,  # Follow redirects
            headers={'User-Agent': 'WAT-Uptime-Monitor/1.0'}
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        status_code = response.status_code
        is_up = 200 <= status_code < 400
    except requests.RequestException as exc:
        logging.warning(f"Request failed: {exc}")
        elapsed_ms = args.timeout * 1000
        status_code = 0
        is_up = False
    
    # Step 3: Log to CSV
    csv_path = Path(args.csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create CSV with headers if missing
    if not csv_path.exists():
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'url', 'status_code', 'response_time_ms', 'is_up'])
    
    # Append row
    with csv_path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, args.url, status_code, round(elapsed_ms, 2), is_up])
    
    # Step 4: Output and exit
    result = {
        'timestamp': timestamp,
        'url': args.url,
        'status_code': status_code,
        'response_time_ms': round(elapsed_ms, 2),
        'is_up': is_up,
    }
    print(json.dumps(result))
    
    # Exit with status code
    sys.exit(0 if is_up else 1)
```

### Integration Points
```yaml
SECRETS:
  - name: "None required for public URL monitoring"
    purpose: "N/A"
    required: false
    notes:
      - "If monitoring authenticated endpoints, add MONITOR_AUTH_USER and MONITOR_AUTH_PASS"

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "URL=https://example.com  # Target URL to monitor"
      - "TIMEOUT=10  # Request timeout in seconds"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "requests==2.31.0  # HTTP client for URL checks"

GITHUB_ACTIONS:
  - trigger: "schedule"
    config: |
      schedule:
        - cron: '*/5 * * * *'  # Every 5 minutes
      
      concurrency:
        group: uptime-monitor
        cancel-in-progress: false  # Let running checks complete
      
      permissions:
        contents: write  # Required for git commit/push
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/monitor.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.monitor')"

# Structure check — verify main() exists
python -c "from tools.monitor import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — tool must produce correct output for sample inputs

# Test successful check (use a reliable site)
python tools/monitor.py --url https://www.google.com --timeout 10 --csv-path /tmp/test_uptime.csv

# Verify CSV was created
test -f /tmp/test_uptime.csv || echo "ERROR: CSV not created"

# Verify CSV has header + 1 data row
LINES=$(wc -l < /tmp/test_uptime.csv)
test "$LINES" -eq 2 || echo "ERROR: Expected 2 lines, got $LINES"

# Verify JSON output is valid
python tools/monitor.py --url https://www.google.com --timeout 10 --csv-path /tmp/test2.csv | python -m json.tool

# Verify exit code for UP site
python tools/monitor.py --url https://www.google.com --timeout 10 --csv-path /tmp/test3.csv
test $? -eq 0 || echo "ERROR: Exit code should be 0 for UP site"

# Verify exit code for DOWN site (use invalid URL)
python tools/monitor.py --url https://this-domain-definitely-does-not-exist-12345.com --timeout 5 --csv-path /tmp/test4.csv
test $? -eq 1 || echo "ERROR: Exit code should be 1 for DOWN site"

# Verify status_code=0 for DOWN site
grep ",0," /tmp/test4.csv || echo "ERROR: status_code should be 0 for connection failure"

# Expected: All tests pass. Fix any failures before proceeding.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify complete workflow simulation

# Clean test environment
rm -rf /tmp/integration_test
mkdir -p /tmp/integration_test/data
cd /tmp/integration_test

# Run check twice to verify CSV append
python tools/monitor.py --url https://example.com --timeout 10
sleep 2
python tools/monitor.py --url https://example.com --timeout 10

# Verify CSV has header + 2 data rows
LINES=$(wc -l < data/uptime_log.csv)
test "$LINES" -eq 3 || echo "ERROR: Expected 3 lines (header + 2 rows), got $LINES"

# Verify timestamps are different (checks happened at different times)
TS1=$(sed -n '2p' data/uptime_log.csv | cut -d',' -f1)
TS2=$(sed -n '3p' data/uptime_log.csv | cut -d',' -f1)
test "$TS1" != "$TS2" || echo "ERROR: Timestamps should differ"

# Verify CSV format
python -c "
import csv, pathlib
rows = list(csv.DictReader(pathlib.Path('data/uptime_log.csv').open()))
assert len(rows) == 2, f'Expected 2 rows, got {len(rows)}'
assert 'timestamp' in rows[0], 'Missing timestamp column'
assert 'url' in rows[0], 'Missing url column'
assert 'status_code' in rows[0], 'Missing status_code column'
assert 'response_time_ms' in rows[0], 'Missing response_time_ms column'
assert 'is_up' in rows[0], 'Missing is_up column'
print('CSV format validated')
"

# Verify workflow.md documents this process
test -f workflow.md || echo "ERROR: workflow.md missing"
grep -q "Check URL" workflow.md || echo "ERROR: workflow.md missing 'Check URL' step"
grep -q "Log to CSV" workflow.md || echo "ERROR: workflow.md missing 'Log to CSV' step"

# Verify CLAUDE.md documents tool
test -f CLAUDE.md || echo "ERROR: CLAUDE.md missing"
grep -q "monitor.py" CLAUDE.md || echo "ERROR: CLAUDE.md missing monitor.py documentation"

# Verify .github/workflows/ exists and is valid
test -f .github/workflows/monitor.yml || echo "ERROR: monitor.yml missing"

# Expected: All checks pass. Integration test proves system works end-to-end.
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, no subagents needed, no MCPs, no secrets required
- [ ] .github/workflows/monitor.yml has cron schedule, concurrency setting, contents:write permission
- [ ] .env.example lists URL and TIMEOUT variables
- [ ] .gitignore excludes .env, __pycache__/, *.pyc
- [ ] README.md covers all three execution paths (CLI, Actions cron, Actions dispatch)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] requirements.txt lists requests==2.31.0
- [ ] CSV append logic creates directory and file automatically
- [ ] Exit codes correctly signal status (0=up, 1=down)
- [ ] Git commit message includes URL, status, response time, timestamp

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials (none needed for public URL monitoring)
- Do not use `git add -A` or `git add .` — stage only data/uptime_log.csv
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — catch requests.RequestException and specific exceptions
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools (this system uses requests library directly)
- Do not use subagents for single-tool linear workflows — overhead without benefit
- Do not use Agent Teams when no parallelization is possible — sequential is correct
- Do not commit .env files (none needed, but .env.example is OK)
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function
- Do not forget to validate URL includes protocol (common user error)
- Do not assume git push always succeeds — add retry logic if needed
- Do not use exit code 1 for success — exit code 0 is success (site up), 1 is failure (site down)

---

## Confidence Score: 10/10

**Score rationale:**
- **Requirements clarity**: High confidence — "simple website uptime checker" has one interpretation
- **Pattern selection**: High confidence — Monitor > Log is proven and documented in library/patterns.md
- **Tool implementation**: High confidence — requests library is reliable, CSV stdlib is stable
- **GitHub Actions integration**: High confidence — cron scheduling and git commits are well-understood
- **Testing approach**: High confidence — validation loop is comprehensive and executable
- **Reference system**: High confidence — systems/website-uptime-monitor/ provides working reference
- **No external dependencies**: High confidence — zero MCPs, zero APIs, zero external services
- **Cost model**: High confidence — GitHub Actions free tier covers this workload

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — all requirements are clear and unambiguous

**Ready to build:** Yes. This PRP has sufficient context for one-pass build success.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/website-uptime-checker.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.

---

## Notes

**Existing reference system:** A very similar system already exists at `systems/website-uptime-monitor/`. This PRP documents the same pattern with comprehensive validation gates and can either:
1. **Use existing system**: Deploy the existing system as-is (already built and tested)
2. **Build fresh**: Follow this PRP to build a new instance (useful for learning factory process)
3. **Extend existing**: Use this PRP to add features to the existing system (multiple URLs, alerting, dashboard)

The factory will detect the existing system during research and use it as a reference pattern.
