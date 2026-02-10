# n8n Node-to-WAT Mapping Reference

This document maps every major n8n node type to its WAT equivalent. Used by `factory/tools/convert_n8n.py` during n8n-to-WAT conversions.

## How to Read This Map

Each entry specifies:
- **n8n Node Type**: The node's type identifier in n8n JSON
- **WAT Equivalent**: What it becomes in a WAT system (trigger, tool, decision, or workflow step)
- **Implementation**: How to implement it in WAT

---

## Trigger Nodes → GitHub Actions Triggers

These n8n nodes start a workflow. In WAT, they become GitHub Actions trigger configurations.

| n8n Node | n8n Type ID | WAT Equivalent | GitHub Actions Trigger |
|----------|------------|----------------|----------------------|
| Manual Trigger | `n8n-nodes-base.manualTrigger` | `workflow_dispatch` | Manual trigger with optional inputs |
| Schedule Trigger | `n8n-nodes-base.scheduleTrigger` | `schedule` | Cron expression in GitHub Actions |
| Cron | `n8n-nodes-base.cron` | `schedule` | Cron expression in GitHub Actions |
| Webhook | `n8n-nodes-base.webhook` | `repository_dispatch` | API-triggered via `repository_dispatch` event |
| Email Trigger (IMAP) | `n8n-nodes-base.emailReadImap` | `schedule` + polling tool | Cron-triggered check for new emails |
| GitHub Trigger | `n8n-nodes-base.githubTrigger` | Native GitHub event | Use native GitHub Actions event triggers |
| Telegram Trigger | `n8n-nodes-base.telegramTrigger` | `repository_dispatch` | Webhook from Telegram → `repository_dispatch` |
| Slack Trigger | `n8n-nodes-base.slackTrigger` | `repository_dispatch` | Webhook from Slack → `repository_dispatch` |

### Conversion Notes — Triggers
- n8n webhooks become `repository_dispatch` triggers. The external system (n8n, Zapier, custom) sends a POST to `https://api.github.com/repos/OWNER/REPO/dispatches`
- n8n cron expressions translate directly to GitHub Actions cron syntax (both use standard cron format)
- n8n manual triggers become `workflow_dispatch` with input parameters matching the manual trigger's configured fields

---

## HTTP & API Nodes → Python Tools

| n8n Node | n8n Type ID | WAT Tool Pattern | Key Implementation |
|----------|------------|-----------------|-------------------|
| HTTP Request | `n8n-nodes-base.httpRequest` | `api_request.py` | `requests` library with retry logic |
| GraphQL | `n8n-nodes-base.graphql` | `graphql_request.py` | `requests` with GraphQL query body |
| Webhook Response | `n8n-nodes-base.respondToWebhook` | Workflow step | Return data via commit or webhook callback |

### Conversion Notes — HTTP
- Map n8n's HTTP method, URL, headers, body, and auth directly to `requests` call parameters
- n8n's retry and timeout settings map to `requests` timeout and `tenacity` retry decorators
- OAuth credentials in n8n → reference GitHub Secrets for tokens

---

## Code & Function Nodes → Python Tools

| n8n Node | n8n Type ID | WAT Tool Pattern | Key Implementation |
|----------|------------|-----------------|-------------------|
| Code | `n8n-nodes-base.code` | `custom_code.py` | Translate JS/Python to WAT Python tool |
| Function | `n8n-nodes-base.function` | `custom_code.py` | Translate JS function body to Python |
| Function Item | `n8n-nodes-base.functionItem` | `custom_code.py` | Per-item processing in Python |
| Execute Command | `n8n-nodes-base.executeCommand` | `shell_command.py` | `subprocess.run()` with the command |

### Conversion Notes — Code
- n8n Code nodes may contain JavaScript or Python. JavaScript must be translated to Python.
- n8n's `$input`, `$json`, `$node` variables map to function arguments and file I/O in WAT tools
- n8n's `$env` variables map to `os.environ` in Python

---

## Logic & Flow Control Nodes → Workflow Decision Points

| n8n Node | n8n Type ID | WAT Equivalent | Implementation |
|----------|------------|----------------|----------------|
| IF | `n8n-nodes-base.if` | Decision point in workflow.md | Bold conditional with Yes/No branches |
| Switch | `n8n-nodes-base.switch` | Multi-branch decision | Multiple conditions with named branches |
| Merge | `n8n-nodes-base.merge` | Merge step in workflow.md | Combine data from parallel branches |
| Split In Batches | `n8n-nodes-base.splitInBatches` | Loop step or Agent Teams | Iterate over items or parallelize with sub-agents |
| Wait | `n8n-nodes-base.wait` | Workflow pause note | Document the wait; implement as cron re-check or sleep |
| No Operation | `n8n-nodes-base.noOp` | (skip) | Remove from workflow — no action needed |
| Stop and Error | `n8n-nodes-base.stopAndError` | Failure mode | Map to error handling in workflow.md |

### Conversion Notes — Logic
- n8n IF conditions map to: `**If {condition}**: Yes → step X, No → step Y` in workflow.md
- n8n Switch maps to: `**Based on {value}**: Case A → ..., Case B → ..., Default → ...`
- n8n Merge (Append/Combine) maps to a Python tool that merges JSON arrays/objects
- n8n Split In Batches is a candidate for Agent Teams if items are independent

---

## Data Transformation Nodes → Python Tools

