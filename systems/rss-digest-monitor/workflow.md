# RSS Digest Monitor Workflow

**System Purpose:** Daily email digest system that monitors multiple RSS feeds, tracks new posts, and delivers formatted HTML summaries via SMTP.

---

## Inputs

```yaml
- config/feeds.json:
    description: "List of RSS/Atom feed URLs with display names and tags"
    format: JSON
    required: true
    example: |
      {
        "feeds": [
          {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "tags": ["tech"]},
          {"name": "GitHub Blog", "url": "https://github.blog/feed/", "tags": ["dev"]}
        ]
      }

- environment_variables:
    SMTP_HOST: "SMTP server hostname (e.g., smtp.gmail.com)"
    SMTP_PORT: "SMTP port (587 for TLS)"
    SMTP_USER: "SMTP authentication username"
    SMTP_PASS: "SMTP authentication password (use App Password for Gmail)"
    SMTP_FROM: "From address (e.g., RSS Digest <notify@example.com>)"
    SMTP_TO: "Comma-separated recipient email addresses"

- state/rss_state.json:
    description: "Tracks last run timestamp and seen post GUIDs (created on first run)"
    format: JSON
    required: false
    example: |
      {
        "last_run": "2026-02-11T08:00:00Z",
        "seen_guids": ["feed_url::post_guid", ...]
      }
```

## Outputs

```yaml
- html_email_digest:
    destination: "SMTP recipients (SMTP_TO)"
    format: "HTML email with plain-text fallback"
    contains: "Posts grouped by feed, including title (linked), summary, date"

- state/rss_state.json:
    destination: "Committed to repository"
    format: JSON
    contains: "Updated last_run timestamp and seen_guids list"

- logs/YYYY-MM-DD_run.json:
    destination: "Committed to repository"
    format: JSON
    contains: "Run summary: feeds checked, new posts found, email sent status"
```

---

## Workflow Steps

### Step 1: Load State

**Delegate to:** `state-manager-specialist`

**Action:** Read `state/rss_state.json` to get last_run timestamp and seen_guids list. Initialize empty state if file doesn't exist (first run).

**Tool:** `tools/load_state.py`

**Expected Output:** State object:
```json
{
  "last_run": "2026-02-11T08:00:00Z",  // or null on first run
  "seen_guids": ["feed_url::post_guid", ...]
}
```

**Failure Mode:** State file is corrupted or unparseable JSON.

**Fallback:** Log warning, initialize empty state `{"last_run": null, "seen_guids": []}`, proceed with full feed history. This ensures the system works even if state is corrupted -- better to duplicate posts once than crash.

---

### Step 2: Fetch RSS Feeds

**Delegate to:** `rss-fetcher-specialist`

**Action:** Iterate through config/feeds.json, fetch each feed URL via HTTP GET with feedparser, parse entries. Handle per-feed errors gracefully -- one feed failure must NOT kill the entire run.

**Tool:** `tools/fetch_rss_feeds.py`

**Expected Output:** Feed results list:
```json
{
  "feeds": [
    {
      "name": "Hacker News",
      "url": "https://news.ycombinator.com/rss",
      "entries": [
        {
          "title": "Post Title",
          "link": "https://example.com/post",
          "summary": "Post summary (truncated to 300 chars)",
          "published": "2026-02-11T08:00:00Z",
          "guid": "https://example.com/post"
        }
      ],
      "error": null  // or "HTTP 404" / "Parse error" if failed
    }
  ]
}
```

**Failure Mode:** Individual feed is unreachable (HTTP error, timeout, malformed XML).

**Fallback:** Log error for that feed, mark as `error: "HTTP 404"` or `error: "Parse error"`, continue with remaining feeds. Do NOT fail entire run. Log all errors to `logs/YYYY-MM-DD_run.json` for review.

---

### Step 3: Filter New Posts

**Delegate to:** `state-manager-specialist`

**Action:** Compare fetched entries against `state.seen_guids`. Filter entries where `(feed_url + "::" + guid)` is not in seen_guids AND `published >= state.last_run` (or include all if first run).

**Tool:** `tools/filter_new_posts.py`

**Expected Output:** New posts list:
```json
{
  "new_posts": [
    {
      "feed_name": "Hacker News",
      "title": "Post Title",
      "link": "https://example.com/post",
      "summary": "Post summary",
      "published": "2026-02-11T08:00:00Z",
      "guid": "https://example.com/post",
      "feed_url": "https://news.ycombinator.com/rss"
    }
  ],
  "new_guids": ["https://news.ycombinator.com/rss::https://example.com/post"]
}
```

