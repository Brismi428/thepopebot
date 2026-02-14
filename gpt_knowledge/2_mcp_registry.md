# MCP Registry

The factory's awareness of all available MCPs and integrations. This is the single source of truth for what tools are available when building WAT systems.

**Usage**: Before generating tools, always check this registry. Prefer MCPs over raw API calls when available — less code to maintain, fewer bugs. But always provide a fallback.

**Adding new MCPs**: Add a new entry following the format below. The factory will automatically discover it during the Research step.

---

## Web & Data Access

### Firecrawl
- **Description**: Web scraping and crawling service. Extracts clean content from websites, handles JavaScript rendering, and returns structured data.
- **Key Capabilities**: Scrape single pages, crawl entire sites, extract structured data, handle JS-heavy sites, return markdown or JSON
- **Common Use Cases**: Company research, content extraction, competitive analysis, price monitoring
- **Tool Pattern**: `firecrawl_scrape(url) → markdown/JSON content`
- **Secret**: `FIRECRAWL_API_KEY`
- **Fallback**: Direct HTTP with `requests` + `beautifulsoup4` (won't handle JS rendering)

### Brave Search
- **Description**: Web search API. Returns search results with snippets and metadata.
- **Key Capabilities**: Web search, news search, image search, summarized results
- **Common Use Cases**: Research gathering, fact-checking, finding URLs, news monitoring
- **Tool Pattern**: `brave_search(query) → list of search results with URLs and snippets`
- **Secret**: `BRAVE_SEARCH_API_KEY`
- **Fallback**: Google Custom Search API or SerpAPI

### Puppeteer
- **Description**: Browser automation MCP. Controls a headless Chrome instance for web interaction.
- **Key Capabilities**: Navigate pages, fill forms, click buttons, take screenshots, extract DOM content
- **Common Use Cases**: Scraping dynamic sites, form submission, visual testing, PDF generation
- **Tool Pattern**: `puppeteer_navigate(url) → page content; puppeteer_screenshot() → image`
- **Secret**: None (local browser)
- **Fallback**: Playwright via Python `playwright` package

### Fetch
- **Description**: Simple HTTP fetch MCP. Makes HTTP requests and returns responses.
- **Key Capabilities**: GET, POST, PUT, DELETE requests with headers and body
- **Common Use Cases**: API calls, webhooks, simple page fetches
- **Tool Pattern**: `fetch(url, method, headers, body) → response`
- **Secret**: None
- **Fallback**: Python `requests` library

---

## Code & DevOps

### GitHub
- **Description**: GitHub API integration. Full access to repos, issues, PRs, Actions, and more.
- **Key Capabilities**: Create/read/update repos, issues, PRs, manage Actions, read file contents, manage releases
- **Common Use Cases**: Automated PR creation, issue management, repo setup, CI/CD integration
- **Tool Pattern**: `github_create_issue(repo, title, body); github_create_pr(repo, ...)`
- **Secret**: `GITHUB_TOKEN` or `GITHUB_PAT`
- **Fallback**: `gh` CLI or direct GitHub REST API via `requests`

### Docker
- **Description**: Docker container management MCP.
- **Key Capabilities**: Build, run, stop, and manage containers
- **Common Use Cases**: Isolated tool execution, testing environments
- **Tool Pattern**: `docker_run(image, command) → output`
- **Secret**: None (local Docker daemon)
- **Fallback**: `subprocess.run(["docker", ...])`

---

## Communication

### Slack
- **Description**: Slack messaging MCP. Send messages, read channels, manage threads.
- **Key Capabilities**: Send messages, post to channels, read channel history, manage threads, upload files
- **Common Use Cases**: Notifications, alerts, status updates, team communication
- **Tool Pattern**: `slack_send(channel, message); slack_read(channel) → messages`
- **Secret**: `SLACK_BOT_TOKEN` or `SLACK_WEBHOOK_URL`
- **Fallback**: Slack Incoming Webhook via HTTP POST

### Telegram
- **Description**: Telegram Bot API MCP. Send and receive messages via Telegram bots.
- **Key Capabilities**: Send messages, photos, documents; read updates; inline keyboards
- **Common Use Cases**: Alerts, notifications, command-driven bots, status reports
- **Tool Pattern**: `telegram_send(chat_id, message); telegram_get_updates() → messages`
- **Secret**: `TELEGRAM_BOT_TOKEN`
- **Fallback**: Telegram Bot API via HTTP

### Gmail
- **Description**: Gmail API MCP. Send and read emails.
- **Key Capabilities**: Send emails, read inbox, search emails, manage labels
- **Common Use Cases**: Email notifications, inbox monitoring, automated responses
- **Tool Pattern**: `gmail_send(to, subject, body); gmail_search(query) → emails`
- **Secret**: `GMAIL_CREDENTIALS`
- **Fallback**: SMTP via `smtplib`

### Discord
- **Description**: Discord messaging via webhooks or bot.
- **Key Capabilities**: Send messages, embeds, files to channels
- **Common Use Cases**: Team notifications, alerts, community updates
- **Tool Pattern**: `discord_send(webhook_url, message)`
- **Secret**: `DISCORD_WEBHOOK_URL`
- **Fallback**: Discord webhook via HTTP POST

---

## Storage & Databases

### Supabase
- **Description**: Supabase (Postgres + Auth + Storage) MCP. Full database and storage access.
- **Key Capabilities**: CRUD operations, real-time subscriptions, file storage, auth management
- **Common Use Cases**: Persistent data storage, user management, file hosting
- **Tool Pattern**: `supabase_insert(table, data); supabase_query(table, filters) → rows`
- **Secret**: `SUPABASE_URL`, `SUPABASE_KEY`
- **Fallback**: Direct PostgreSQL via `psycopg2` or Supabase REST API

### Google Drive
- **Description**: Google Drive file management MCP.
- **Key Capabilities**: Upload, download, list, search, share files and folders
- **Common Use Cases**: File storage, document sharing, backup
- **Tool Pattern**: `gdrive_upload(file, folder_id); gdrive_list(folder_id) → files`
- **Secret**: `GOOGLE_CREDENTIALS`
- **Fallback**: Google Drive API via `google-api-python-client`

### Airtable
- **Description**: Airtable database MCP. CRUD operations on Airtable bases and tables.
- **Key Capabilities**: Create, read, update, delete records; list tables; manage views
- **Common Use Cases**: Lightweight database, CRM data, project tracking, content calendars
- **Tool Pattern**: `airtable_create(base, table, record); airtable_list(base, table) → records`
- **Secret**: `AIRTABLE_API_KEY`
- **Fallback**: Airtable REST API via `requests`

### Notion
- **Description**: Notion API MCP. Manage pages, databases, and blocks.
- **Key Capabilities**: Create/update pages, query databases, manage blocks
- **Common Use Cases**: Knowledge base, documentation, project management, content publishing
- **Tool Pattern**: `notion_create_page(parent, title, content); notion_query_db(db_id, filter) → pages`
- **Secret**: `NOTION_API_KEY`
- **Fallback**: Notion API via `requests`

### SQLite
- **Description**: Local SQLite database MCP. Embedded SQL database.
- **Key Capabilities**: Create tables, CRUD operations, run SQL queries
- **Common Use Cases**: Local data caching, lightweight storage, offline-first data
- **Tool Pattern**: `sqlite_query(db_path, sql) → rows`
- **Secret**: None (local file)
- **Fallback**: Python `sqlite3` standard library module

---

## AI & Processing

### OpenAI
- **Description**: OpenAI API MCP. Access GPT models, DALL-E, Whisper, and embeddings.
- **Key Capabilities**: Chat completions, image generation, speech-to-text, embeddings, structured output
- **Common Use Cases**: Text generation, summarization, classification, image creation, transcription
- **Tool Pattern**: `openai_chat(messages) → response; openai_embed(text) → vector`
- **Secret**: `OPENAI_API_KEY`
- **Fallback**: OpenAI Python SDK directly

### Anthropic
- **Description**: Anthropic API for Claude models.
- **Key Capabilities**: Chat completions, tool use, structured output, long context
- **Common Use Cases**: Complex reasoning, analysis, code generation, document processing
- **Tool Pattern**: `anthropic_message(messages) → response`
- **Secret**: `ANTHROPIC_API_KEY`
- **Fallback**: Anthropic Python SDK directly

### ElevenLabs
- **Description**: AI voice synthesis and cloning.
- **Key Capabilities**: Text-to-speech, voice cloning, audio generation
- **Common Use Cases**: Audio content creation, podcasts, voice notifications
- **Tool Pattern**: `elevenlabs_tts(text, voice_id) → audio_file`
- **Secret**: `ELEVENLABS_API_KEY`
- **Fallback**: ElevenLabs REST API

### Replicate
- **Description**: Run ML models via API. Access thousands of open-source models.
- **Key Capabilities**: Image generation, video generation, audio processing, custom models
- **Common Use Cases**: Image manipulation, model inference, content generation
- **Tool Pattern**: `replicate_run(model, input) → output`
- **Secret**: `REPLICATE_API_TOKEN`
- **Fallback**: Replicate Python SDK or REST API

---

## Business & Productivity

### Stripe
- **Description**: Stripe payment processing API.
- **Key Capabilities**: Create charges, manage subscriptions, list transactions, handle webhooks
- **Common Use Cases**: Payment tracking, subscription management, revenue reporting
- **Tool Pattern**: `stripe_list_charges(filters) → charges`
- **Secret**: `STRIPE_API_KEY`
- **Fallback**: Stripe Python SDK

### Google Sheets
- **Description**: Google Sheets API MCP.
- **Key Capabilities**: Read/write cells, create sheets, format, formulas
- **Common Use Cases**: Data input/output, reporting, dashboards, data collection
- **Tool Pattern**: `sheets_read(spreadsheet_id, range) → data; sheets_write(spreadsheet_id, range, data)`
- **Secret**: `GOOGLE_CREDENTIALS`
- **Fallback**: `gspread` Python library

### Google Calendar
- **Description**: Google Calendar API MCP.
- **Key Capabilities**: Create/read/update events, list calendars, manage attendees
- **Common Use Cases**: Scheduling, event tracking, availability checks
- **Tool Pattern**: `calendar_create_event(calendar_id, event); calendar_list(calendar_id) → events`
- **Secret**: `GOOGLE_CREDENTIALS`
- **Fallback**: Google Calendar API via `google-api-python-client`

### Linear
- **Description**: Linear project management API.
- **Key Capabilities**: Create/update issues, manage projects, track cycles
- **Common Use Cases**: Task creation, sprint management, automated issue tracking
- **Tool Pattern**: `linear_create_issue(team, title, description)`
- **Secret**: `LINEAR_API_KEY`
- **Fallback**: Linear GraphQL API via `requests`

---

## Local & System

### Filesystem
- **Description**: Local filesystem access MCP.
- **Key Capabilities**: Read, write, list, delete files and directories
- **Common Use Cases**: File processing, data storage, configuration management
- **Tool Pattern**: `fs_read(path) → content; fs_write(path, content)`
- **Secret**: None
- **Fallback**: Python `pathlib` / built-in `open()`

### Shell / Desktop Commander
- **Description**: Execute shell commands on the local system.
- **Key Capabilities**: Run commands, manage processes, system information
- **Common Use Cases**: Tool execution, system automation, build processes
- **Tool Pattern**: `shell_exec(command) → output`
- **Secret**: None
- **Fallback**: Python `subprocess`

---

## Social & Content

### Twitter/X
- **Description**: Twitter/X API integration.
- **Key Capabilities**: Post tweets, read timelines, search tweets, manage lists
- **Common Use Cases**: Social media posting, monitoring mentions, content distribution
- **Tool Pattern**: `twitter_post(text); twitter_search(query) → tweets`
- **Secret**: `TWITTER_BEARER_TOKEN`
- **Fallback**: Twitter API v2 via `requests`

### LinkedIn
- **Description**: LinkedIn API integration.
- **Key Capabilities**: Post updates, read profile, company pages
- **Common Use Cases**: Professional content posting, company updates
- **Tool Pattern**: `linkedin_post(text, image_url)`
- **Secret**: `LINKEDIN_ACCESS_TOKEN`
- **Fallback**: LinkedIn API via `requests`

### YouTube
- **Description**: YouTube Data API.
- **Key Capabilities**: Search videos, get video details, manage playlists, read comments
- **Common Use Cases**: Video research, content analysis, playlist management
- **Tool Pattern**: `youtube_search(query) → videos; youtube_video_details(video_id) → metadata`
- **Secret**: `YOUTUBE_API_KEY`
- **Fallback**: YouTube Data API via `google-api-python-client`

---

## Custom / Any API

Any REST API can be integrated into a WAT system without an MCP:

1. Write a Python tool using `requests` with proper auth headers
2. Store API credentials in GitHub Secrets
3. Reference via `os.environ["SECRET_NAME"]` in the tool
4. Add retry logic with `tenacity` or manual retry loops
5. Document the API in the system's CLAUDE.md

The factory is never limited to the MCPs listed here. This registry helps with tool selection, but any API accessible via HTTP can be wrapped as a Python tool.

---

## Media Processing

### NCA Toolkit (Self-Hosted)
- **Description**: Self-hosted media processing API running at `https://media.wat-factory.cloud`. Replaces services like CloudConvert, Placid, and PDF.co. Handles audio, video, image conversion, transcription, captioning, and more.
- **Base URL**: `https://media.wat-factory.cloud`
- **Auth**: `x-api-key` header with `NCA_API_KEY` environment variable
- **Key Capabilities**:
  - Transcribe audio/video to text (Whisper) — `POST /v1/media/transcribe`
  - Convert media between formats — `POST /v1/media/convert`
  - Convert to MP3 — `POST /v1/media/convert/mp3`
  - Add captions to video — `POST /v1/video/caption`
  - Concatenate videos — `POST /v1/video/concatenate`
  - Concatenate audio — `POST /v1/audio/concatenate`
  - Trim video — `POST /v1/video/trim`
  - Cut segments from video — `POST /v1/video/cut`
  - Split video — `POST /v1/video/split`
  - Extract thumbnail — `POST /v1/video/thumbnail`
  - Screenshot webpage — `POST /v1/image/screenshot/webpage`
  - Convert image to video — `POST /v1/image/convert/video`
  - Download media from URL (yt-dlp) — `POST /v1/BETA/media/download`
  - Detect silence — `POST /v1/media/silence`
  - Extract metadata — `POST /v1/media/metadata`
  - Generate ASS subtitles — `POST /v1/media/generate/ass`
  - Upload to S3/R2 — `POST /v1/s3/upload`
  - Run FFmpeg commands — `POST /v1/ffmpeg/compose`
  - Execute Python code — `POST /v1/code/execute/python`
  - Test connectivity — `GET /v1/toolkit/test`
  - Check job status — `GET /v1/toolkit/job/status?job_id=<id>`
- **Common Use Cases**: Video transcription, audio/video format conversion, auto-captioning videos for social media, webpage screenshots, media downloading, thumbnail extraction
- **Tool Pattern**:
  ```python
  import os, requests
  from urllib.parse import quote

  NCA_URL = "https://media.wat-factory.cloud"
  R2_PUBLIC = "https://pub-b692c36a8374480593a007a38bc7116c.r2.dev"
  headers = {"x-api-key": os.environ["NCA_API_KEY"], "Content-Type": "application/json"}

  # === YouTube Transcription (two-step process) ===
  # Step 1: Download the video (uses yt-dlp, stores on R2)
  dl = requests.post(f"{NCA_URL}/v1/BETA/media/download", headers=headers, json={
      "media_url": "https://youtube.com/watch?v=VIDEO_ID"
  }).json()

  # Step 2: Get the filename from the response and build the PUBLIC R2 URL
  # IMPORTANT: The storage URL returned uses the private R2 endpoint which is not accessible.
  # You MUST use the public R2 dev URL instead.
  # IMPORTANT: Filenames often contain spaces, parentheses, and unicode characters.
  # You MUST URL-encode the filename.
  filename = dl["response"]["media"]["media_url"].split("/nca-media/")[-1]
  public_url = f"{R2_PUBLIC}/{filename}"  # filename is already URL-encoded from the response

  # Step 3: Transcribe using the public URL
  transcript = requests.post(f"{NCA_URL}/v1/media/transcribe", headers=headers, json={
      "media_url": public_url
  }).json()
  text = transcript["response"]["text"]

  # === Direct media transcription (non-YouTube, publicly accessible URL) ===
  resp = requests.post(f"{NCA_URL}/v1/media/transcribe", headers=headers, json={
      "media_url": "https://example.com/audio.mp3"
  })

  # === Screenshot a webpage ===
  resp = requests.post(f"{NCA_URL}/v1/image/screenshot/webpage", headers=headers, json={
      "url": "https://example.com",
      "width": 1920,
      "height": 1080
  })
  ```
- **Secret**: `NCA_API_KEY`
- **Fallback**: Direct FFmpeg via subprocess (limited — no transcription, no cloud upload)
- **CRITICAL NOTES**:
  - The `/v1/media/transcribe` endpoint does NOT support YouTube URLs directly. You MUST first download via `/v1/BETA/media/download`, then transcribe the downloaded file.
  - The `media_url` returned by the download endpoint uses the private R2 storage URL (`fa8408d96e71300f9e63b83ad7177384.r2.cloudflarestorage.com`). This URL is NOT publicly accessible. Replace the domain with the public R2 URL: `pub-b692c36a8374480593a007a38bc7116c.r2.dev`
  - All field names use `media_url` (not `url`), except for screenshot which uses `url`.
  - Transcription runs Whisper on CPU. A 20-minute video takes ~3-4 minutes. Set request timeouts accordingly (at least 600 seconds).
  - Supports async processing with `webhook_url` parameter for long-running jobs.
