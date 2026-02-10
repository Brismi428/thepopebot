# Website Uptime Monitor — Operating Instructions

## System Identity

You are the **Website Uptime Monitor** — a lightweight, Git-native uptime monitoring system that checks a single website URL on a schedule and logs status to a CSV file. You run autonomously via GitHub Actions, require no external services, and provide full auditability through Git history.

## Purpose

Monitor the uptime and response time of a single HTTP/HTTPS endpoint every 5 minutes. Record all checks to a version-controlled CSV log. Provide historical data and at-a-glance status via GitHub Actions.

## Architecture

- **Execution Engine**: GitHub Actions with Python 3.11
- **Storage**: CSV file in Git repository (`logs/uptime_log.csv`)
- **Tool**: `tools/check_url.py` — HTTP check + CSV append
- **Schedule**: Every 5 minutes via GitHub Actions cron
- **Auditability**: Every check creates a Git commit

## Required Secrets & Environment Variables

### GitHub Repository Variables

Configure these in your repository settings (Settings → Secrets and variables → Actions → Variables):

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONITOR_URL` | The URL to monitor (http:// or https://) | Yes | `https://example.com` |
| `TIMEOUT_SECONDS` | HTTP request timeout in seconds | No | `10` |

### GitHub Secrets

| Secret | Description | Required |
|--------|-------------|----------|
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions | Yes (auto) |
| `ANTHROPIC_API_KEY` | Required only for Agent HQ (issue-driven execution) | No |

**Note**: The main monitoring workflow (`monitor.yml`) does NOT require `ANTHROPIC_API_KEY`. Only the Agent HQ workflow (`agent_hq.yml`) needs it for autonomous issue handling.

## How to Execute

### Execution Path 1: Scheduled (Primary Mode)

The system runs automatically every 5 minutes via GitHub Actions cron.

**Setup:**
1. Push this system to a GitHub repository
2. Configure `MONITOR_URL` repository variable
3. Optionally configure `TIMEOUT_SECONDS`
4. GitHub Actions will start running automatically

**Monitoring:**
- Go to Actions tab in your GitHub repository
- Look for "Website Uptime Monitor" workflow runs
- ✅ Green checkmark = site is up
- ❌ Red X = site is down or timeout

**Data Access:**
- View `logs/uptime_log.csv` in the repository
- Each row is one check with timestamp, URL, status code, response time, and up/down status
- Use Git history to track changes: `git log -- logs/uptime_log.csv`

### Execution Path 2: Manual Trigger

Run a one-time check on demand.

**Via GitHub Actions UI:**
1. Go to Actions tab
2. Select "Website Uptime Monitor" workflow
3. Click "Run workflow"
4. Optionally override the URL for a one-time check
5. Click "Run workflow" button

**Via GitHub CLI:**
```bash
gh workflow run monitor.yml \
  --repo OWNER/REPO \
  --field url="https://example.com" \
  --field timeout="10"
```

**Via API:**
```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/monitor.yml/dispatches \
  -d '{"ref":"main","inputs":{"url":"https://example.com","timeout":"10"}}'
```

### Execution Path 3: Local Testing

Run the tool locally for development and testing.

**Requirements:**
- Python 3.11+
- `pip install requests`

**Steps:**
```bash
# Set environment variables
export MONITOR_URL="https://example.com"
export TIMEOUT_SECONDS="10"

# Run the tool
python tools/check_url.py --url $MONITOR_URL --timeout $TIMEOUT_SECONDS --csv logs/uptime_log.csv

# Check the CSV
cat logs/uptime_log.csv

# View JSON output
python tools/check_url.py --url https://example.com | jq .
```

**Exit codes:**
- `0` - Site is up (status code < 400)
- `1` - Site is down (status code >= 400, timeout, or error)

### Execution Path 4: GitHub Agent HQ

Request tasks via GitHub Issues.

**Setup:**
1. Configure `ANTHROPIC_API_KEY` secret in repository settings
2. Open a new issue or comment on an existing issue
3. Mention `@claude` followed by your request

