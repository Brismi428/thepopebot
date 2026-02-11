name: "RSS Digest Monitor"
description: |
  Daily email digest system that monitors multiple RSS feeds, tracks new posts, and delivers formatted HTML summaries via SMTP

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
Build an autonomous RSS feed monitoring system that checks multiple RSS/Atom feeds daily at 8 AM UTC, identifies posts published since the last run, groups them by feed source, and delivers a formatted HTML email digest via SMTP. The system must maintain state between runs to track which posts have been seen, handle feed errors gracefully, and work without human intervention.

## Why
- **Automation**: Eliminates manual RSS reader checking across multiple sources
- **Consolidation**: One daily email instead of fragmented feed reader notifications
- **Time savings**: Users get curated updates at a predictable time without constant monitoring
- **Reliability**: GitHub Actions ensures consistent daily execution without a server
- **User impact**: Content consumers, researchers, and teams monitoring multiple sources daily

## What
A stateful RSS monitoring pipeline that fetches feeds, deduplicates against previous runs, formats new content into an HTML email digest grouped by source, and delivers via SMTP. Results are tracked in a Git-committed state file, providing auditability and recovery.

### Success Criteria
- [ ] System fetches multiple RSS/Atom feeds without failing the entire run if one feed is down
- [ ] New posts are correctly identified by comparing against state file (last run timestamp + seen GUIDs)
- [ ] Email digest is sent via SMTP with HTML formatting, grouped by feed source
- [ ] Each digest entry includes: feed name, post title (linked), summary/description, publish date
- [ ] State file is updated and committed after successful email send
- [ ] System runs autonomously via GitHub Actions on schedule (daily at 8 AM UTC)
- [ ] If no new posts, no email is sent (silent run with state update)
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs
[What goes into the system. Be specific about format, source, and any validation requirements.]

```yaml
- name: "feeds_config"
  type: "JSON file"
  source: "config/feeds.json in the repository"
  required: true
  description: "List of RSS/Atom feed URLs with display names and optional tags"
  example: |
    {
      "feeds": [
        {
          "name": "Hacker News",
          "url": "https://news.ycombinator.com/rss",
          "tags": ["tech", "news"]
        },
        {
          "name": "GitHub Blog",
          "url": "https://github.blog/feed/",
          "tags": ["dev", "github"]
        }
      ]
    }

- name: "email_recipients"
  type: "list of strings"
  source: "SMTP_TO environment variable (comma-separated) or config file"
  required: true
  description: "Email addresses to receive the digest"
  example: "user@example.com,team@example.com"

- name: "smtp_config"
  type: "environment variables"
  source: "GitHub Secrets"
  required: true
  description: "SMTP server configuration for email delivery"
  example: |
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=notifications@example.com
    SMTP_PASS=app_password
    SMTP_FROM=RSS Digest <notifications@example.com>
    SMTP_TO=recipient@example.com

- name: "state_file"
  type: "JSON file"
  source: "state/rss_state.json in the repository"
  required: false (created on first run)
  description: "Tracks last run timestamp and seen post GUIDs to prevent duplicates"
  example: |
    {
      "last_run": "2026-02-11T08:00:00Z",
      "seen_guids": [
        "https://news.ycombinator.com/item?id=12345",
        "https://github.blog/post-slug/"
      ]
    }
```

## Outputs
[What comes out of the system. Where do results go?]

```yaml
- name: "html_email_digest"
  type: "HTML email"
  destination: "SMTP recipients configured in environment"
  description: "Formatted HTML email with posts grouped by feed, including title, link, summary, date"
  example: |
    Subject: RSS Digest - February 11, 2026 (5 new posts)
    
    [HTML body with sections per feed, styled table/cards of posts]

- name: "updated_state_file"
  type: "JSON file"
  destination: "state/rss_state.json committed to repository"
  description: "Updated state file with new timestamp and seen GUIDs"
  example: |
    {
      "last_run": "2026-02-11T08:00:00Z",
      "seen_guids": ["guid1", "guid2", "guid3", ...]
    }

- name: "run_summary"
  type: "JSON file"
  destination: "logs/YYYY-MM-DD_run.json committed to repository"
  description: "Summary of the run: feeds checked, new posts found, email sent status"
  example: |
    {
      "timestamp": "2026-02-11T08:05:23Z",
      "feeds_checked": 5,
      "feeds_failed": 1,
      "new_posts": 12,
      "email_sent": true,
      "failed_feeds": ["https://broken-feed.example/rss"]
    }
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://feedparser.readthedocs.io/"
  why: "Standard Python library for parsing RSS/Atom feeds - handles malformed XML, encoding issues, all feed formats"

- url: "https://docs.python.org/3/library/email.mime.html"
  why: "Python email composition for multipart HTML emails with plain-text fallback"

- url: "https://docs.python.org/3/library/smtplib.html"
  why: "SMTP client for email delivery with TLS support"

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide HTTP fetch capabilities (Fetch MCP) - fallback to requests"

- doc: "library/patterns.md"
  why: "This is a Monitor > Collect > Transform > Deliver pattern with state persistence"

- doc: "library/tool_catalog.md"
  why: "Reuse rest_client pattern for HTTP fallback, json_read_write for state management, email_send pattern"
```