**Failure Mode:** Published date is missing or unparseable.

**Fallback:** Use current timestamp as published date, log warning, include post. Better to duplicate than miss a post.

---

### Step 4: Generate HTML Digest

**Delegate to:** `digest-generator-specialist`

**Action:** Group new posts by feed_name. Generate HTML email body with sections per feed, styled post cards. Create plain-text fallback. Generate subject line with new post count.

**Tool:** `tools/generate_html_digest.py`

**Expected Output:** MIME multipart email object (or None if no new posts).

**Conditional:** If `new_posts` is empty, skip email generation and proceed directly to Step 6 (state update with no new GUIDs).

**Failure Mode:** No new posts (empty list).

**Fallback:** Return None -- skip email send, proceed to state update. Log "No new posts" to run summary.

---

### Step 5: Send Email via SMTP

**Action:** Connect to SMTP server (SMTP_HOST:SMTP_PORT), authenticate (SMTP_USER, SMTP_PASS), send digest to SMTP_TO recipients. Use TLS for security.

**Tool:** `tools/send_email_smtp.py`

**Conditional:** Only execute if Step 4 produced an email object (new posts exist).

**Expected Output:** Success status:
```json
{
  "sent": true,
  "message_id": "abc123@smtp.example.com",
  "error": null
}
```

**Failure Mode:** SMTP authentication failure, network error, recipient rejection.

**Fallback:** Retry once with 30-second delay. If still fails, log error and exit non-zero. **DO NOT update state if email fails** -- posts will retry next run. This prevents losing posts due to temporary email issues.

---

### Step 6: Update State

**Delegate to:** `state-manager-specialist`

**Action:** Update state object: set `last_run` to current timestamp, append `new_guids` to `seen_guids` (keep last 10,000 to prevent unbounded growth). Write to `state/rss_state.json`.

**Tool:** `tools/save_state.py`

**Conditional:** Only execute if Step 5 succeeded (or if no email was sent because no new posts).

**Expected Output:** Updated state file written to disk.

**Failure Mode:** File write permission error, disk full.

**Fallback:** Log error and exit non-zero. State is not committed. Next run will retry same posts (acceptable failure mode -- better than losing state).

---

### Step 7: Commit State to Repository

**Action:** Stage `state/rss_state.json` and `logs/YYYY-MM-DD_run.json`, commit with descriptive message including post count, push to origin.

**Tool:** `git add`, `git commit`, `git push` (via GitHub Actions or local Git CLI)

**Expected Output:** Git commit SHA.

**Failure Mode:** Git conflict (concurrent run), push rejection.

**Fallback:** Pull with rebase, retry commit. If fails after 2 attempts, log error but exit 0 (state was saved locally, will sync next run).

---

## Execution Modes

This system supports three execution paths:

### Mode 1: GitHub Actions (Primary)

Scheduled daily at 8 AM UTC via `.github/workflows/monitor.yml`. Runs autonomously with secrets from GitHub Secrets.

### Mode 2: Manual Dispatch

Trigger via GitHub Actions UI or API for testing or on-demand digests. Supports `force_send` input to send digest even if no new posts (for testing).

### Mode 3: Local CLI

Run directly: `SMTP_HOST=... SMTP_TO=... claude workflow.md`

Useful for development and testing with local `.env` file.

---

## Failure Handling Summary

| Failure Scenario | Behavior |
|------------------|----------|
| Single feed unreachable | Log error, continue with other feeds |
| State file corrupted | Initialize empty state, process all posts |
| No new posts | Silent run, update state only (no email) |
| SMTP authentication fails | Retry once, then fail (preserve state for retry) |
| Email send fails | Fail run, do NOT update state (posts retry next run) |
| State write fails | Fail run, log error (local state preserved) |
| Git push fails | Log error, exit 0 (state saved locally, will sync next run) |

---

## Success Criteria

- [ ] System fetches multiple RSS/Atom feeds without failing if one is down
- [ ] New posts correctly identified by comparing against state file
- [ ] Email digest sent via SMTP with HTML formatting, grouped by feed
- [ ] Each digest entry includes: feed name, title (linked), summary, date
- [ ] State file updated and committed after successful email send
- [ ] System runs autonomously via GitHub Actions daily at 8 AM UTC
- [ ] If no new posts, no email sent (silent run with state update)
- [ ] All three execution paths work: CLI, GitHub Actions, manual dispatch