**Example tasks:**

```markdown
@claude Run a manual check of https://example.org
```

```markdown
@claude Analyze the uptime log for the past week and report any downtime patterns
```

```markdown
@claude Change the monitored URL to https://newsite.com and update the configuration
```

**How it works:**
1. Issue or comment triggers `agent_hq.yml` workflow
2. Claude reads the task, executes the appropriate action
3. Results are committed to a new branch
4. A draft PR is opened for review
5. Human reviews and merges the PR

## Workflow Execution

### Main Workflow: `tools/check_url.py`

**Process:**
1. Load configuration (URL and timeout from env vars or config file)
2. Execute HTTP GET request with timeout
3. Measure response time in milliseconds
4. Determine up/down status (< 400 = up, >= 400 = down)
5. Append result to `logs/uptime_log.csv` (create with headers if new)
6. Output JSON summary to stdout
7. Exit 0 if up, exit 1 if down

**Failure handling:**
- **Timeout**: Recorded as down with status_code=0, response_time=timeout*1000
- **Connection error**: Recorded as down with status_code=0, response_time=0
- **Other request errors**: Recorded as down with status_code=0, response_time=0
- **File write error**: Exit 1 with error message (GitHub Actions shows failed run)

### CSV Schema

The `logs/uptime_log.csv` file has the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp with UTC timezone (e.g., `2026-02-10T20:15:00+00:00`) |
| `url` | string | The URL that was checked |
| `status_code` | integer | HTTP status code (200, 404, 500, etc.) or 0 if timeout/error |
| `response_time_ms` | float | Response time in milliseconds, rounded to 2 decimal places |
| `is_up` | boolean | `True` if status_code < 400, `False` otherwise |

**Example CSV content:**
```csv
timestamp,url,status_code,response_time_ms,is_up
2026-02-10T20:00:00+00:00,https://example.com,200,145.32,True
2026-02-10T20:05:00+00:00,https://example.com,200,132.18,True
2026-02-10T20:10:00+00:00,https://example.com,503,5021.47,False
2026-02-10T20:15:00+00:00,https://example.com,0,10000.00,False
```

## Subagents

This system does not use subagents. It is a single-purpose tool with one task: check a URL and log the result. All logic is contained in `tools/check_url.py`.

## Agent Teams

This system does not use Agent Teams. There are no independent parallelizable tasks. The workflow is strictly sequential:
1. Check URL → 2. Log to CSV → 3. Commit

## MCP Requirements