### Workflow Pattern Selection
```yaml
pattern: "Monitor > Collect > Transform > Deliver (with state persistence)"
rationale: |
  - Monitor: Check RSS feeds on schedule (GitHub Actions cron)
  - Collect: Fetch all configured feeds, parse entries
  - Transform: Filter new posts, group by source, format as HTML
  - Deliver: Send email digest via SMTP
  State persistence is critical to avoid resending posts across runs.
modifications: |
  - Add state loading before Collect
  - Add state saving after Deliver
  - Add per-feed error handling (one feed failure doesn't kill the run)
  - Add conditional delivery (skip email if no new posts)
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "HTTP fetch for RSS feeds"
    primary_mcp: "fetch"
    alternative_mcp: "none"
    fallback: "Python requests library with User-Agent header and timeout"
    secret_name: "none"

  - name: "Email delivery"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "Python smtplib with TLS - standard library, no MCP needed"
    secret_name: "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TO"

  - name: "JSON state persistence"
    primary_mcp: "filesystem"
    alternative_mcp: "none"
    fallback: "Python pathlib + json.loads/dumps - stdlib only"
    secret_name: "none"
```

### Known Gotchas & Constraints
```
# CRITICAL: RSS feeds can return HTTP 429 (rate limit) - must handle gracefully with exponential backoff
# CRITICAL: feedparser normalizes all feed formats (RSS 1.0, 2.0, Atom) but some feeds have malformed XML - must handle parsing errors per-feed
# CRITICAL: Feed entry GUIDs are not always globally unique - use (feed_url + guid) as composite key
# CRITICAL: Feed publish dates can be missing, malformed, or in the future - must handle date parsing with fallback to current time
# CRITICAL: SMTP authentication varies by provider (Gmail requires App Password, not account password)
# CRITICAL: State file must be committed AFTER successful email send to avoid losing track of seen posts on failure
# CRITICAL: HTML email must include plain-text fallback for email clients that don't render HTML
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: feedparser library automatically handles character encoding issues and malformed XML - use it instead of raw XML parsing
# CRITICAL: Some feeds include full content in <description>, others only summaries - truncate if too long (300 chars)
```

---

## System Design

### Subagent Architecture
[Define the specialist subagents this system needs. One subagent per major capability or workflow phase.]

