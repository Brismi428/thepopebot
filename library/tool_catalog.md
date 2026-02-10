# WAT Systems Factory -- Reusable Tool Pattern Catalog

> **Version:** 0.1.0-seed
> **Maintainer:** WAT Systems Factory / Agent HQ
> **Purpose:** Canonical reference of composable tool patterns that factory-generated workflows can assemble into pipelines. Each pattern is self-contained, testable, and convertible to an MCP tool or n8n node.

---

## Table of Contents

1. [Web Scraping & Search](#web-scraping--search)
2. [File I/O](#file-io)
3. [API Calls](#api-calls)
4. [Data Processing](#data-processing)
5. [AI Processing](#ai-processing)
6. [Notifications](#notifications)
7. [Git Operations](#git-operations)
8. [GitHub API](#github-api)
9. [Database Operations](#database-operations)
10. [Media Processing](#media-processing)
11. [n8n Conversion](#n8n-conversion)
12. [Agent Teams Coordination](#agent-teams-coordination)
13. [GitHub Agent HQ Interaction](#github-agent-hq-interaction)

---

## Web Scraping & Search

### `firecrawl_scrape`

**Description:** Scrapes a single URL or crawls an entire domain via the Firecrawl API, returning clean Markdown-formatted content suitable for downstream LLM consumption.

| Field | Detail |
|---|---|
| **Input** | `url: str`, `mode: Literal["scrape", "crawl"]`, `max_pages: int = 50`, `selectors: list[str] = []` |
| **Output** | `dict` with keys `markdown: str`, `metadata: dict`, `links: list[str]` |
| **Key Dependencies** | `firecrawl-py`, `httpx` |
| **MCP Alternative** | `@anthropic/firecrawl-mcp` server -- exposes `firecrawl_scrape` and `firecrawl_crawl` tools directly |

```python
import os
from firecrawl import FirecrawlApp

def main(url: str, mode: str = "scrape", max_pages: int = 50,
         selectors: list[str] | None = None) -> dict:
    """Scrape or crawl a URL via Firecrawl and return Markdown content."""
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

    if mode == "crawl":
        result = app.crawl_url(url, params={
            "limit": max_pages,
            "scrapeOptions": {"formats": ["markdown"]},
        })
        pages = [{"markdown": p.get("markdown", ""), "url": p.get("url")}
                 for p in result.get("data", [])]
        return {"pages": pages, "count": len(pages)}

    # Default: single-page scrape
    result = app.scrape_url(url, params={"formats": ["markdown"]})
    return {
        "markdown": result.get("markdown", ""),
        "metadata": result.get("metadata", {}),
        "links": result.get("links", []),
    }
```

---

### `brave_search`

**Description:** Runs a web search query through the Brave Search API and returns structured result objects with titles, URLs, and snippets.

| Field | Detail |
|---|---|
| **Input** | `query: str`, `count: int = 10`, `freshness: str = ""` |
| **Output** | `list[dict]` each with `title`, `url`, `description`, `age` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | `@anthropic/brave-search-mcp` server -- exposes `brave_web_search` and `brave_local_search` |

```python
import os, httpx

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

def main(query: str, count: int = 10, freshness: str = "") -> list[dict]:
    """Execute a Brave web search and return structured results."""
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": os.environ["BRAVE_API_KEY"],
    }
    params = {"q": query, "count": min(count, 20)}
    if freshness:
        params["freshness"] = freshness  # e.g. "pd" (past day), "pw", "pm"

    resp = httpx.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
    resp.raise_for_status()

    results = []
    for item in resp.json().get("web", {}).get("results", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "description": item.get("description"),
            "age": item.get("age", ""),
        })
    return results
```

---

### `puppeteer_screenshot`

**Description:** Launches a headless browser via Puppeteer (through its MCP server or a local Node bridge) to capture a screenshot or extract JavaScript-rendered DOM content from a page.

| Field | Detail |
|---|---|
| **Input** | `url: str`, `action: Literal["screenshot", "extract"]`, `selector: str = "body"`, `viewport: dict = {"width": 1280, "height": 720}` |
| **Output** | `dict` with `base64_image: str` (for screenshot) or `html: str` (for extract) |
| **Key Dependencies** | `playwright` (Python) or Node `puppeteer` via subprocess |
| **MCP Alternative** | `@anthropic/puppeteer-mcp` server -- exposes `puppeteer_navigate`, `puppeteer_screenshot`, `puppeteer_click`, `puppeteer_fill` |

```python
from playwright.async_api import async_playwright
import asyncio, base64

async def _run(url: str, action: str, selector: str, viewport: dict) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport_size=viewport)
        await page.goto(url, wait_until="networkidle")

        if action == "screenshot":
            buf = await page.screenshot(full_page=True)
            await browser.close()
            return {"base64_image": base64.b64encode(buf).decode()}

        content = await page.inner_html(selector)
        await browser.close()
        return {"html": content}

def main(url: str, action: str = "screenshot", selector: str = "body",
         viewport: dict | None = None) -> dict:
    """Capture a screenshot or extract rendered HTML from a URL."""
    vp = viewport or {"width": 1280, "height": 720}
    return asyncio.run(_run(url, action, selector, vp))
```

---

## File I/O

### `csv_read_write`

**Description:** Reads a CSV file into a list of dictionaries or writes a list of dictionaries out to CSV, handling encoding detection and BOM stripping automatically.

| Field | Detail |
|---|---|
| **Input** | `path: str`, `mode: Literal["read", "write"]`, `data: list[dict] = []`, `encoding: str = "utf-8-sig"` |
| **Output** | `list[dict]` on read; `dict` with `rows_written: int, path: str` on write |
| **Key Dependencies** | `csv` (stdlib), `chardet` (optional encoding detection) |
| **MCP Alternative** | `@anthropic/filesystem-mcp` for raw read/write; CSV parsing done in-tool |

```python
import csv, io, pathlib

def main(path: str, mode: str = "read", data: list[dict] | None = None,
         encoding: str = "utf-8-sig") -> dict | list[dict]:
    """Read or write CSV files with automatic encoding handling."""
    p = pathlib.Path(path)

    if mode == "read":
        text = p.read_text(encoding=encoding)
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]

    # Write mode
    if not data:
        raise ValueError("data is required for write mode")
    fieldnames = list(data[0].keys())
    with p.open("w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return {"rows_written": len(data), "path": str(p.resolve())}
```

---

### `json_read_write`

**Description:** Reads a JSON or JSONL file into Python objects or writes Python objects out to JSON/JSONL, with optional pretty-printing and schema validation.

| Field | Detail |
|---|---|
| **Input** | `path: str`, `mode: Literal["read", "write"]`, `data: Any = None`, `jsonl: bool = False`, `indent: int = 2` |
| **Output** | Parsed object(s) on read; `dict` with `path: str, size_bytes: int` on write |
| **Key Dependencies** | `json` (stdlib), `jsonschema` (optional validation) |
| **MCP Alternative** | `@anthropic/filesystem-mcp` for raw I/O |

```python
import json, pathlib

def main(path: str, mode: str = "read", data=None,
         jsonl: bool = False, indent: int = 2):
    """Read or write JSON / JSONL files."""
    p = pathlib.Path(path)

    if mode == "read":
        text = p.read_text(encoding="utf-8")
        if jsonl:
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        return json.loads(text)

    # Write mode
    if jsonl:
        lines = [json.dumps(item, ensure_ascii=False) for item in data]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        p.write_text(json.dumps(data, indent=indent, ensure_ascii=False),
                      encoding="utf-8")
    return {"path": str(p.resolve()), "size_bytes": p.stat().st_size}
```

---

### `apollo_enrich`

**Description:** Enriches a company name/domain with company data and decision-maker contacts via the Apollo.io API. Returns structured company info, tech stack, and key contacts.

| Field | Detail |
|---|---|
| **Input** | `company_name: str`, `domain: str = None` |
| **Output** | `dict` with company data, tech stack, decision makers |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | None; direct HTTP API |

---

### `hunter_email_search`

**Description:** Searches for email addresses at a given domain via the Hunter.io API. Returns verified contacts with confidence scores.

| Field | Detail |
|---|---|
| **Input** | `domain: str`, `limit: int = 5` |
| **Output** | `dict` with emails, patterns, organization info |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | None; direct HTTP API |

---

### `multi_dimension_scorer`

**Description:** Scores a data record across N independent dimensions with configurable point values. Used for lead scoring, content quality assessment, or any multi-criteria evaluation.

| Field | Detail |
|---|---|
| **Input** | `record: dict`, `dimensions: list[dict]` (each with name, max_points, scoring_function) |
| **Output** | `dict` with dimension breakdown and total score |
| **Key Dependencies** | None (stdlib only) |
| **MCP Alternative** | None |

---

### `email_sequence_generator`

**Description:** Generates a multi-email sequence (outreach or nurture) using Claude API. Takes company/audience context and a sequence template, returns structured JSON with subject lines, bodies, and send timing.

| Field | Detail |
|---|---|
| **Input** | `context: dict`, `sequence_template: str`, `email_count: int` |
| **Output** | `dict` with sequence of emails (subject, body, send_day) |
| **Key Dependencies** | `anthropic` |
| **MCP Alternative** | Anthropic MCP |

---

### `pdf_extract`

**Description:** Extracts text content, metadata, and optionally tables from a PDF file, returning structured output ready for LLM ingestion or data-pipeline processing.

| Field | Detail |
|---|---|
| **Input** | `path: str`, `pages: str = "all"`, `extract_tables: bool = False` |
| **Output** | `dict` with `text: str`, `pages: list[dict]`, `metadata: dict`, `tables: list` |
| **Key Dependencies** | `pymupdf` (fitz), `pdfplumber` (for tables) |
| **MCP Alternative** | None standard; wrap as custom MCP tool |

```python
import fitz  # pymupdf

def main(path: str, pages: str = "all", extract_tables: bool = False) -> dict:
    """Extract text and metadata from a PDF file."""
    doc = fitz.open(path)
    metadata = dict(doc.metadata)

    page_range = range(len(doc))
    if pages != "all":
        # Parse ranges like "1-5" or "3,7,10-12"
        page_range = _parse_page_range(pages, len(doc))

    extracted_pages = []
    for i in page_range:
        page = doc[i]
        extracted_pages.append({
            "page_number": i + 1,
            "text": page.get_text("text"),
        })

    result = {
        "text": "\n\n".join(p["text"] for p in extracted_pages),
        "pages": extracted_pages,
        "metadata": metadata,
    }

    if extract_tables:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            result["tables"] = []
            for i in page_range:
                for table in pdf.pages[i].extract_tables():
                    result["tables"].append({"page": i + 1, "rows": table})

    return result

def _parse_page_range(spec: str, total: int) -> list[int]:
    indices = []
    for part in spec.split(","):
        if "-" in part:
            start, end = part.split("-", 1)
            indices.extend(range(int(start) - 1, min(int(end), total)))
        else:
            indices.append(int(part) - 1)
    return [i for i in indices if 0 <= i < total]
```

---

## API Calls

### `rest_client`

**Description:** A generic REST API client with configurable retry logic, exponential backoff, header injection, and response normalization -- the universal building block for any HTTP-based integration.

| Field | Detail |
|---|---|
| **Input** | `url: str`, `method: str = "GET"`, `headers: dict = {}`, `body: Any = None`, `retries: int = 3`, `backoff: float = 1.0`, `timeout: int = 30` |
| **Output** | `dict` with `status: int`, `headers: dict`, `body: Any`, `elapsed_ms: float` |
| **Key Dependencies** | `httpx`, `tenacity` |
| **MCP Alternative** | `@anthropic/fetch-mcp` for simple GET/POST |

```python
import httpx, time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

def _is_retryable(exc):
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout))

def main(url: str, method: str = "GET", headers: dict | None = None,
         body=None, retries: int = 3, backoff: float = 1.0,
         timeout: int = 30) -> dict:
    """Make an HTTP request with retry logic and exponential backoff."""

    @retry(
        stop=stop_after_attempt(retries),
        wait=wait_exponential(multiplier=backoff, min=1, max=30),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    def _do_request():
        t0 = time.monotonic()
        resp = httpx.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            json=body if isinstance(body, (dict, list)) else None,
            content=body if isinstance(body, (str, bytes)) else None,
            timeout=timeout,
        )
        elapsed = (time.monotonic() - t0) * 1000
        resp.raise_for_status()
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text
        return {
            "status": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp_body,
            "elapsed_ms": round(elapsed, 2),
        }

    return _do_request()
```

---

### `graphql_client`

**Description:** Sends GraphQL queries and mutations to any endpoint, with variable substitution, error extraction, and the same retry semantics as `rest_client`.

| Field | Detail |
|---|---|
| **Input** | `endpoint: str`, `query: str`, `variables: dict = {}`, `headers: dict = {}`, `retries: int = 3` |
| **Output** | `dict` with `data: Any`, `errors: list | None`, `status: int` |
| **Key Dependencies** | `httpx`, `tenacity` |
| **MCP Alternative** | None standard; wrap as custom MCP tool |

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

def main(endpoint: str, query: str, variables: dict | None = None,
         headers: dict | None = None, retries: int = 3) -> dict:
    """Execute a GraphQL query or mutation with retry logic."""

    @retry(stop=stop_after_attempt(retries),
           wait=wait_exponential(multiplier=1, min=1, max=15))
    def _execute():
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = httpx.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json", **(headers or {})},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        return {
            "data": result.get("data"),
            "errors": result.get("errors"),
            "status": resp.status_code,
        }

    return _execute()
```

---

### `oauth_token_refresh`

**Description:** Manages OAuth 2.0 token lifecycle -- obtains tokens via client_credentials or authorization_code grants, caches them, and transparently refreshes before expiry.

| Field | Detail |
|---|---|
| **Input** | `token_url: str`, `client_id: str`, `client_secret: str`, `grant_type: str = "client_credentials"`, `refresh_token: str = ""`, `scopes: list[str] = []` |
| **Output** | `dict` with `access_token: str`, `expires_in: int`, `token_type: str` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | None; typically embedded within other tools |

```python
import httpx, time

_token_cache: dict = {}

def main(token_url: str, client_id: str, client_secret: str,
         grant_type: str = "client_credentials",
         refresh_token: str = "", scopes: list[str] | None = None) -> dict:
    """Obtain or refresh an OAuth 2.0 access token."""
    cache_key = f"{token_url}:{client_id}"

    # Return cached token if still valid
    cached = _token_cache.get(cache_key)
    if cached and cached["expires_at"] > time.time() + 60:
        return {
            "access_token": cached["access_token"],
            "expires_in": int(cached["expires_at"] - time.time()),
            "token_type": cached["token_type"],
        }

    data = {"grant_type": grant_type, "client_id": client_id,
            "client_secret": client_secret}
    if refresh_token:
        data["refresh_token"] = refresh_token
    if scopes:
        data["scope"] = " ".join(scopes)

    resp = httpx.post(token_url, data=data, timeout=15)
    resp.raise_for_status()
    token_data = resp.json()

    _token_cache[cache_key] = {
        "access_token": token_data["access_token"],
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_at": time.time() + token_data.get("expires_in", 3600),
    }
    return {
        "access_token": token_data["access_token"],
        "expires_in": token_data.get("expires_in", 3600),
        "token_type": token_data.get("token_type", "Bearer"),
    }
```

---

## Data Processing

### `filter_sort`

**Description:** Applies filter predicates and multi-key sorting to a list of dictionaries, supporting comparison operators, regex matching, and null handling.

| Field | Detail |
|---|---|
| **Input** | `data: list[dict]`, `filters: list[dict]` (each with `field`, `op`, `value`), `sort_by: list[dict]` (each with `field`, `order`) |
| **Output** | `list[dict]` -- filtered and sorted records |
| **Key Dependencies** | `re` (stdlib) |
| **MCP Alternative** | None; pure logic tool |

```python
import re, operator

OPS = {
    "eq": operator.eq, "ne": operator.ne,
    "gt": operator.gt, "ge": operator.ge,
    "lt": operator.lt, "le": operator.le,
    "contains": lambda a, b: b in str(a),
    "regex": lambda a, b: bool(re.search(b, str(a))),
    "in": lambda a, b: a in b,
}

def main(data: list[dict], filters: list[dict] | None = None,
         sort_by: list[dict] | None = None) -> list[dict]:
    """Filter and sort a list of dictionaries."""
    result = data

    # Apply filters
    for f in (filters or []):
        op_fn = OPS.get(f["op"], operator.eq)
        result = [row for row in result if op_fn(row.get(f["field"]), f["value"])]

    # Apply sorting
    if sort_by:
        for s in reversed(sort_by):
            reverse = s.get("order", "asc") == "desc"
            result.sort(key=lambda row: (row.get(s["field"]) is None,
                                          row.get(s["field"], "")),
                        reverse=reverse)

    return result
```

---

### `dedup`

**Description:** Removes duplicate records from a dataset based on one or more key fields, with configurable strategies for which duplicate to keep (first, last, or merge).

| Field | Detail |
|---|---|
| **Input** | `data: list[dict]`, `keys: list[str]`, `strategy: Literal["first", "last", "merge"] = "first"` |
| **Output** | `dict` with `unique: list[dict]`, `duplicates_removed: int` |
| **Key Dependencies** | None (stdlib only) |
| **MCP Alternative** | None; pure logic tool |

```python
def main(data: list[dict], keys: list[str],
         strategy: str = "first") -> dict:
    """Deduplicate records by key fields."""
    seen: dict[tuple, dict] = {}
    order: list[tuple] = []

    for row in data:
        key = tuple(row.get(k) for k in keys)
        if key not in seen:
            seen[key] = row
            order.append(key)
        elif strategy == "last":
            seen[key] = row
        elif strategy == "merge":
            # Merge: later values fill in blanks only
            for k, v in row.items():
                if seen[key].get(k) in (None, ""):
                    seen[key][k] = v

    unique = [seen[k] for k in order]
    return {
        "unique": unique,
        "duplicates_removed": len(data) - len(unique),
    }
```

---

### `transform_map`

**Description:** Applies field-level transformations to every record in a dataset -- renaming columns, computing derived fields, type-casting, and applying template expressions.

| Field | Detail |
|---|---|
| **Input** | `data: list[dict]`, `mappings: list[dict]` (each with `source`, `target`, `transform`), `drop_unmapped: bool = False` |
| **Output** | `list[dict]` -- transformed records |
| **Key Dependencies** | None (stdlib only) |
| **MCP Alternative** | None; pure logic tool |

```python
from datetime import datetime

TRANSFORMS = {
    "upper": lambda v: str(v).upper(),
    "lower": lambda v: str(v).lower(),
    "strip": lambda v: str(v).strip(),
    "int": lambda v: int(v) if v not in (None, "") else None,
    "float": lambda v: float(v) if v not in (None, "") else None,
    "isodate": lambda v: datetime.fromisoformat(str(v)).isoformat(),
    "bool": lambda v: str(v).lower() in ("true", "1", "yes"),
    "default": lambda v: v,
}

def main(data: list[dict], mappings: list[dict],
         drop_unmapped: bool = False) -> list[dict]:
    """Apply field-level transformations to each record."""
    results = []
    for row in data:
        new_row = {} if drop_unmapped else dict(row)
        for m in mappings:
            source_val = row.get(m["source"])
            transform_fn = TRANSFORMS.get(m.get("transform", "default"),
                                           TRANSFORMS["default"])
            new_row[m["target"]] = transform_fn(source_val)
        results.append(new_row)
    return results
```

---

## AI Processing

### `llm_prompt`

**Description:** Sends a prompt to an LLM provider (OpenAI, Anthropic, or compatible endpoint) with system instructions, returning the raw text completion and token usage metadata.

| Field | Detail |
|---|---|
| **Input** | `prompt: str`, `system: str = ""`, `provider: Literal["openai", "anthropic"] = "anthropic"`, `model: str = ""`, `max_tokens: int = 4096`, `temperature: float = 0.3` |
| **Output** | `dict` with `text: str`, `model: str`, `usage: dict` |
| **Key Dependencies** | `anthropic`, `openai` |
| **MCP Alternative** | None; this IS the core LLM call |

```python
import os

def main(prompt: str, system: str = "", provider: str = "anthropic",
         model: str = "", max_tokens: int = 4096,
         temperature: float = 0.3) -> dict:
    """Send a prompt to an LLM and return the completion."""

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resolved_model = model or "claude-sonnet-4-20250514"
        msg = client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "text": msg.content[0].text,
            "model": resolved_model,
            "usage": {"input_tokens": msg.usage.input_tokens,
                      "output_tokens": msg.usage.output_tokens},
        }

    # OpenAI / compatible
    import openai
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    resolved_model = model or "gpt-4o"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=resolved_model, messages=messages,
        max_tokens=max_tokens, temperature=temperature,
    )
    choice = resp.choices[0]
    return {
        "text": choice.message.content,
        "model": resolved_model,
        "usage": {"input_tokens": resp.usage.prompt_tokens,
                  "output_tokens": resp.usage.completion_tokens},
    }
```

---

### `structured_extract`

**Description:** Sends content to an LLM with a JSON schema instruction, parses the response into a validated Python object, and retries with corrective prompts if the response fails schema validation.

| Field | Detail |
|---|---|
| **Input** | `content: str`, `schema: dict` (JSON Schema), `instructions: str = ""`, `retries: int = 2` |
| **Output** | `dict` with `data: Any` (validated), `raw: str`, `attempts: int` |
| **Key Dependencies** | `anthropic` or `openai`, `jsonschema` |
| **MCP Alternative** | None; core LLM extraction pattern |

```python
import json, os
from jsonschema import validate, ValidationError

def main(content: str, schema: dict, instructions: str = "",
         retries: int = 2) -> dict:
    """Extract structured data from content using an LLM with schema validation."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system_prompt = (
        "Extract information from the provided content and return ONLY valid JSON "
        "matching the schema below. No markdown fences, no commentary.\n\n"
        f"Schema:\n```json\n{json.dumps(schema, indent=2)}\n```"
    )
    if instructions:
        system_prompt += f"\n\nAdditional instructions: {instructions}"

    user_content = content
    for attempt in range(1, retries + 2):
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = msg.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            parsed = json.loads(raw)
            validate(instance=parsed, schema=schema)
            return {"data": parsed, "raw": raw, "attempts": attempt}
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt > retries:
                raise ValueError(f"Failed after {attempt} attempts: {exc}") from exc
            user_content = (
                f"Your previous response was invalid: {exc}\n\n"
                f"Original content:\n{content}\n\n"
                "Please try again, returning ONLY valid JSON."
            )

    raise RuntimeError("Unreachable")
```

---

### `embedding_generate`

**Description:** Generates vector embeddings for one or more text inputs using OpenAI, Voyage, or a local model, returning arrays ready for storage in a vector database.

| Field | Detail |
|---|---|
| **Input** | `texts: list[str]`, `provider: Literal["openai", "voyage"] = "openai"`, `model: str = ""` |
| **Output** | `dict` with `embeddings: list[list[float]]`, `model: str`, `dimensions: int` |
| **Key Dependencies** | `openai` or `voyageai` |
| **MCP Alternative** | None standard |

```python
import os

def main(texts: list[str], provider: str = "openai",
         model: str = "") -> dict:
    """Generate vector embeddings for text inputs."""

    if provider == "openai":
        import openai
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resolved = model or "text-embedding-3-small"
        resp = client.embeddings.create(input=texts, model=resolved)
        vecs = [item.embedding for item in resp.data]
        return {
            "embeddings": vecs,
            "model": resolved,
            "dimensions": len(vecs[0]) if vecs else 0,
        }

    if provider == "voyage":
        import voyageai
        client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
        resolved = model or "voyage-2"
        resp = client.embed(texts, model=resolved)
        return {
            "embeddings": resp.embeddings,
            "model": resolved,
            "dimensions": len(resp.embeddings[0]) if resp.embeddings else 0,
        }

    raise ValueError(f"Unsupported provider: {provider}")
```

---

## Notifications

### `slack_notify`

**Description:** Sends a message to a Slack channel or thread via the Slack Web API or an incoming webhook, supporting Block Kit for rich formatting.

| Field | Detail |
|---|---|
| **Input** | `channel: str`, `text: str`, `blocks: list[dict] = []`, `thread_ts: str = ""`, `use_webhook: bool = False` |
| **Output** | `dict` with `ok: bool`, `ts: str`, `channel: str` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | `@anthropic/slack-mcp` server -- exposes `slack_post_message`, `slack_list_channels`, etc. |

```python
import os, httpx

def main(channel: str, text: str, blocks: list[dict] | None = None,
         thread_ts: str = "", use_webhook: bool = False) -> dict:
    """Send a Slack message to a channel or thread."""

    if use_webhook:
        webhook_url = os.environ["SLACK_WEBHOOK_URL"]
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return {"ok": True, "ts": "", "channel": channel}

    token = os.environ["SLACK_BOT_TOKEN"]
    payload = {"channel": channel, "text": text}
    if blocks:
        payload["blocks"] = blocks
    if thread_ts:
        payload["thread_ts"] = thread_ts

    resp = httpx.post(
        "https://slack.com/api/chat.postMessage",
        json=payload,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        timeout=10,
    )
    data = resp.json()
    return {"ok": data.get("ok", False), "ts": data.get("ts", ""),
            "channel": data.get("channel", channel)}
```

---

### `discord_webhook`

**Description:** Posts a message or embed to a Discord channel via a webhook URL, with support for rich embeds, username overrides, and file attachments.

| Field | Detail |
|---|---|
| **Input** | `webhook_url: str`, `content: str = ""`, `embeds: list[dict] = []`, `username: str = ""` |
| **Output** | `dict` with `status: int`, `success: bool` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | None standard; wrap as custom MCP tool |

```python
import httpx

def main(webhook_url: str, content: str = "", embeds: list[dict] | None = None,
         username: str = "") -> dict:
    """Send a message or embed to Discord via webhook."""
    payload: dict = {}
    if content:
        payload["content"] = content
    if embeds:
        payload["embeds"] = embeds
    if username:
        payload["username"] = username

    if not payload:
        raise ValueError("Must provide content or embeds")

    resp = httpx.post(webhook_url, json=payload, timeout=10)
    return {
        "status": resp.status_code,
        "success": resp.status_code in (200, 204),
    }
```

---

### `email_send`

**Description:** Sends an email via SMTP or a transactional email API (SendGrid, Resend), supporting HTML body, plain-text fallback, and file attachments.

| Field | Detail |
|---|---|
| **Input** | `to: list[str]`, `subject: str`, `body_html: str = ""`, `body_text: str = ""`, `provider: Literal["smtp", "sendgrid", "resend"] = "resend"`, `from_addr: str = ""` |
| **Output** | `dict` with `success: bool`, `message_id: str` |
| **Key Dependencies** | `httpx`, `smtplib` (stdlib) |
| **MCP Alternative** | None standard |

```python
import os, httpx

def main(to: list[str], subject: str, body_html: str = "",
         body_text: str = "", provider: str = "resend",
         from_addr: str = "") -> dict:
    """Send an email via a transactional provider or SMTP."""
    sender = from_addr or os.environ.get("EMAIL_FROM", "noreply@example.com")

    if provider == "resend":
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
                     "Content-Type": "application/json"},
            json={
                "from": sender, "to": to, "subject": subject,
                "html": body_html or f"<pre>{body_text}</pre>",
                "text": body_text or "",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"success": True, "message_id": data.get("id", "")}

    if provider == "sendgrid":
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}",
                     "Content-Type": "application/json"},
            json={
                "personalizations": [{"to": [{"email": e} for e in to]}],
                "from": {"email": sender},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body_text or ""},
                    {"type": "text/html", "value": body_html or body_text},
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return {"success": True, "message_id": resp.headers.get("X-Message-Id", "")}

    # SMTP fallback
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(body_html or body_text, "html" if body_html else "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587))) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
    return {"success": True, "message_id": ""}
```

---

## Git Operations

### `git_commit_push`

**Description:** Stages specified files (or all changes), creates a commit with a conventional-commit message, and optionally pushes to the remote -- the bread-and-butter of automated code updates.

| Field | Detail |
|---|---|
| **Input** | `repo_path: str`, `message: str`, `files: list[str] = []`, `push: bool = True`, `branch: str = ""` |
| **Output** | `dict` with `commit_sha: str`, `branch: str`, `pushed: bool` |
| **Key Dependencies** | `subprocess` (stdlib), `git` CLI |
| **MCP Alternative** | `@anthropic/git-mcp` server -- exposes `git_status`, `git_commit`, `git_push`, etc. |

```python
import subprocess

def _git(repo: str, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo,
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()

def main(repo_path: str, message: str, files: list[str] | None = None,
         push: bool = True, branch: str = "") -> dict:
    """Stage, commit, and optionally push changes in a git repo."""
    if branch:
        try:
            _git(repo_path, "checkout", branch)
        except subprocess.CalledProcessError:
            _git(repo_path, "checkout", "-b", branch)

    # Stage
    if files:
        for f in files:
            _git(repo_path, "add", f)
    else:
        _git(repo_path, "add", "-A")

    # Commit
    _git(repo_path, "commit", "-m", message)
    sha = _git(repo_path, "rev-parse", "HEAD")

    current_branch = _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")

    pushed = False
    if push:
        _git(repo_path, "push", "-u", "origin", current_branch)
        pushed = True

    return {"commit_sha": sha, "branch": current_branch, "pushed": pushed}
```

---

### `git_branch_manage`

**Description:** Creates, lists, switches, or deletes branches in a local repository, with optional remote tracking setup.

| Field | Detail |
|---|---|
| **Input** | `repo_path: str`, `action: Literal["create", "switch", "delete", "list"]`, `branch: str = ""`, `from_ref: str = "main"` |
| **Output** | `dict` with `branch: str`, `action: str`, `branches: list[str]` (for list action) |
| **Key Dependencies** | `subprocess` (stdlib), `git` CLI |
| **MCP Alternative** | `@anthropic/git-mcp` |

```python
import subprocess

def _git(repo: str, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo,
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()

def main(repo_path: str, action: str = "list", branch: str = "",
         from_ref: str = "main") -> dict:
    """Create, switch, delete, or list branches."""

    if action == "list":
        raw = _git(repo_path, "branch", "-a")
        branches = [b.strip().lstrip("* ") for b in raw.splitlines()]
        return {"action": "list", "branches": branches, "branch": ""}

    if not branch:
        raise ValueError("branch name required for create/switch/delete")

    if action == "create":
        _git(repo_path, "checkout", "-b", branch, from_ref)
        return {"action": "create", "branch": branch, "branches": []}

    if action == "switch":
        _git(repo_path, "checkout", branch)
        return {"action": "switch", "branch": branch, "branches": []}

    if action == "delete":
        _git(repo_path, "branch", "-d", branch)
        return {"action": "delete", "branch": branch, "branches": []}

    raise ValueError(f"Unknown action: {action}")
```

---

### `git_read_repo`

**Description:** Reads repository structure and file contents without requiring a local clone, using either a local path or the GitHub API for remote repos.

| Field | Detail |
|---|---|
| **Input** | `repo: str` (local path or `owner/repo`), `path: str = ""`, `ref: str = "main"`, `depth: int = 2` |
| **Output** | `dict` with `tree: list[dict]`, `file_content: str` (if path points to a file) |
| **Key Dependencies** | `httpx`, `subprocess` (stdlib) |
| **MCP Alternative** | `@anthropic/github-mcp` for remote repos |

```python
import os, httpx, subprocess, pathlib

def main(repo: str, path: str = "", ref: str = "main",
         depth: int = 2) -> dict:
    """Read repository tree or file contents."""

    # Local repo
    if os.path.isdir(repo):
        target = pathlib.Path(repo) / path
        if target.is_file():
            return {"tree": [], "file_content": target.read_text(encoding="utf-8")}
        tree = []
        for item in sorted(target.rglob("*")):
            rel = item.relative_to(pathlib.Path(repo))
            if len(rel.parts) <= depth and not any(p.startswith(".") for p in rel.parts):
                tree.append({
                    "path": str(rel), "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        return {"tree": tree, "file_content": ""}

    # Remote GitHub repo
    headers = {"Authorization": f"token {os.environ['GITHUB_TOKEN']}",
               "Accept": "application/vnd.github.v3+json"}
    base = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = httpx.get(base, headers=headers, params={"ref": ref}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict) and data.get("type") == "file":
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return {"tree": [], "file_content": content}

    tree = [{"path": item["path"], "type": item["type"], "size": item.get("size", 0)}
            for item in data]
    return {"tree": tree, "file_content": ""}
```

---

## GitHub API

### `github_create_issue`

**Description:** Creates a new issue on a GitHub repository with title, body, labels, assignees, and milestone, returning the full issue URL and number.

| Field | Detail |
|---|---|
| **Input** | `repo: str` (`owner/repo`), `title: str`, `body: str = ""`, `labels: list[str] = []`, `assignees: list[str] = []`, `milestone: int = 0` |
| **Output** | `dict` with `number: int`, `url: str`, `html_url: str` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | `@anthropic/github-mcp` -- exposes `create_issue` |

```python
import os, httpx

def main(repo: str, title: str, body: str = "",
         labels: list[str] | None = None,
         assignees: list[str] | None = None,
         milestone: int = 0) -> dict:
    """Create a GitHub issue."""
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload: dict = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    if assignees:
        payload["assignees"] = assignees
    if milestone:
        payload["milestone"] = milestone

    resp = httpx.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers, json=payload, timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "number": data["number"],
        "url": data["url"],
        "html_url": data["html_url"],
    }
```

---

### `github_pull_request`

**Description:** Creates or updates a pull request, with support for draft PRs, auto-merge labels, and reviewer assignment.

| Field | Detail |
|---|---|
| **Input** | `repo: str`, `title: str`, `body: str`, `head: str`, `base: str = "main"`, `draft: bool = False`, `reviewers: list[str] = []` |
| **Output** | `dict` with `number: int`, `html_url: str`, `state: str` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | `@anthropic/github-mcp` -- exposes `create_pull_request` |

```python
import os, httpx

def main(repo: str, title: str, body: str, head: str,
         base: str = "main", draft: bool = False,
         reviewers: list[str] | None = None) -> dict:
    """Create a GitHub pull request."""
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "title": title, "body": body,
        "head": head, "base": base, "draft": draft,
    }

    resp = httpx.post(
        f"https://api.github.com/repos/{repo}/pulls",
        headers=headers, json=payload, timeout=15,
    )
    resp.raise_for_status()
    pr = resp.json()

    # Request reviewers if specified
    if reviewers:
        httpx.post(
            f"https://api.github.com/repos/{repo}/pulls/{pr['number']}/requested_reviewers",
            headers=headers,
            json={"reviewers": reviewers},
            timeout=10,
        )

    return {
        "number": pr["number"],
        "html_url": pr["html_url"],
        "state": pr["state"],
    }
```

---

### `github_workflow_dispatch`

**Description:** Triggers a GitHub Actions workflow via the repository dispatch or workflow_dispatch API, passing custom inputs and waiting optionally for completion status.

| Field | Detail |
|---|---|
| **Input** | `repo: str`, `workflow_id: str` (filename or ID), `ref: str = "main"`, `inputs: dict = {}`, `wait: bool = False`, `timeout: int = 300` |
| **Output** | `dict` with `triggered: bool`, `run_id: int`, `status: str`, `conclusion: str` |
| **Key Dependencies** | `httpx`, `time` (stdlib) |
| **MCP Alternative** | `@anthropic/github-mcp` |

```python
import os, httpx, time

def main(repo: str, workflow_id: str, ref: str = "main",
         inputs: dict | None = None, wait: bool = False,
         timeout: int = 300) -> dict:
    """Trigger a GitHub Actions workflow and optionally wait for completion."""
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    # Trigger
    resp = httpx.post(
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches",
        headers=headers,
        json={"ref": ref, "inputs": inputs or {}},
        timeout=15,
    )
    resp.raise_for_status()

    if not wait:
        return {"triggered": True, "run_id": 0, "status": "queued", "conclusion": ""}

    # Poll for the new run
    time.sleep(3)
    deadline = time.time() + timeout
    while time.time() < deadline:
        runs_resp = httpx.get(
            f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/runs",
            headers=headers, params={"branch": ref, "per_page": 1},
            timeout=15,
        )
        runs = runs_resp.json().get("workflow_runs", [])
        if runs:
            run = runs[0]
            if run["status"] == "completed":
                return {
                    "triggered": True, "run_id": run["id"],
                    "status": run["status"], "conclusion": run["conclusion"],
                }
        time.sleep(10)

    return {"triggered": True, "run_id": 0, "status": "timeout", "conclusion": ""}
```

---

## Database Operations

### `supabase_query`

**Description:** Executes queries against a Supabase project using the PostgREST API -- supports select, insert, update, upsert, and delete with filter chaining.

| Field | Detail |
|---|---|
| **Input** | `table: str`, `action: Literal["select", "insert", "update", "upsert", "delete"]`, `data: dict | list[dict] = {}`, `filters: list[dict] = []`, `select_columns: str = "*"`, `limit: int = 100` |
| **Output** | `dict` with `data: list[dict]`, `count: int`, `status: int` |
| **Key Dependencies** | `supabase` (supabase-py) |
| **MCP Alternative** | `@anthropic/supabase-mcp` server |

```python
import os
from supabase import create_client

def main(table: str, action: str = "select", data=None,
         filters: list[dict] | None = None,
         select_columns: str = "*", limit: int = 100) -> dict:
    """Execute a Supabase database operation."""
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )

    query = client.table(table)

    if action == "select":
        query = query.select(select_columns)
        for f in (filters or []):
            query = getattr(query, f.get("op", "eq"))(f["field"], f["value"])
        result = query.limit(limit).execute()
        return {"data": result.data, "count": len(result.data), "status": 200}

    if action == "insert":
        result = query.insert(data).execute()
        return {"data": result.data, "count": len(result.data), "status": 201}

    if action == "upsert":
        result = query.upsert(data).execute()
        return {"data": result.data, "count": len(result.data), "status": 200}

    if action == "update":
        q = query.update(data)
        for f in (filters or []):
            q = getattr(q, f.get("op", "eq"))(f["field"], f["value"])
        result = q.execute()
        return {"data": result.data, "count": len(result.data), "status": 200}

    if action == "delete":
        q = query.delete()
        for f in (filters or []):
            q = getattr(q, f.get("op", "eq"))(f["field"], f["value"])
        result = q.execute()
        return {"data": result.data, "count": len(result.data), "status": 200}

    raise ValueError(f"Unknown action: {action}")
```

---

### `sqlite_query`

**Description:** Opens (or creates) a local SQLite database and executes arbitrary SQL, returning rows as dictionaries -- ideal for lightweight local state, caching, and intermediate pipeline storage.

| Field | Detail |
|---|---|
| **Input** | `db_path: str`, `sql: str`, `params: list = []`, `mode: Literal["query", "execute", "script"] = "query"` |
| **Output** | `dict` with `rows: list[dict]`, `rowcount: int`, `lastrowid: int` |
| **Key Dependencies** | `sqlite3` (stdlib) |
| **MCP Alternative** | `@anthropic/sqlite-mcp` server |

```python
import sqlite3

def main(db_path: str, sql: str, params: list | None = None,
         mode: str = "query") -> dict:
    """Execute SQL against a SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        if mode == "script":
            cur.executescript(sql)
            conn.commit()
            return {"rows": [], "rowcount": cur.rowcount, "lastrowid": cur.lastrowid}

        if mode == "execute":
            cur.execute(sql, params or [])
            conn.commit()
            return {"rows": [], "rowcount": cur.rowcount, "lastrowid": cur.lastrowid}

        # query mode
        cur.execute(sql, params or [])
        rows = [dict(row) for row in cur.fetchall()]
        return {"rows": rows, "rowcount": len(rows), "lastrowid": 0}

    finally:
        conn.close()
```

---

### `airtable_ops`

**Description:** Reads, creates, updates, or deletes records in an Airtable base, handling pagination and field-type coercion automatically.

| Field | Detail |
|---|---|
| **Input** | `base_id: str`, `table_name: str`, `action: Literal["list", "create", "update", "delete"]`, `records: list[dict] = []`, `filter_formula: str = ""`, `max_records: int = 100` |
| **Output** | `dict` with `records: list[dict]`, `count: int` |
| **Key Dependencies** | `httpx` |
| **MCP Alternative** | None standard; wrap as custom MCP tool |

```python
import os, httpx

BASE_URL = "https://api.airtable.com/v0"

def _headers():
    return {
        "Authorization": f"Bearer {os.environ['AIRTABLE_API_KEY']}",
        "Content-Type": "application/json",
    }

def main(base_id: str, table_name: str, action: str = "list",
         records: list[dict] | None = None,
         filter_formula: str = "", max_records: int = 100) -> dict:
    """Perform CRUD operations on Airtable records."""
    url = f"{BASE_URL}/{base_id}/{table_name}"

    if action == "list":
        params: dict = {"maxRecords": max_records}
        if filter_formula:
            params["filterByFormula"] = filter_formula
        all_records, offset = [], None
        while True:
            if offset:
                params["offset"] = offset
            resp = httpx.get(url, headers=_headers(), params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            all_records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset or len(all_records) >= max_records:
                break
        return {"records": all_records, "count": len(all_records)}

    if action == "create":
        payload = {"records": [{"fields": r} for r in (records or [])]}
        resp = httpx.post(url, headers=_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        created = resp.json().get("records", [])
        return {"records": created, "count": len(created)}

    if action == "update":
        payload = {"records": records or []}  # expects [{"id": ..., "fields": {...}}]
        resp = httpx.patch(url, headers=_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        updated = resp.json().get("records", [])
        return {"records": updated, "count": len(updated)}

    if action == "delete":
        ids = [r if isinstance(r, str) else r.get("id") for r in (records or [])]
        resp = httpx.delete(url, headers=_headers(),
                            params={"records[]": ids}, timeout=15)
        resp.raise_for_status()
        return {"records": resp.json().get("records", []),
                "count": len(ids)}

    raise ValueError(f"Unknown action: {action}")
```

---

## Media Processing

### `image_transform`

**Description:** Performs common image operations -- resize, crop, convert format, compress, and generate thumbnails -- using Pillow, suitable for batch processing in data pipelines.

| Field | Detail |
|---|---|
| **Input** | `input_path: str`, `output_path: str`, `operations: list[dict]` (each with `type` and params like `width`, `height`, `format`, `quality`) |
| **Output** | `dict` with `output_path: str`, `width: int`, `height: int`, `size_bytes: int`, `format: str` |
| **Key Dependencies** | `Pillow` |
| **MCP Alternative** | None standard |

```python
from PIL import Image
import pathlib

def main(input_path: str, output_path: str,
         operations: list[dict] | None = None) -> dict:
    """Apply image transformations (resize, crop, convert, compress)."""
    img = Image.open(input_path)

    for op in (operations or []):
        op_type = op.get("type")

        if op_type == "resize":
            img = img.resize((op["width"], op["height"]), Image.LANCZOS)

        elif op_type == "thumbnail":
            img.thumbnail((op.get("max_width", 256), op.get("max_height", 256)),
                          Image.LANCZOS)

        elif op_type == "crop":
            img = img.crop((op["left"], op["top"], op["right"], op["bottom"]))

        elif op_type == "convert":
            if op.get("mode"):
                img = img.convert(op["mode"])  # e.g. "RGB", "L"

        elif op_type == "rotate":
            img = img.rotate(op.get("degrees", 0), expand=True)

    fmt = pathlib.Path(output_path).suffix.lstrip(".").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    quality = next((op.get("quality", 85) for op in (operations or [])
                    if op.get("type") == "compress"), 85)

    save_kwargs = {"format": fmt}
    if fmt in ("JPEG", "WEBP"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True

    img.save(output_path, **save_kwargs)
    out = pathlib.Path(output_path)
    return {
        "output_path": str(out.resolve()),
        "width": img.width,
        "height": img.height,
        "size_bytes": out.stat().st_size,
        "format": fmt,
    }
```

---

### `audio_transcribe`

**Description:** Transcribes audio files to text using the OpenAI Whisper API or a local Whisper model, with support for language detection, timestamps, and speaker diarization hints.

| Field | Detail |
|---|---|
| **Input** | `audio_path: str`, `provider: Literal["openai", "local"] = "openai"`, `language: str = ""`, `timestamps: bool = False` |
| **Output** | `dict` with `text: str`, `language: str`, `duration_seconds: float`, `segments: list[dict]` |
| **Key Dependencies** | `openai` (for API), `whisper` (for local) |
| **MCP Alternative** | None standard |

```python
import os

def main(audio_path: str, provider: str = "openai",
         language: str = "", timestamps: bool = False) -> dict:
    """Transcribe audio to text."""

    if provider == "openai":
        import openai
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        with open(audio_path, "rb") as f:
            kwargs = {"model": "whisper-1", "file": f}
            if language:
                kwargs["language"] = language
            if timestamps:
                kwargs["response_format"] = "verbose_json"
                kwargs["timestamp_granularities"] = ["segment"]

            result = client.audio.transcriptions.create(**kwargs)

        if timestamps and hasattr(result, "segments"):
            return {
                "text": result.text,
                "language": getattr(result, "language", language),
                "duration_seconds": getattr(result, "duration", 0),
                "segments": [{"start": s.start, "end": s.end, "text": s.text}
                             for s in result.segments],
            }
        return {
            "text": result.text if hasattr(result, "text") else str(result),
            "language": language,
            "duration_seconds": 0,
            "segments": [],
        }

    # Local whisper
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language=language or None)
    return {
        "text": result["text"],
        "language": result.get("language", ""),
        "duration_seconds": 0,
        "segments": result.get("segments", []),
    }
```

---

### `video_extract_frames`

**Description:** Extracts frames from a video file at specified intervals or timestamps using ffmpeg, returning image file paths and metadata suitable for downstream vision-model analysis.

| Field | Detail |
|---|---|
| **Input** | `video_path: str`, `output_dir: str`, `interval_seconds: float = 1.0`, `format: str = "jpg"`, `max_frames: int = 100` |
| **Output** | `dict` with `frames: list[str]` (paths), `count: int`, `video_duration: float` |
| **Key Dependencies** | `ffmpeg-python` or `subprocess` + `ffmpeg` CLI |
| **MCP Alternative** | None standard |

```python
import subprocess, pathlib, json

def main(video_path: str, output_dir: str, interval_seconds: float = 1.0,
         format: str = "jpg", max_frames: int = 100) -> dict:
    """Extract frames from a video at regular intervals."""
    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Get video duration via ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
        capture_output=True, text=True, check=True,
    )
    duration = float(json.loads(probe.stdout)["format"]["duration"])

    # Extract frames
    pattern = str(out / f"frame_%05d.{format}")
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval_seconds}",
        "-frames:v", str(max_frames),
        "-q:v", "2",
        pattern,
    ], capture_output=True, check=True)

    frames = sorted(str(f) for f in out.glob(f"frame_*.{format}"))
    return {
        "frames": frames[:max_frames],
        "count": len(frames[:max_frames]),
        "video_duration": duration,
    }
```

---

## n8n Conversion

### `n8n_parse_workflow`

**Description:** Parses an n8n workflow JSON export into a normalized intermediate representation (IR), extracting nodes, connections, triggers, and credentials references for translation into other formats.

| Field | Detail |
|---|---|
| **Input** | `workflow_json: dict | str` (raw JSON or path to file), `resolve_credentials: bool = False` |
| **Output** | `dict` with `name: str`, `nodes: list[dict]`, `connections: dict`, `triggers: list[dict]`, `variables: list[str]` |
| **Key Dependencies** | `json` (stdlib) |
| **MCP Alternative** | None; factory-specific tool |

```python
import json, pathlib

def main(workflow_json, resolve_credentials: bool = False) -> dict:
    """Parse an n8n workflow JSON into normalized IR."""
    if isinstance(workflow_json, str):
        if workflow_json.strip().startswith("{"):
            wf = json.loads(workflow_json)
        else:
            wf = json.loads(pathlib.Path(workflow_json).read_text())
    else:
        wf = workflow_json

    nodes = []
    triggers = []
    variables = set()

    for node in wf.get("nodes", []):
        parsed = {
            "id": node.get("id", ""),
            "name": node.get("name", ""),
            "type": node.get("type", ""),
            "parameters": node.get("parameters", {}),
            "position": node.get("position", [0, 0]),
            "credentials": node.get("credentials", {}),
            "disabled": node.get("disabled", False),
        }
        nodes.append(parsed)

        # Identify triggers
        node_type = node.get("type", "")
        if "trigger" in node_type.lower() or node_type.startswith("n8n-nodes-base.webhook"):
            triggers.append(parsed)

        # Extract variable references like {{ $env.VAR_NAME }}
        params_str = json.dumps(node.get("parameters", {}))
        import re
        for match in re.finditer(r'\$env\.(\w+)', params_str):
            variables.add(match.group(1))

    connections = {}
    for source_name, targets in wf.get("connections", {}).items():
        connections[source_name] = []
        for output_group in targets.values() if isinstance(targets, dict) else [targets]:
            for conn_list in (output_group if isinstance(output_group, list) else [output_group]):
                if isinstance(conn_list, list):
                    for conn in conn_list:
                        connections[source_name].append({
                            "target": conn.get("node", ""),
                            "target_input": conn.get("type", "main"),
                            "target_index": conn.get("index", 0),
                        })

    return {
        "name": wf.get("name", "Untitled"),
        "nodes": nodes,
        "connections": connections,
        "triggers": triggers,
        "variables": sorted(variables),
    }
```

---

### `n8n_node_mapper`

**Description:** Maps n8n node types to their WAT Systems Factory tool equivalents, producing a translation table that the factory assembly step uses to wire tool calls together.

| Field | Detail |
|---|---|
| **Input** | `nodes: list[dict]` (from `n8n_parse_workflow` output), `custom_mappings: dict = {}` |
| **Output** | `dict` with `mapped: list[dict]`, `unmapped: list[dict]`, `coverage: float` |
| **Key Dependencies** | None (stdlib only) |
| **MCP Alternative** | None; factory-specific tool |

```python
# Default n8n node type -> WAT tool mapping
DEFAULT_MAP = {
    "n8n-nodes-base.httpRequest": "rest_client",
    "n8n-nodes-base.webhook": "trigger_webhook",
    "n8n-nodes-base.code": "custom_code",
    "n8n-nodes-base.set": "transform_map",
    "n8n-nodes-base.if": "conditional_branch",
    "n8n-nodes-base.switch": "conditional_branch",
    "n8n-nodes-base.merge": "data_merge",
    "n8n-nodes-base.splitInBatches": "batch_splitter",
    "n8n-nodes-base.gmail": "email_send",
    "n8n-nodes-base.slack": "slack_notify",
    "n8n-nodes-base.github": "github_create_issue",
    "n8n-nodes-base.postgres": "postgres_query",
    "n8n-nodes-base.mysql": "mysql_query",
    "n8n-nodes-base.airtable": "airtable_ops",
    "n8n-nodes-base.googleSheets": "sheets_read_write",
    "n8n-nodes-base.openAi": "llm_prompt",
    "@n8n/n8n-nodes-langchain.agent": "agent_orchestrator",
    "n8n-nodes-base.respondToWebhook": "webhook_response",
    "n8n-nodes-base.cron": "trigger_cron",
    "n8n-nodes-base.readWriteFile": "json_read_write",
    "n8n-nodes-base.discord": "discord_webhook",
}

def main(nodes: list[dict], custom_mappings: dict | None = None) -> dict:
    """Map n8n node types to WAT tool equivalents."""
    mapping = {**DEFAULT_MAP, **(custom_mappings or {})}

    mapped = []
    unmapped = []
    for node in nodes:
        n8n_type = node.get("type", "")
        wat_tool = mapping.get(n8n_type)
        entry = {**node, "wat_tool": wat_tool}
        if wat_tool:
            mapped.append(entry)
        else:
            unmapped.append(entry)

    total = len(nodes) or 1
    return {
        "mapped": mapped,
        "unmapped": unmapped,
        "coverage": round(len(mapped) / total, 4),
    }
```

---

### `n8n_trigger_translate`

**Description:** Converts n8n trigger nodes (webhook, cron, manual, polling) into factory-native trigger definitions, preserving schedules, URL paths, and authentication requirements.

| Field | Detail |
|---|---|
| **Input** | `triggers: list[dict]` (from `n8n_parse_workflow`), `base_url: str = ""` |
| **Output** | `list[dict]` each with `type`, `config`, `original_node` |
| **Key Dependencies** | None (stdlib only) |
| **MCP Alternative** | None; factory-specific tool |

```python
def main(triggers: list[dict], base_url: str = "") -> list[dict]:
    """Translate n8n trigger nodes to factory trigger definitions."""
    translated = []

    for trigger in triggers:
        n8n_type = trigger.get("type", "")
        params = trigger.get("parameters", {})

        if "webhook" in n8n_type.lower():
            config = {
                "type": "webhook",
                "method": params.get("httpMethod", "POST"),
                "path": params.get("path", "/webhook"),
                "full_url": f"{base_url}{params.get('path', '/webhook')}" if base_url else "",
                "auth": params.get("authentication", "none"),
                "response_mode": params.get("responseMode", "onReceived"),
            }
        elif "cron" in n8n_type.lower() or "schedule" in n8n_type.lower():
            rule = params.get("rule", {})
            cron_expr = rule.get("cronExpression", params.get("cronExpression", ""))
            interval = params.get("interval", [{}])
            config = {
                "type": "cron",
                "expression": cron_expr,
                "interval": interval[0] if isinstance(interval, list) else interval,
                "timezone": params.get("timezone", "UTC"),
            }
        elif "manual" in n8n_type.lower():
            config = {"type": "manual", "description": "Manually triggered"}
        else:
            config = {
                "type": "polling",
                "poll_interval": params.get("pollTimes", {}).get("item", [{}]),
                "resource": params.get("resource", ""),
            }

        translated.append({
            "type": config["type"],
            "config": config,
            "original_node": trigger.get("name", ""),
        })

    return translated
```

---

## Agent Teams Coordination

### `task_decompose`

**Description:** Takes a high-level objective and decomposes it into an ordered list of subtasks with dependency edges, estimated complexity, and suggested tool assignments -- the planning phase for multi-agent execution.

| Field | Detail |
|---|---|
| **Input** | `objective: str`, `context: str = ""`, `max_subtasks: int = 10`, `available_tools: list[str] = []` |
| **Output** | `dict` with `subtasks: list[dict]` (each with `id`, `description`, `dependencies`, `tools`, `complexity`), `execution_order: list[str]` |
| **Key Dependencies** | `anthropic` or `openai` (for LLM-based decomposition) |
| **MCP Alternative** | None; orchestration-layer tool |

```python
import json, os

def main(objective: str, context: str = "", max_subtasks: int = 10,
         available_tools: list[str] | None = None) -> dict:
    """Decompose an objective into ordered subtasks with dependencies."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    tools_hint = ""
    if available_tools:
        tools_hint = f"\n\nAvailable tools: {', '.join(available_tools)}"

    system = (
        "You are a task-planning agent. Decompose the given objective into subtasks. "
        "Return ONLY valid JSON with this structure:\n"
        '{"subtasks": [{"id": "t1", "description": "...", '
        '"dependencies": [], "tools": ["tool_name"], '
        '"complexity": "low|medium|high"}], '
        '"execution_order": ["t1", "t2"]}\n'
        f"Maximum {max_subtasks} subtasks. Minimize dependencies for parallelism."
        f"{tools_hint}"
    )

    prompt = f"Objective: {objective}"
    if context:
        prompt += f"\n\nContext:\n{context}"

    msg = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=4096,
        temperature=0.2, system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)
```

---

### `subagent_spawn`

**Description:** Spawns a sub-agent to execute a single subtask, managing prompt construction, tool injection, timeout, and result collection -- the execution unit for parallel agent teams.

| Field | Detail |
|---|---|
| **Input** | `task: dict` (from `task_decompose`), `agent_config: dict` (model, temperature, tools), `inputs: dict = {}`, `timeout: int = 120` |
| **Output** | `dict` with `task_id: str`, `status: Literal["success", "error", "timeout"]`, `result: Any`, `usage: dict` |
| **Key Dependencies** | `anthropic` or `openai`, `asyncio` |
| **MCP Alternative** | None; orchestration-layer tool |

```python
import os, json, asyncio

async def _execute(task: dict, agent_config: dict, inputs: dict,
                   timeout: int) -> dict:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system = (
        f"You are a specialist agent. Complete this task precisely:\n"
        f"Task: {task['description']}\n\n"
        f"Available tools: {', '.join(task.get('tools', []))}\n"
        "Return your result as JSON."
    )
    user_content = json.dumps({"task": task, "inputs": inputs}, indent=2)

    try:
        msg = await asyncio.wait_for(
            client.messages.create(
                model=agent_config.get("model", "claude-sonnet-4-20250514"),
                max_tokens=agent_config.get("max_tokens", 4096),
                temperature=agent_config.get("temperature", 0.2),
                system=system,
                messages=[{"role": "user", "content": user_content}],
            ),
            timeout=timeout,
        )
        return {
            "task_id": task["id"],
            "status": "success",
            "result": msg.content[0].text,
            "usage": {"input_tokens": msg.usage.input_tokens,
                      "output_tokens": msg.usage.output_tokens},
        }
    except asyncio.TimeoutError:
        return {"task_id": task["id"], "status": "timeout", "result": None, "usage": {}}
    except Exception as exc:
        return {"task_id": task["id"], "status": "error",
                "result": str(exc), "usage": {}}

def main(task: dict, agent_config: dict | None = None,
         inputs: dict | None = None, timeout: int = 120) -> dict:
    """Spawn a sub-agent to execute a single subtask."""
    config = agent_config or {"model": "claude-sonnet-4-20250514"}
    return asyncio.run(_execute(task, config, inputs or {}, timeout))
```

---

### `result_merge`

**Description:** Collects results from multiple sub-agent executions, resolves conflicts, fills gaps from failed tasks, and assembles a unified output -- the synthesis step that closes the agent-team loop.

| Field | Detail |
|---|---|
| **Input** | `results: list[dict]` (from `subagent_spawn`), `strategy: Literal["concat", "merge_json", "summarize"] = "merge_json"`, `objective: str = ""` |
| **Output** | `dict` with `merged: Any`, `failures: list[dict]`, `success_rate: float` |
| **Key Dependencies** | `json` (stdlib); optionally `anthropic` for summarize strategy |
| **MCP Alternative** | None; orchestration-layer tool |

```python
import json, os

def main(results: list[dict], strategy: str = "merge_json",
         objective: str = "") -> dict:
    """Merge results from multiple sub-agent executions."""
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] != "success"]

    if strategy == "concat":
        merged = "\n\n---\n\n".join(
            f"## Task {r['task_id']}\n{r['result']}" for r in successes
        )

    elif strategy == "merge_json":
        merged = {}
        for r in successes:
            try:
                data = json.loads(r["result"]) if isinstance(r["result"], str) else r["result"]
                if isinstance(data, dict):
                    merged.update(data)
                else:
                    merged[r["task_id"]] = data
            except (json.JSONDecodeError, TypeError):
                merged[r["task_id"]] = r["result"]

    elif strategy == "summarize":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        all_results = "\n\n".join(
            f"Task {r['task_id']}:\n{r['result']}" for r in successes
        )
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=4096,
            temperature=0.2,
            system="Synthesize these sub-task results into a coherent final answer.",
            messages=[{"role": "user",
                       "content": f"Objective: {objective}\n\nResults:\n{all_results}"}],
        )
        merged = msg.content[0].text
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    total = len(results) or 1
    return {
        "merged": merged,
        "failures": [{"task_id": f["task_id"], "status": f["status"],
                       "error": f.get("result")} for f in failures],
        "success_rate": round(len(successes) / total, 4),
    }
```

---

## GitHub Agent HQ Interaction

### `issue_parse`

**Description:** Fetches a GitHub issue and parses its body into structured fields -- extracting task checkboxes, metadata blocks, labels, assignees, and linked PRs -- providing the canonical input format for Agent HQ dispatch.

| Field | Detail |
|---|---|
| **Input** | `repo: str`, `issue_number: int` |
| **Output** | `dict` with `title: str`, `body: str`, `labels: list[str]`, `assignees: list[str]`, `checkboxes: list[dict]`, `metadata: dict`, `linked_prs: list[int]` |
| **Key Dependencies** | `httpx`, `re` (stdlib) |
| **MCP Alternative** | `@anthropic/github-mcp` for raw issue fetch; parsing is custom |

```python
import os, re, httpx

def main(repo: str, issue_number: int) -> dict:
    """Fetch and parse a GitHub issue into structured fields."""
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = httpx.get(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=headers, timeout=15,
    )
    resp.raise_for_status()
    issue = resp.json()

    body = issue.get("body", "") or ""

    # Parse checkboxes: - [ ] or - [x]
    checkboxes = []
    for match in re.finditer(r'^[\s]*-\s+\[([ xX])\]\s+(.*)', body, re.MULTILINE):
        checkboxes.append({
            "checked": match.group(1).lower() == "x",
            "text": match.group(2).strip(),
            "raw": match.group(0),
        })

    # Parse metadata blocks: <!-- key: value --> or **Key:** value
    metadata = {}
    for match in re.finditer(r'<!--\s*(\w+)\s*:\s*(.*?)\s*-->', body):
        metadata[match.group(1)] = match.group(2)
    for match in re.finditer(r'\*\*(\w[\w\s]*)\*\*:\s*(.*)', body):
        metadata[match.group(1).strip()] = match.group(2).strip()

    # Find linked PR references: #123 or GH-123
    linked_prs = [int(m) for m in re.findall(r'(?:^|\s)#(\d+)', body)
                  if int(m) != issue_number]

    return {
        "title": issue.get("title", ""),
        "body": body,
        "labels": [l["name"] for l in issue.get("labels", [])],
        "assignees": [a["login"] for a in issue.get("assignees", [])],
        "checkboxes": checkboxes,
        "metadata": metadata,
        "linked_prs": linked_prs,
    }
```

---

### `pr_create_from_changes`

**Description:** Creates a complete pull request from a set of file changes -- handles branch creation, file writing, committing, pushing, and PR creation in one atomic operation, designed for Agent HQ automated code contributions.

| Field | Detail |
|---|---|
| **Input** | `repo: str`, `branch: str`, `title: str`, `body: str`, `files: list[dict]` (each with `path`, `content`), `base: str = "main"`, `labels: list[str] = []` |
| **Output** | `dict` with `pr_number: int`, `pr_url: str`, `commit_sha: str`, `branch: str` |
| **Key Dependencies** | `httpx`, `base64` (stdlib) |
| **MCP Alternative** | `@anthropic/github-mcp` for individual steps; this bundles them |

```python
import os, httpx, base64

def _gh(method, path, **kwargs):
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = httpx.request(method, f"https://api.github.com{path}",
                         headers=headers, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json() if resp.content else {}

def main(repo: str, branch: str, title: str, body: str,
         files: list[dict], base: str = "main",
         labels: list[str] | None = None) -> dict:
    """Create a PR with file changes in a single operation."""

    # 1. Get base branch SHA
    ref_data = _gh("GET", f"/repos/{repo}/git/ref/heads/{base}")
    base_sha = ref_data["object"]["sha"]

    # 2. Create branch
    try:
        _gh("POST", f"/repos/{repo}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": base_sha})
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 422:  # branch already exists
            raise

    # 3. Create/update files via Contents API
    commit_sha = ""
    for file in files:
        # Check if file exists to get its SHA
        existing_sha = None
        try:
            existing = _gh("GET", f"/repos/{repo}/contents/{file['path']}",
                          params={"ref": branch})
            existing_sha = existing.get("sha")
        except httpx.HTTPStatusError:
            pass

        payload = {
            "message": f"Add/update {file['path']}",
            "content": base64.b64encode(file["content"].encode()).decode(),
            "branch": branch,
        }
        if existing_sha:
            payload["sha"] = existing_sha

        result = _gh("PUT", f"/repos/{repo}/contents/{file['path']}", json=payload)
        commit_sha = result.get("commit", {}).get("sha", commit_sha)

    # 4. Create PR
    pr_payload = {"title": title, "body": body, "head": branch, "base": base}
    pr = _gh("POST", f"/repos/{repo}/pulls", json=pr_payload)

    # 5. Add labels
    if labels:
        _gh("POST", f"/repos/{repo}/issues/{pr['number']}/labels",
            json={"labels": labels})

    return {
        "pr_number": pr["number"],
        "pr_url": pr["html_url"],
        "commit_sha": commit_sha,
        "branch": branch,
    }
```

---

### `checkbox_update`

**Description:** Updates the checked/unchecked state of specific task checkboxes within a GitHub issue body, preserving all other content -- the primary mechanism for Agent HQ to report progress on multi-step tasks.

| Field | Detail |
|---|---|
| **Input** | `repo: str`, `issue_number: int`, `updates: list[dict]` (each with `text: str` or `index: int`, `checked: bool`) |
| **Output** | `dict` with `updated: int`, `body_preview: str` (first 500 chars of new body) |
| **Key Dependencies** | `httpx`, `re` (stdlib) |
| **MCP Alternative** | `@anthropic/github-mcp` for raw issue update; checkbox logic is custom |

```python
import os, re, httpx

def main(repo: str, issue_number: int, updates: list[dict]) -> dict:
    """Update checkbox states in a GitHub issue body."""
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Fetch current issue body
    resp = httpx.get(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=headers, timeout=15,
    )
    resp.raise_for_status()
    body = resp.json().get("body", "") or ""

    # Find all checkboxes with their positions
    checkbox_pattern = re.compile(r'^([\s]*-\s+\[)([ xX])(\]\s+)(.*)', re.MULTILINE)
    matches = list(checkbox_pattern.finditer(body))

    updated_count = 0
    # Process updates in reverse order to preserve string positions
    for update in updates:
        target_text = update.get("text", "")
        target_index = update.get("index", -1)
        new_state = "x" if update["checked"] else " "

        for idx, match in enumerate(matches):
            checkbox_text = match.group(4).strip()
            if (target_text and target_text.lower() in checkbox_text.lower()) or \
               (target_index >= 0 and idx == target_index):
                prefix = match.group(1)
                suffix = match.group(3) + match.group(4)
                replacement = f"{prefix}{new_state}{suffix}"
                body = body[:match.start()] + replacement + body[match.end():]
                updated_count += 1
                # Re-find matches after edit (positions shifted)
                matches = list(checkbox_pattern.finditer(body))
                break

    # Update issue body
    httpx.patch(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=headers, json={"body": body}, timeout=15,
    )

    return {
        "updated": updated_count,
        "body_preview": body[:500],
    }
```

---

## Quick Reference: Tool Dependency Matrix

| Tool | `httpx` | `anthropic` | `openai` | `Pillow` | `supabase` | Stdlib Only |
|---|---|---|---|---|---|---|
| `firecrawl_scrape` | x | | | | | |
| `brave_search` | x | | | | | |
| `puppeteer_screenshot` | | | | | | |
| `csv_read_write` | | | | | | x |
| `json_read_write` | | | | | | x |
| `pdf_extract` | | | | | | |
| `rest_client` | x | | | | | |
| `graphql_client` | x | | | | | |
| `oauth_token_refresh` | x | | | | | |
| `filter_sort` | | | | | | x |
| `dedup` | | | | | | x |
| `transform_map` | | | | | | x |
| `llm_prompt` | | x | x | | | |
| `structured_extract` | | x | | | | |
| `embedding_generate` | | | x | | | |
| `slack_notify` | x | | | | | |
| `discord_webhook` | x | | | | | |
| `email_send` | x | | | | | |
| `git_commit_push` | | | | | | x |
| `git_branch_manage` | | | | | | x |
| `git_read_repo` | x | | | | | |
| `github_create_issue` | x | | | | | |
| `github_pull_request` | x | | | | | |
| `github_workflow_dispatch` | x | | | | | |
| `supabase_query` | | | | | x | |
| `sqlite_query` | | | | | | x |
| `airtable_ops` | x | | | | | |
| `image_transform` | | | | x | | |
| `audio_transcribe` | | | x | | | |
| `video_extract_frames` | | | | | | x |
| `n8n_parse_workflow` | | | | | | x |
| `n8n_node_mapper` | | | | | | x |
| `n8n_trigger_translate` | | | | | | x |
| `task_decompose` | | x | | | | |
| `subagent_spawn` | | x | | | | |
| `result_merge` | | x | | | | |
| `issue_parse` | x | | | | | |
| `pr_create_from_changes` | x | | | | | |
| `checkbox_update` | x | | | | | |

---

## Environment Variables Reference

All tools expect secrets via environment variables. Never hard-code credentials.

| Variable | Used By |
|---|---|
| `FIRECRAWL_API_KEY` | `firecrawl_scrape` |
| `BRAVE_API_KEY` | `brave_search` |
| `ANTHROPIC_API_KEY` | `llm_prompt`, `structured_extract`, `task_decompose`, `subagent_spawn`, `result_merge` |
| `OPENAI_API_KEY` | `llm_prompt`, `embedding_generate`, `audio_transcribe` |
| `VOYAGE_API_KEY` | `embedding_generate` |
| `GITHUB_TOKEN` | `git_read_repo`, `github_create_issue`, `github_pull_request`, `github_workflow_dispatch`, `issue_parse`, `pr_create_from_changes`, `checkbox_update` |
| `SLACK_BOT_TOKEN` | `slack_notify` |
| `SLACK_WEBHOOK_URL` | `slack_notify` (webhook mode) |
| `RESEND_API_KEY` | `email_send` |
| `SENDGRID_API_KEY` | `email_send` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | `email_send` (SMTP mode) |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | `supabase_query` |
| `AIRTABLE_API_KEY` | `airtable_ops` |

---

## Lead Generation (from lead-gen-machine build)

### `lead_score`

**Description:** Scores a lead record against an ideal customer profile using weighted multi-dimensional matching across industry, company size, location, and keyword criteria.

| Field | Detail |
|---|---|
| **Input** | `company: dict` (with industry, company_size, location, description, technologies), `profile: dict` (with industry, company_size, location, keywords) |
| **Output** | `int` -- match score 0-100 |
| **Key Dependencies** | None (stdlib only) |
| **MCP Alternative** | None; pure logic tool |

**Scoring dimensions**: Industry match (0-30 points, with synonym expansion), Size match (0-25 points, with range overlap detection), Location match (0-20 points, with substring and word-level matching), Keyword match (0-25 points, proportional to keywords found).

**Pattern notes**: This scoring approach is reusable for any lead-matching or entity-ranking system. The synonym map and size range parser can be extended for new domains.

---

### `contact_extract`

**Description:** Extracts structured contact information from raw website content using Claude with a structured extraction prompt, falling back to regex when Claude API is unavailable.

| Field | Detail |
|---|---|
| **Input** | `content: str` (scraped webpage text), `url: str` |
| **Output** | `dict` with company_name, industry, company_size, location, description, email, phone, technologies |
| **Key Dependencies** | `anthropic` (primary), `re` (stdlib, fallback) |
| **MCP Alternative** | None; core LLM extraction pattern |

**Pattern notes**: The dual-mode approach (Claude primary + regex fallback) ensures the tool works even without API access. The extraction prompt should request ONLY valid JSON with no commentary to maximize parse success.

---

## Uptime Monitoring (from website-uptime-monitor build)

### `check_url`

**Description:** Performs an HTTP GET request to a target URL, measures response time, determines up/down status based on status code, and appends the result to a CSV log file. Designed for autonomous scheduled monitoring with Git-based audit trail.

| Field | Detail |
|---|---|
| **Input** | `url: str`, `timeout: int = 10`, `csv_path: str = "logs/uptime_log.csv"` |
| **Output** | `dict` with timestamp, status_code, response_time_ms, is_up, csv_updated |
| **Key Dependencies** | `requests` |
| **MCP Alternative** | Fetch MCP (but direct `requests` is simpler for single GET + timeout) |

**Exit code signaling**: Returns exit code 0 if up, 1 if down -- allowing GitHub Actions to show workflow status at-a-glance.

**CSV schema**: timestamp (ISO 8601 UTC), url, status_code (int, 0 if timeout/error), response_time_ms (float), is_up (boolean, True if status_code < 400).

**Failure handling**: All HTTP exceptions (Timeout, ConnectionError, RequestException) are caught and recorded as "down" status with status_code=0. No exception crashes the tool - every check produces a CSV entry.

**Pattern notes**: This is the minimal viable monitoring tool. No detection logic, no alerting, just raw data collection. The tool itself is stateless - all state lives in the Git-committed CSV file. Suitable for systems where simplicity and zero external dependencies are priorities.

**Concurrency**: The tool itself is concurrency-safe (CSV opens in append mode), but the workflow should use GitHub Actions `concurrency` setting to prevent simultaneous runs that could cause git push conflicts.

**Extension points**: Add auth headers for authenticated endpoints, add retry logic for transient failures, add response body validation (regex checks), add multiple URLs via loop or matrix strategy.

---

> **Next steps:** Each tool pattern above can be instantiated by the factory's `assemble_workflow` step. To add a new tool, copy any pattern above, implement `main()`, and register it in the factory's tool registry.