| n8n Node | n8n Type ID | WAT Tool Pattern | Key Implementation |
|----------|------------|-----------------|-------------------|
| Set | `n8n-nodes-base.set` | `data_transform.py` | Map/rename/add fields in data |
| Item Lists | `n8n-nodes-base.itemLists` | `data_transform.py` | Sort, limit, filter, deduplicate |
| Spreadsheet File | `n8n-nodes-base.spreadsheetFile` | `file_io.py` | `pandas` or `csv` module for read/write |
| XML | `n8n-nodes-base.xml` | `data_transform.py` | `xml.etree` or `xmltodict` |
| HTML Extract | `n8n-nodes-base.htmlExtract` | `web_scrape.py` | `beautifulsoup4` for HTML parsing |
| Markdown | `n8n-nodes-base.markdown` | `data_transform.py` | Markdown processing in Python |
| Crypto | `n8n-nodes-base.crypto` | `data_transform.py` | `hashlib` for hashing |
| Date & Time | `n8n-nodes-base.dateTime` | `data_transform.py` | `datetime` module |
| Compression | `n8n-nodes-base.compression` | `file_io.py` | `zipfile` or `gzip` modules |

---

## Communication Nodes → Python Tools (Notification Pattern)

| n8n Node | n8n Type ID | WAT Tool Pattern | Key Implementation |
|----------|------------|-----------------|-------------------|
| Slack | `n8n-nodes-base.slack` | `notify_slack.py` | Slack webhook or MCP |
| Telegram | `n8n-nodes-base.telegram` | `notify_telegram.py` | Telegram Bot API or MCP |
| Discord | `n8n-nodes-base.discord` | `notify_discord.py` | Discord webhook |
| Gmail / Email | `n8n-nodes-base.gmail` | `send_email.py` | SMTP or Gmail API |
| Send Email | `n8n-nodes-base.emailSend` | `send_email.py` | SMTP via `smtplib` |
| Twilio | `n8n-nodes-base.twilio` | `send_sms.py` | Twilio API |

---

## Storage & Database Nodes → Python Tools

| n8n Node | n8n Type ID | WAT Tool Pattern | Key Implementation |
|----------|------------|-----------------|-------------------|
| Postgres | `n8n-nodes-base.postgres` | `database.py` | `psycopg2` or Supabase client |
| MySQL | `n8n-nodes-base.mySql` | `database.py` | `mysql-connector-python` |
| MongoDB | `n8n-nodes-base.mongoDb` | `database.py` | `pymongo` |
| Redis | `n8n-nodes-base.redis` | `cache.py` | `redis` Python client |
| Google Sheets | `n8n-nodes-base.googleSheets` | `sheets.py` | Google Sheets API or MCP |
| Airtable | `n8n-nodes-base.airtable` | `airtable.py` | Airtable API or MCP |
| Notion | `n8n-nodes-base.notion` | `notion.py` | Notion API or MCP |
| S3 | `n8n-nodes-base.s3` | `storage.py` | `boto3` |
| Google Drive | `n8n-nodes-base.googleDrive` | `storage.py` | Google Drive API or MCP |
| FTP | `n8n-nodes-base.ftp` | `file_transfer.py` | `ftplib` |

---

## AI & LangChain Nodes → Python Tools

| n8n Node | n8n Type ID | WAT Tool Pattern | Key Implementation |
|----------|------------|-----------------|-------------------|
| OpenAI | `n8n-nodes-base.openAi` | `ai_process.py` | OpenAI API or MCP |
| AI Agent | `@n8n/n8n-nodes-langchain.agent` | Agent Teams or tool | Claude Code sub-agent or API call |
| AI Chain | `@n8n/n8n-nodes-langchain.chain` | Workflow steps | Multi-step LLM pipeline in workflow.md |
| Text Classifier | `@n8n/n8n-nodes-langchain.textClassifier` | `ai_process.py` | LLM prompt for classification |
| Summarizer | `@n8n/n8n-nodes-langchain.summarizer` | `ai_process.py` | LLM prompt for summarization |
| Vector Store | `@n8n/n8n-nodes-langchain.vectorStore` | `vector_store.py` | Embedding API + vector DB |

---

## Service-Specific Nodes → Python Tools

| n8n Node | WAT Tool Pattern | Notes |
|----------|-----------------|-------|
| GitHub | `github_api.py` | Use `gh` CLI or GitHub API directly |
| Jira | `api_request.py` | Jira REST API |
| Stripe | `api_request.py` | Stripe Python SDK |
| Trello | `api_request.py` | Trello REST API |
| Linear | `api_request.py` | Linear GraphQL API |
| HubSpot | `api_request.py` | HubSpot API |
| Salesforce | `api_request.py` | Salesforce REST API |
| Shopify | `api_request.py` | Shopify Admin API |
| WordPress | `api_request.py` | WordPress REST API |

### Conversion Notes — Services
- Most service nodes become HTTP API tools with service-specific endpoints
- Auth tokens stored in GitHub Secrets, injected as environment variables
- Check MCP registry — if an MCP exists for the service, prefer it over raw API calls

---

## Unmapped / Custom Nodes

If an n8n node type is not in this map:

1. Check if it's a community node — look for `n8n-nodes-community.` prefix
2. Map it to the closest WAT equivalent (usually a Python tool with HTTP calls)
3. Mark it with `TODO: manual review needed` in the converted workflow
4. Log the unmapped node type so it can be added to this map for future conversions
5. Add the mapping to this file after successful conversion