```yaml
subagents:
  - name: "rss-fetcher-specialist"
    description: "Delegate when fetching and parsing RSS/Atom feeds from URLs. Handles HTTP errors, feed parsing, and data normalization."
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Fetch RSS/Atom feeds from configured URLs using feedparser"
      - "Handle per-feed HTTP errors gracefully (timeouts, 404, 429, 500)"
      - "Parse feed entries and normalize to common schema (title, link, summary, date, guid)"
      - "Return structured feed data with error flags for failed feeds"
    inputs: "List of feed configs (name, url, tags) from config/feeds.json"
    outputs: "List of feed results, each with entries list or error status"

  - name: "digest-generator-specialist"
    description: "Delegate when formatting new posts into HTML email digest. Handles grouping, HTML generation, and plain-text fallback."
    tools: "Read, Write"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Group new posts by feed source"
      - "Generate HTML email body with styled sections per feed"
      - "Create plain-text fallback version"
      - "Generate email subject line with new post count"
    inputs: "List of new posts (grouped by feed) with metadata (title, link, summary, date)"
    outputs: "MIME multipart email object with HTML and plain-text parts"

  - name: "state-manager-specialist"
    description: "Delegate when loading or saving RSS monitoring state. Handles state file I/O, guid tracking, and timestamp management."
    tools: "Read, Write, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Load state file (last_run timestamp, seen_guids list) or initialize if missing"
      - "Filter posts by comparing publish date and guid against state"
      - "Update state with new timestamp and seen guids after successful email send"
      - "Commit state file to repository"
    inputs: "state/rss_state.json (or creates if missing), list of current feed entries"
    outputs: "Filtered new posts list, updated state object for persistence"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "Fetch feed 1 via HTTP GET + parse XML"
  - "Fetch feed 2 via HTTP GET + parse XML"
  - "Fetch feed 3 via HTTP GET + parse XML"
  # (N feeds = N independent tasks)

independent_task_count: "N (number of configured feeds, typically 3-20)"
recommendation: "Sequential execution (do NOT use Agent Teams)"
rationale: |
  While feed fetching is technically parallelizable, the tasks complete quickly (1-3s each),
  and the state comparison step requires all feeds to be fetched first (sequential dependency).
  Agent Teams adds token cost and complexity for minimal wall-time benefit on small feed lists.
  
  For users monitoring 20+ feeds, parallel fetch could be a future optimization, but the
  system should start with sequential fetch as the default. GitHub Actions has generous
  timeout limits (6 hours default), so even 50 feeds at 3s each = 2.5 minutes total.

sequential_rationale: |
  1. Fetch all feeds (sequential loop) - 10-30 seconds for typical 5-10 feeds
  2. Load state and filter new posts (depends on all fetches completing)
  3. Generate digest (depends on filtered posts)
  4. Send email (depends on digest)
  5. Save state (depends on successful email send)
  
  All steps have clear sequential dependencies. No parallelization opportunity that
  justifies Agent Teams overhead.
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "schedule"
    config: "cron: '0 8 * * *'  # Daily at 8 AM UTC"
    description: "Primary trigger - runs every day at 8 AM UTC to check for new posts since last run"

  - type: "workflow_dispatch"
    config: |
      inputs:
        force_send:
          description: 'Send digest even if no new posts (for testing)'
          required: false
          default: 'false'
    description: "Manual trigger for testing or on-demand digest generation"

  - type: "repository_dispatch (optional future enhancement)"
    config: "event_type: 'rss_check_now'"
    description: "Webhook trigger for immediate check (e.g., from another workflow or external service)"
```

---

## Implementation Blueprint

### Workflow Steps
[Ordered list of workflow phases. Each step becomes a section in workflow.md.]

```yaml
steps:
  - name: "Load State"
    description: "Read state/rss_state.json to get last_run timestamp and seen_guids list. Initialize empty state if file doesn't exist (first run)."
    subagent: "state-manager-specialist"
    tools: ["load_state.py"]
    inputs: "state/rss_state.json (or none on first run)"
    outputs: "State object: {last_run: ISO timestamp, seen_guids: [list]}"
    failure_mode: "State file is corrupted or unparseable JSON"
    fallback: "Log warning, initialize empty state {last_run: null, seen_guids: []}, proceed with full feed history"

  - name: "Fetch RSS Feeds"
    description: "Iterate through config/feeds.json, fetch each feed URL via HTTP GET with feedparser, parse entries. Handle per-feed errors gracefully."
    subagent: "rss-fetcher-specialist"
    tools: ["fetch_rss_feeds.py"]
    inputs: "config/feeds.json (list of {name, url, tags})"
    outputs: "List of feed results: [{feed_name, feed_url, entries: [{title, link, summary, published, guid}], error: null | str}]"
    failure_mode: "Individual feed is unreachable (HTTP error, timeout, malformed XML)"
    fallback: "Log error for that feed, mark as error: 'HTTP 404' or 'Parse error', continue with remaining feeds. Do NOT fail entire run."

  - name: "Filter New Posts"
    description: "Compare fetched entries against state.seen_guids. Filter entries where (feed_url + guid) not in seen_guids AND published >= state.last_run (or all if first run)."
    subagent: "state-manager-specialist"
    tools: ["filter_new_posts.py"]
    inputs: "Feed results from step 2, state object from step 1"
    outputs: "List of new posts: [{feed_name, title, link, summary, published, guid, feed_url}], new_guids list"
    failure_mode: "Published date is missing or unparseable"
    fallback: "Use current timestamp as published date, log warning, include post (better to duplicate than miss)"

  - name: "Generate HTML Digest"
    description: "Group new posts by feed_name. Generate HTML email body with sections per feed, styled post cards. Create plain-text fallback. Generate subject line."
    subagent: "digest-generator-specialist"
    tools: ["generate_html_digest.py"]
    inputs: "List of new posts (already filtered), current date for subject line"
    outputs: "MIME multipart email object with Subject, HTML part, plain-text part"
    failure_mode: "No new posts (empty list)"
    fallback: "Return None - skip email send, proceed to state update with no changes to seen_guids"

  - name: "Send Email via SMTP"
    description: "Connect to SMTP server (SMTP_HOST:SMTP_PORT), authenticate (SMTP_USER, SMTP_PASS), send digest to SMTP_TO recipients. Use TLS."
    subagent: "none (main agent handles)"
    tools: ["send_email_smtp.py"]
    inputs: "MIME email object from step 4, SMTP credentials from environment"
    outputs: "Success status: {sent: true, message_id: str} or {sent: false, error: str}"
    failure_mode: "SMTP authentication failure, network error, recipient rejection"
    fallback: "Retry once with 30s delay. If still fails, log error and exit non-zero. DO NOT update state if email fails - posts will retry next run."

  - name: "Update State"
    description: "Update state object: set last_run to current timestamp, append new_guids to seen_guids (keep last 10,000 to prevent unbounded growth). Write to state/rss_state.json."
    subagent: "state-manager-specialist"
    tools: ["save_state.py"]
    inputs: "State object, new_guids list from step 3, current timestamp"
    outputs: "Updated state/rss_state.json file"
    failure_mode: "File write permission error, disk full"
    fallback: "Log error and exit non-zero. State is not committed. Next run will retry same posts (acceptable failure mode - better than losing state)."

  - name: "Commit State to Repo"
    description: "Stage state/rss_state.json and logs/YYYY-MM-DD_run.json, commit with message, push to origin."
    subagent: "none (main agent handles)"
    tools: ["git_commit_push.py (from tool_catalog)"]
    inputs: "state/rss_state.json, logs/ directory"
    outputs: "Git commit SHA"
    failure_mode: "Git conflict (concurrent run), push rejection"
    fallback: "Pull with rebase, retry commit. If fails after 2 attempts, log error but exit 0 (state was saved locally, will sync next run)."
```