This system does NOT require any MCPs. It uses standard Python libraries:
- `requests` — HTTP client (fallback to Python's `urllib` if needed)
- `csv` — CSV file handling (Python standard library)

**Why no MCPs?**
- **Simplicity**: For a single HTTP request and CSV append, direct library calls are simpler and more reliable
- **Zero dependencies**: No MCP server to maintain or configure
- **Portability**: Works anywhere Python and `requests` are available

## Tool Reference

### `tools/check_url.py`

**Purpose**: Check a URL and log the result to CSV.

**Usage:**
```bash
python tools/check_url.py --url <URL> --timeout <SECONDS> --csv <CSV_PATH>
```

**Arguments:**
- `--url` (required) — URL to check (or set `MONITOR_URL` env var)
- `--timeout` (optional) — Request timeout in seconds (default: 10, or `TIMEOUT_SECONDS` env var)
- `--csv` (optional) — Path to CSV log file (default: `logs/uptime_log.csv`)

**Returns:**
- JSON object to stdout with check results
- Exit code 0 if up, 1 if down

**Example:**
```bash
python tools/check_url.py --url https://example.com --timeout 5 --csv logs/uptime_log.csv
```

**Output:**
```json
{
  "timestamp": "2026-02-10T20:15:00+00:00",
  "url": "https://example.com",
  "status_code": 200,
  "response_time_ms": 145.32,
  "is_up": true,
  "csv_updated": "/path/to/logs/uptime_log.csv"
}
```

## Troubleshooting

### Issue: Workflow not running every 5 minutes

**Cause**: GitHub Actions cron has ±5 minute variance under load. This is a platform limitation.

**Solution**: Accept the variance. If exact timing is critical, consider self-hosted runners or a different platform.

### Issue: CSV file not being committed

**Cause**: Git push failure due to concurrent workflow runs.

**Solution**: The workflow includes retry logic (`git pull --rebase` then `git push`). If this persists, check the Actions logs for details. The `concurrency` setting in `monitor.yml` should prevent this.

### Issue: All checks showing as "down"

**Cause**: Timeout value is too low for the target URL, or the URL is genuinely unreachable.

**Solution**:
1. Increase `TIMEOUT_SECONDS` repository variable
2. Test the URL locally: `curl -I https://example.com`
3. Check if the target site blocks GitHub Actions IPs (set `User-Agent` header)

### Issue: Repository size growing too large

**Cause**: CSV file growing over time. At ~100 bytes per check, 8,640 checks/month = ~850 KB/month.

**Solution**:
1. Archive old data: Move entries older than N months to `logs/archive/YYYY-MM.csv`
2. Squash old commits: `git rebase -i` to combine historical commits
3. Use Git LFS for the CSV file (overkill for this use case)

### Issue: "ANTHROPIC_API_KEY not found" error

**Cause**: Agent HQ workflow requires Claude API access but secret is not configured.

**Solution**:
- If you don't need Agent HQ: Ignore this error (main monitoring workflow works without it)
- If you want Agent HQ: Add `ANTHROPIC_API_KEY` secret in repository settings

### Issue: False negatives (site is up but logged as down)

**Cause**: Temporary network issues, GitHub Actions runner connectivity problems, or legitimate brief outages.

**Solution**:
1. Check multiple consecutive checks to identify patterns
2. Increase timeout if the site is genuinely slow
3. Add retry logic (modify `tools/check_url.py` to retry failed requests)

## Data Analysis

### Basic Analysis

**Count total checks:**
```bash
wc -l logs/uptime_log.csv
# Subtract 1 for header row
```

**Count downtime events:**
```bash
grep ",False" logs/uptime_log.csv | wc -l
```

**Calculate uptime percentage:**
```bash
TOTAL=$(tail -n +2 logs/uptime_log.csv | wc -l)
UP=$(grep ",True" logs/uptime_log.csv | wc -l)
UPTIME=$(echo "scale=2; $UP / $TOTAL * 100" | bc)
echo "Uptime: ${UPTIME}%"
```

**Find slowest response times:**
```bash
tail -n +2 logs/uptime_log.csv | sort -t',' -k4 -n -r | head -n 10
```

### Advanced Analysis (Python/Pandas)

```python
import pandas as pd

# Load the CSV
df = pd.read_csv('logs/uptime_log.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Uptime percentage
uptime_pct = (df['is_up'].sum() / len(df)) * 100
print(f"Uptime: {uptime_pct:.2f}%")

# Average response time (when up)
avg_response = df[df['is_up']]['response_time_ms'].mean()
print(f"Avg response time: {avg_response:.2f}ms")

# Downtime events
downtime = df[~df['is_up']]
print(f"Total downtime events: {len(downtime)}")

# Downtime by status code
print("\nDowntime by status code:")
print(downtime['status_code'].value_counts())

# Daily uptime summary
df['date'] = df['timestamp'].dt.date
daily = df.groupby('date').agg({
    'is_up': ['sum', 'count'],
    'response_time_ms': 'mean'
})
print("\nDaily summary:")
print(daily)
```

## Extending the System

### Monitor Multiple URLs

**Option 1: Multiple workflow files**

Create `monitor-site1.yml`, `monitor-site2.yml`, etc., each with a different `MONITOR_URL` variable and schedule offset:

```yaml
# monitor-site1.yml
on:
  schedule:
    - cron: '*/5 * * * *'  # :00, :05, :10, :15, etc.

# monitor-site2.yml
on:
  schedule:
    - cron: '1-59/5 * * * *'  # :01, :06, :11, :16, etc.
```

**Option 2: Matrix strategy**

Modify `monitor.yml` to use a matrix strategy:

```yaml
jobs:
  check:
    strategy:
      matrix:
        url:
          - https://site1.com
          - https://site2.com
          - https://site3.com
    steps:
      - name: Run uptime check
        run: |
          python tools/check_url.py --url ${{ matrix.url }} --csv logs/uptime_${{ matrix.url }}.csv
```

### Add Alerting

**Option 1: Slack notification**

Add a step to `monitor.yml`:

```yaml
- name: Notify Slack on downtime
  if: steps.check.outputs.exit_code != '0'
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"🚨 Website down: '"$MONITOR_URL"'"}'
```

**Option 2: GitHub Issue**

Add a step to `monitor.yml`:

```yaml
- name: Open issue on downtime
  if: steps.check.outputs.exit_code != '0'
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `Website down: ${process.env.MONITOR_URL}`,
        body: 'Automated downtime alert from uptime monitor.',
        labels: ['downtime']
      });
```

### Add Authentication

Modify `tools/check_url.py` to accept authentication parameters:

```python
# Add arguments
parser.add_argument('--auth-header', help='Authorization header value')

# In check_url():
headers = {'User-Agent': 'WAT-Uptime-Monitor/1.0'}
if auth_header:
    headers['Authorization'] = auth_header

response = requests.get(url, timeout=timeout, headers=headers, ...)
```

Then set a GitHub Secret for the auth token and pass it in the workflow:

```yaml
- name: Run uptime check
  env:
    AUTH_TOKEN: ${{ secrets.API_AUTH_TOKEN }}
  run: |
    python tools/check_url.py --url $MONITOR_URL --auth-header "Bearer $AUTH_TOKEN"
```

## Cost & Resource Usage

### GitHub Actions Minutes

- Each check takes ~10 seconds to run
- At 5-minute intervals: 288 checks/day = 48 minutes/day
- Monthly: 48 × 30 = 1,440 minutes/month

**Free tier limits:**
- **Public repos**: Unlimited minutes
- **Private repos**: 2,000 minutes/month (free tier)

This system uses ~72% of the free tier for a single monitored URL.

### Repository Size

- Each check appends ~100 bytes to the CSV
- Each commit adds ~1 KB of Git metadata
- Monthly: 8,640 checks × 1.1 KB = ~9.5 MB/month
- Annual: ~114 MB/year

Git repositories handle this easily. Consider archiving or squashing commits after 1-2 years.

### API Rate Limits

This system makes no API calls (other than the monitored URL itself). No rate limit concerns.

## Maintenance

### Weekly

- Check the Actions tab for any failed runs
- Review recent CSV entries for anomalies

### Monthly

- Review uptime percentage
- Analyze response time trends
- Check repository size (if it's growing unexpectedly)

### Quarterly

- Archive old CSV data if desired
- Review and update `MONITOR_URL` if target site has changed
- Update dependencies: `pip install --upgrade requests`

### Annually

- Squash old commits to reduce repo size
- Review and update this documentation
- Consider upgrading Python version in workflow

## Security Notes

- **No secrets in code**: All configuration via environment variables and GitHub Secrets
- **Minimal permissions**: Workflow uses default `GITHUB_TOKEN` with write access only to the repository
- **No external services**: System does not send data anywhere except the monitored URL and GitHub
- **Public data**: CSV is committed to the repository — do not monitor URLs that leak sensitive data in responses

## Support & Feedback

This system was generated by the WAT Systems Factory. For issues, enhancements, or questions:

1. Open a GitHub Issue in this repository
2. Use Agent HQ: mention `@claude` in an issue with your question
3. Refer to `workflow.md` for detailed process documentation
4. Check GitHub Actions logs for execution details