### Tool Specifications
[For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.]

```yaml
tools:
  - name: "load_state.py"
    purpose: "Load RSS state file (last run timestamp and seen GUIDs) or initialize empty state on first run"
    catalog_pattern: "json_read_write (adapted)"
    inputs:
      - "state_file_path: str — Path to state JSON file (default: state/rss_state.json)"
    outputs: "JSON object: {last_run: ISO timestamp or null, seen_guids: [list]}"
    dependencies: ["json (stdlib)", "pathlib (stdlib)"]
    mcp_used: "filesystem (optional) or stdlib pathlib"
    error_handling: "FileNotFoundError -> return empty state. JSONDecodeError -> log warning, return empty state."

  - name: "fetch_rss_feeds.py"
    purpose: "Fetch and parse multiple RSS/Atom feeds, handling per-feed errors gracefully"
    catalog_pattern: "rest_client (for HTTP fetch) + custom RSS parsing"
    inputs:
      - "feeds_config: list[dict] — [{name, url, tags}] from config/feeds.json"
      - "timeout: int — HTTP timeout per feed (default: 15 seconds)"
    outputs: "JSON: {feeds: [{name, url, entries: [{title, link, summary, published, guid}], error: str or null}]}"
    dependencies: ["feedparser", "httpx (or requests)", "logging"]
    mcp_used: "fetch (optional) or requests library"
    error_handling: "Per-feed try/except. HTTPError, Timeout, ParseError -> set feed.error, continue. Log all errors."

  - name: "filter_new_posts.py"
    purpose: "Compare fetched posts against state, identify new posts since last run"
    catalog_pattern: "filter_sort (adapted) + custom guid deduplication"
    inputs:
      - "feed_results: dict — Output from fetch_rss_feeds.py"
      - "state: dict — {last_run, seen_guids} from load_state.py"
    outputs: "JSON: {new_posts: [{feed_name, title, link, summary, published, guid, feed_url}], new_guids: [list]}"
    dependencies: ["dateutil.parser (for robust date parsing)"]
    mcp_used: "none"
    error_handling: "Unparseable date -> use current timestamp. Missing guid -> generate from link. Log warnings."

  - name: "generate_html_digest.py"
    purpose: "Generate HTML email digest grouped by feed, with plain-text fallback"
    catalog_pattern: "new (HTML email generation pattern)"
    inputs:
      - "new_posts: list[dict] — Filtered posts from filter_new_posts.py"
      - "current_date: str — For email subject line"
    outputs: "MIME multipart email object (or None if no posts)"
    dependencies: ["email.mime.multipart", "email.mime.text", "jinja2 (optional for HTML templating)"]
    mcp_used: "none"
    error_handling: "Empty posts list -> return None. Truncate long summaries to 300 chars. Handle missing fields gracefully."

  - name: "send_email_smtp.py"
    purpose: "Send email via SMTP with TLS authentication"
    catalog_pattern: "email_send (from tool_catalog)"
    inputs:
      - "email_message: MIMEMultipart — From generate_html_digest.py"
      - "smtp_config: dict — {host, port, user, pass, from, to} from environment variables"
    outputs: "JSON: {sent: bool, message_id: str, error: str or null}"
    dependencies: ["smtplib (stdlib)", "email (stdlib)"]
    mcp_used: "none"
    error_handling: "SMTPAuthenticationError, SMTPException, socket.error -> retry once after 30s. Log error, raise on second failure."

  - name: "save_state.py"
    purpose: "Update state file with new timestamp and seen GUIDs, enforce max size"
    catalog_pattern: "json_read_write (write mode)"
    inputs:
      - "state: dict — Current state object"
      - "new_guids: list[str] — GUIDs from this run"
      - "current_timestamp: str — ISO format timestamp"
      - "max_guids: int — Maximum seen_guids to retain (default: 10000)"
    outputs: "Updated state/rss_state.json file"
    dependencies: ["json (stdlib)", "pathlib (stdlib)"]
    mcp_used: "filesystem (optional) or stdlib"
    error_handling: "IOError -> log error, raise. Enforce max_guids by keeping most recent entries only."
```

### Per-Tool Pseudocode
```python
# load_state.py
def main(state_file_path: str = "state/rss_state.json") -> dict:
    # PATTERN: json_read_write (read mode with initialization fallback)
    # Step 1: Check if state file exists
    path = pathlib.Path(state_file_path)
    if not path.exists():
        return {"last_run": None, "seen_guids": []}
    
    # Step 2: Load and parse JSON
    try:
        data = json.loads(path.read_text())
        return data
    except json.JSONDecodeError:
        logging.warning("State file corrupted, initializing empty state")
        return {"last_run": None, "seen_guids": []}

# fetch_rss_feeds.py
def main(feeds_config: list[dict], timeout: int = 15) -> dict:
    # PATTERN: rest_client + feedparser
    # CRITICAL: Handle per-feed errors gracefully - one feed failure must not kill the run
    import feedparser
    results = []
    for feed in feeds_config:
        try:
            # User-Agent header prevents some feeds from blocking
            parsed = feedparser.parse(feed["url"], 
                                     request_headers={"User-Agent": "RSS-Digest-Monitor/1.0"})
            if parsed.bozo:  # feedparser sets bozo=1 if malformed XML
                logging.warning(f"Feed {feed['name']} has malformed XML: {parsed.bozo_exception}")
            
            entries = [{
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", entry.get("description", ""))[:300],
                "published": entry.get("published", entry.get("updated", "")),
                "guid": entry.get("id", entry.get("link", ""))
            } for entry in parsed.entries]
            
            results.append({
                "name": feed["name"],
                "url": feed["url"],
                "entries": entries,
                "error": None
            })
        except Exception as e:
            logging.error(f"Failed to fetch {feed['name']}: {e}")
            results.append({
                "name": feed["name"],
                "url": feed["url"],
                "entries": [],
                "error": str(e)
            })
    return {"feeds": results}

# filter_new_posts.py
def main(feed_results: dict, state: dict) -> dict:
    # PATTERN: filter_sort + custom deduplication
    # CRITICAL: Use (feed_url + guid) as composite key - GUIDs not globally unique
    from dateutil import parser as dateparser
    
    seen_guids = set(state.get("seen_guids", []))
    last_run = state.get("last_run")
    if last_run:
        last_run_dt = dateparser.parse(last_run)
    else:
        last_run_dt = None  # First run - include all posts
    
    new_posts = []
    new_guids = []
    
    for feed in feed_results["feeds"]:
        if feed["error"]:
            continue  # Skip failed feeds
        for entry in feed["entries"]:
            composite_guid = f"{feed['url']}::{entry['guid']}"
            
            # Check if seen before
            if composite_guid in seen_guids:
                continue
            
            # Check if published since last run
            if last_run_dt:
                try:
                    published_dt = dateparser.parse(entry["published"])
                    if published_dt < last_run_dt:
                        continue
                except Exception:
                    logging.warning(f"Unparseable date for {entry['title']}, including anyway")
            
            new_posts.append({
                "feed_name": feed["name"],
                "title": entry["title"],
                "link": entry["link"],
                "summary": entry["summary"],
                "published": entry["published"],
                "guid": entry["guid"],
                "feed_url": feed["url"]
            })
            new_guids.append(composite_guid)
    
    return {"new_posts": new_posts, "new_guids": new_guids}

# generate_html_digest.py
def main(new_posts: list[dict], current_date: str) -> MIMEMultipart | None:
    # PATTERN: HTML email generation (new)
    # CRITICAL: Include plain-text fallback for email clients without HTML
    if not new_posts:
        return None
    
    # Group by feed
    from itertools import groupby
    grouped = {}
    for post in sorted(new_posts, key=lambda p: p["feed_name"]):
        if post["feed_name"] not in grouped:
            grouped[post["feed_name"]] = []
        grouped[post["feed_name"]].append(post)
    
    # Generate HTML
    html_body = f"<html><body><h1>RSS Digest - {current_date}</h1>"
    text_body = f"RSS Digest - {current_date}\n\n"
    
    for feed_name, posts in grouped.items():
        html_body += f"<h2>{feed_name}</h2><ul>"
        text_body += f"\n{feed_name}\n" + "="*len(feed_name) + "\n"
        for post in posts:
            html_body += f"""
            <li>
                <strong><a href="{post['link']}">{post['title']}</a></strong><br>
                {post['summary']}<br>
                <small>{post['published']}</small>
            </li>
            """
            text_body += f"\n• {post['title']}\n  {post['link']}\n  {post['summary']}\n  {post['published']}\n"
        html_body += "</ul>"
    
    html_body += "</body></html>"
    
    # Create MIME message
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"RSS Digest - {current_date} ({len(new_posts)} new posts)"
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    
    return msg

# send_email_smtp.py
def main(email_message: MIMEMultipart, smtp_config: dict) -> dict:
    # PATTERN: email_send from tool_catalog
    # CRITICAL: Use TLS. Gmail requires App Password, not account password.
    import smtplib
    from email.mime.multipart import MIMEMultipart
    
    email_message["From"] = smtp_config["from"]
    email_message["To"] = smtp_config["to"]
    
    try:
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            server.login(smtp_config["user"], smtp_config["pass"])
            server.send_message(email_message)
            return {"sent": True, "message_id": email_message.get("Message-ID", ""), "error": None}
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP auth failed: {e}")
        return {"sent": False, "message_id": "", "error": f"Authentication failed: {e}"}
    except Exception as e:
        logging.error(f"SMTP send failed: {e}")
        return {"sent": False, "message_id": "", "error": str(e)}

# save_state.py
def main(state: dict, new_guids: list[str], current_timestamp: str, 
         max_guids: int = 10000, state_file_path: str = "state/rss_state.json") -> None:
    # PATTERN: json_read_write (write mode)
    # CRITICAL: Enforce max_guids to prevent unbounded state file growth
    import json
    import pathlib
    
    updated_guids = state.get("seen_guids", []) + new_guids
    # Keep most recent max_guids entries
    if len(updated_guids) > max_guids:
        updated_guids = updated_guids[-max_guids:]
    
    updated_state = {
        "last_run": current_timestamp,
        "seen_guids": updated_guids
    }
    
    path = pathlib.Path(state_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(updated_state, indent=2))
```

### Integration Points
```yaml
SECRETS:
  - name: "SMTP_HOST"
    purpose: "SMTP server hostname (e.g., smtp.gmail.com)"
    required: true

  - name: "SMTP_PORT"
    purpose: "SMTP server port (typically 587 for TLS)"
    required: true

  - name: "SMTP_USER"
    purpose: "SMTP authentication username (email address)"
    required: true

  - name: "SMTP_PASS"
    purpose: "SMTP authentication password (use App Password for Gmail)"
    required: true

  - name: "SMTP_FROM"
    purpose: "From address for digest emails (e.g., RSS Digest <notify@example.com>)"
    required: true

  - name: "SMTP_TO"
    purpose: "Comma-separated list of recipient email addresses"
    required: true

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "SMTP_HOST=smtp.gmail.com  # SMTP server hostname"
      - "SMTP_PORT=587  # SMTP port (587 for TLS)"
      - "SMTP_USER=your-email@gmail.com  # SMTP auth username"
      - "SMTP_PASS=your-app-password  # SMTP auth password (use App Password for Gmail)"
      - "SMTP_FROM=RSS Digest <your-email@gmail.com>  # From address"
      - "SMTP_TO=recipient@example.com  # Comma-separated recipients"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "feedparser==6.0.11  # Universal RSS/Atom feed parser"
      - "python-dateutil==2.8.2  # Robust date parsing"
      - "httpx==0.27.0  # HTTP client (optional, fallback to requests)"

GITHUB_ACTIONS:
  - trigger: "schedule"
    config: "cron: '0 8 * * *'  # Daily at 8 AM UTC"
  - trigger: "workflow_dispatch"
    config: "Manual trigger with optional force_send input"
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/load_state.py').read())"
python -c "import ast; ast.parse(open('tools/fetch_rss_feeds.py').read())"
python -c "import ast; ast.parse(open('tools/filter_new_posts.py').read())"
python -c "import ast; ast.parse(open('tools/generate_html_digest.py').read())"
python -c "import ast; ast.parse(open('tools/send_email_smtp.py').read())"
python -c "import ast; ast.parse(open('tools/save_state.py').read())"

# Import check — verify no missing dependencies
python -c "import importlib; importlib.import_module('tools.load_state')"
python -c "import importlib; importlib.import_module('tools.fetch_rss_feeds')"
python -c "import importlib; importlib.import_module('tools.filter_new_posts')"
python -c "import importlib; importlib.import_module('tools.generate_html_digest')"
python -c "import importlib; importlib.import_module('tools.send_email_smtp')"
python -c "import importlib; importlib.import_module('tools.save_state')"

# Structure check — verify main() exists
python -c "from tools.load_state import main; assert callable(main)"
python -c "from tools.fetch_rss_feeds import main; assert callable(main)"
python -c "from tools.filter_new_posts import main; assert callable(main)"
python -c "from tools.generate_html_digest import main; assert callable(main)"
python -c "from tools.send_email_smtp import main; assert callable(main)"
python -c "from tools.save_state import main; assert callable(main)"

# Subagent YAML validation
python -c "import yaml; yaml.safe_load(open('.claude/agents/rss-fetcher-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/digest-generator-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/state-manager-specialist.md').read().split('---')[1])"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test each tool independently with mock/sample data

# Test 1: load_state with missing file (first run scenario)
rm -f /tmp/test_state.json
python tools/load_state.py /tmp/test_state.json
# Expected output: {"last_run": null, "seen_guids": []}

# Test 2: fetch_rss_feeds with real feed (Hacker News RSS)
echo '[{"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "tags": ["tech"]}]' > /tmp/feeds.json
python tools/fetch_rss_feeds.py /tmp/feeds.json
# Expected output: JSON with feeds array, entries list with title/link/summary/published/guid
# Verify: entries is not empty, no errors

# Test 3: filter_new_posts with sample data
# (Requires sample feed_results JSON and state JSON - create fixtures)
python tools/filter_new_posts.py /tmp/feed_results.json /tmp/state.json
# Expected output: JSON with new_posts array and new_guids array

# Test 4: generate_html_digest with sample posts
echo '[{"feed_name": "Test Feed", "title": "Test Post", "link": "https://example.com", "summary": "Test summary", "published": "2026-02-11T08:00:00Z", "guid": "test1", "feed_url": "https://example.com/rss"}]' > /tmp/posts.json
python tools/generate_html_digest.py /tmp/posts.json "2026-02-11"
# Expected output: MIME email object with Subject, HTML part, plain-text part

# Test 5: send_email_smtp with test SMTP server (skip if no test SMTP available)
# Requires SMTP_* environment variables to be set
# python tools/send_email_smtp.py /tmp/email.eml
# Expected output: {"sent": true, "message_id": "...", "error": null}

# Test 6: save_state with sample data
python tools/save_state.py /tmp/state.json '["guid1", "guid2"]' "2026-02-11T08:00:00Z"
cat /tmp/state.json
# Expected output: File contains {"last_run": "2026-02-11T08:00:00Z", "seen_guids": ["guid1", "guid2"]}

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with sample data

# Setup: Create sample config and state
mkdir -p /tmp/rss_test/state /tmp/rss_test/config
echo '{"feeds": [{"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "tags": ["tech"]}]}' > /tmp/rss_test/config/feeds.json
echo '{"last_run": null, "seen_guids": []}' > /tmp/rss_test/state/rss_state.json

# Step 1: Load state
python tools/load_state.py /tmp/rss_test/state/rss_state.json > /tmp/rss_test/state.json

# Step 2: Fetch feeds
python tools/fetch_rss_feeds.py /tmp/rss_test/config/feeds.json > /tmp/rss_test/feed_results.json

# Step 3: Filter new posts
python tools/filter_new_posts.py /tmp/rss_test/feed_results.json /tmp/rss_test/state.json > /tmp/rss_test/new_posts.json

# Step 4: Generate digest (only if new posts exist)
python -c "
import json, sys
posts = json.load(open('/tmp/rss_test/new_posts.json'))
if posts['new_posts']:
    sys.exit(0)
else:
    print('No new posts - skipping digest')
    sys.exit(1)
" && python tools/generate_html_digest.py /tmp/rss_test/new_posts.json "2026-02-11" > /tmp/rss_test/digest.eml

# Step 5: Verify output structure
python -c "
import json
new_posts = json.load(open('/tmp/rss_test/new_posts.json'))
assert 'new_posts' in new_posts, 'Missing new_posts key'
assert 'new_guids' in new_posts, 'Missing new_guids key'
print('✓ Pipeline integration test passed')
"

# Verify workflow.md references match actual tool files
grep -E "(load_state|fetch_rss_feeds|filter_new_posts|generate_html_digest|send_email_smtp|save_state)\.py" workflow.md
# Expected: All tools mentioned in workflow exist as files

# Verify CLAUDE.md documents all tools and subagents
grep -E "(load_state|fetch_rss_feeds|filter_new_posts|generate_html_digest|send_email_smtp|save_state)" CLAUDE.md
grep -E "(rss-fetcher-specialist|digest-generator-specialist|state-manager-specialist)" CLAUDE.md
# Expected: All tools and subagents are documented

# Verify .github/workflows/ YAML is valid
python -c "import yaml; yaml.safe_load(open('.github/workflows/monitor.yml'))"
# Expected: Valid YAML, no parse errors
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
- [ ] .gitignore excludes .env, __pycache__/, state/*.json (except example)
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies
- [ ] State file includes .gitignore exception comment explaining why state/ is tracked
- [ ] Email digest includes plain-text fallback for non-HTML email clients
- [ ] Per-feed error handling prevents single feed failure from killing entire run

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets
- Do not use `git add -A` or `git add .` — stage only specific files (state/rss_state.json, logs/)
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not create MCP-dependent tools without HTTP/API fallbacks — feedparser + requests is the fallback
- Do not fail the entire run if one RSS feed is down — handle per-feed errors gracefully
- Do not send email if no new posts — silent run with state update only
- Do not update state before email is successfully sent — posts will be lost if email fails
- Do not let seen_guids grow unbounded — enforce max size (10,000 recommended)
- Do not use feed entry GUID alone as deduplication key — use composite (feed_url + guid)
- Do not crash on unparseable dates — use current timestamp as fallback
- Do not send HTML-only emails — always include plain-text fallback part
- Do not commit .env files, credentials, or SMTP passwords to the repository
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function

---

## Confidence Score: 9/10

**Score rationale:**
- [Workflow Pattern]: High confidence — this is a well-understood Monitor > Transform > Deliver pattern with clear state persistence requirements. Pattern selection is solid.
- [Tool Design]: High confidence — feedparser is battle-tested, SMTP is stdlib, state management is straightforward JSON. All tools have clear inputs/outputs and proven patterns.
- [Error Handling]: High confidence — per-feed error isolation, retry logic for SMTP, state rollback on failure. Failure modes are well-defined.
- [MCP/Library Requirements]: High confidence — feedparser handles RSS/Atom normalization, smtplib is stdlib, no exotic dependencies. Fallbacks are clear.
- [Validation Strategy]: High confidence — 3-level validation is well-defined with concrete test commands. Integration test covers full pipeline.
- [Scale Consideration]: Medium confidence — Sequential feed fetching works for typical 5-20 feeds (10-60s runtime). For 50+ feeds, parallel fetch may be needed, but sequential is correct starting point.
- [Email Formatting]: High confidence — MIME multipart with HTML + plain-text is standard pattern. Grouping by feed is straightforward.
- [State Management]: High confidence — Composite guid key prevents duplicates, max_guids prevents unbounded growth, commit-after-send prevents data loss.

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — all requirements are clear and executable. The system can be built as-is.

**Ready to build**: YES — confidence score 9/10, no ambiguity flags, all patterns proven, all failure modes handled.

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/rss-digest-monitor.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
