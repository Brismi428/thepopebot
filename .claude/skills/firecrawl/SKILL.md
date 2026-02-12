---
name: firecrawl
description: Web scraping, crawling, and data extraction via the Firecrawl API. Use this skill for ANY task that involves fetching web page content, crawling websites, discovering URLs, searching the web with content extraction, or extracting structured data from web pages. Firecrawl replaces requests+BeautifulSoup, urllib, Selenium, and Playwright-based scraping in all new WAT systems.
---

# Firecrawl Integration Guide

## Overview

Firecrawl is the **preferred tool for all web scraping, crawling, and data extraction** in WAT systems. It handles proxies, caching, rate limits, JavaScript rendering, anti-bot bypasses, and dynamic content automatically.

**Do not use** `requests + BeautifulSoup`, `urllib`, `httpx` with HTML parsing, `Selenium`, or `Playwright` for scraping in new systems. Use Firecrawl instead.

Six endpoints cover every web data need:

| Endpoint | Use When |
|----------|----------|
| `/scrape` | You need content from a single URL |
| `/crawl` | You need content from multiple pages on a site |
| `/map` | You need to discover all URLs on a domain |
| `/search` | You need to find pages by keyword and get their content |
| `/extract` | You need structured data matching a JSON schema |
| `/agent` | You can describe what you need in plain English but don't know where it lives |

## Setup

```python
# pip install firecrawl-py

import os
from firecrawl import Firecrawl

# FIRECRAWL_API_KEY is available via LLM_SECRETS
app = Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"])
```

## /scrape -- Single URL to Clean Data

Converts one URL into markdown, HTML, JSON, links, screenshots, or a summary. Handles JavaScript-rendered pages, PDFs, and images.

```python
# Basic: get markdown (ideal for LLM consumption)
result = app.scrape("https://example.com")
print(result["markdown"])

# Multiple formats at once
result = app.scrape("https://example.com", formats=["markdown", "html", "links"])
print(result["markdown"])
print(result["links"])  # list of URLs found on page

# Main content only (strips navs, footers, sidebars)
result = app.scrape("https://example.com", formats=["markdown"], only_main_content=True)

# With browser actions (click, scroll, fill forms, wait)
result = app.scrape("https://example.com", formats=["markdown"], actions=[
    {"type": "click", "selector": "#load-more"},
    {"type": "wait", "milliseconds": 2000},
    {"type": "screenshot"}
])
```

**When to use:** Fetching a single page's content. Use instead of `requests.get()` + BeautifulSoup parsing.

## /crawl -- Recursive Site Crawl

Discovers and scrapes multiple pages from a site. Follows links recursively, respects sitemaps.

```python
# Crawl up to 50 pages
result = app.crawl("https://docs.example.com", limit=50)
for page in result["data"]:
    print(page["metadata"]["title"])
    print(page["markdown"][:200])

# Crawl with scrape options applied to every page
from firecrawl import ScrapeOptions
result = app.crawl(
    "https://docs.example.com",
    limit=100,
    scrape_options=ScrapeOptions(formats=["markdown", "html"])
)

# Async: start crawl and check later
job = app.start_crawl("https://docs.example.com", limit=200)
# ... do other work ...
status = app.get_crawl_status(job["id"])

# Include subdomains
result = app.crawl("https://example.com", limit=100, allow_subdomains=True)

# Crawl the entire domain (not just the URL path subtree)
result = app.crawl("https://example.com/docs", limit=100, crawl_entire_domain=True)
```

**When to use:** Scraping documentation sites, blogs, or any multi-page content. Use instead of writing your own link-following crawler.

## /map -- Discover All URLs on a Domain

Returns a list of URLs found on a site without scraping their content. Fast way to understand site structure.

```python
result = app.map("https://example.com")
for url in result["links"]:
    print(url)

# With a limit
result = app.map("https://example.com", limit=500)
```

**When to use:** Site audits, building URL inventories, deciding which pages to scrape. Use before `/crawl` when you need to filter URLs first.

## /search -- Web Search + Content Extraction

Searches the web and optionally scrapes the results in one call. Combines search engine results with full page content.

```python
# Search and get markdown content from results
results = app.search(
    "firecrawl web scraping python",
    limit=5,
    scrape_options={"formats": ["markdown", "links"]}
)
for r in results["data"]:
    print(r["metadata"]["title"])
    print(r["markdown"][:200])

# Search with time filter (past week)
results = app.search("python release notes", limit=3, tbs="qdr:w")

# Search with geographic filter
results = app.search("local news", limit=5, location="Germany")

# Filter by source type
results = app.search("machine learning paper", limit=5, categories=["research"])
```

**Time filters (`tbs`):** `qdr:h` (past hour), `qdr:d` (past day), `qdr:w` (past week), `qdr:m` (past month), `qdr:y` (past year).

**Categories:** `github`, `research`, `pdf`.

**When to use:** Finding and fetching relevant pages when you don't have specific URLs. Use instead of a search API + separate scraping step.

## /extract -- AI-Powered Structured Extraction

Extracts structured data from one or more URLs using a JSON schema and/or a natural language prompt. The AI reads the pages and returns data matching your schema.

```python
# With JSON schema
schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "pricing_plans": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "string"},
                    "features": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    },
    "required": ["company_name", "pricing_plans"]
}

result = app.extract(
    urls=["https://example.com/pricing"],
    prompt="Extract the company name and all pricing plans with their features",
    schema=schema
)
print(result["data"])

# Prompt-only (no schema -- AI determines structure)
result = app.extract(
    urls=["https://example.com/about"],
    prompt="Extract the founding team members and their roles"
)

# Wildcard URL patterns (crawl + extract)
result = app.extract(
    urls=["https://example.com/blog/*"],
    prompt="Extract the title, author, and publication date from each blog post",
    schema={
        "type": "object",
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "author": {"type": "string"},
                        "date": {"type": "string"}
                    }
                }
            }
        }
    }
)
```

**When to use:** Pulling specific data points from pages into a defined structure. Use instead of scraping HTML and writing fragile CSS/XPath selectors.

## /agent -- Describe What You Need in Plain English

Tell the agent what data you want. It searches, navigates, and extracts autonomously. No URLs or schemas required (but both can be provided as hints).

```python
from pydantic import BaseModel, Field
from typing import List

# With Pydantic schema
class Founder(BaseModel):
    name: str
    role: str

class CompanyFounders(BaseModel):
    founders: List[Founder] = Field(description="List of company founders")

result = app.agent(
    prompt="Find the founders of Firecrawl and their roles",
    schema=CompanyFounders,
    model="spark-1-mini"  # or "spark-1-pro" for harder tasks
)
print(result["data"])

# Without schema -- returns unstructured answer
result = app.agent(
    prompt="What are the current pricing tiers for Vercel?",
    model="spark-1-mini"
)

# With URL hints and credit limit
result = app.agent(
    prompt="Extract all job openings and their locations",
    urls=["https://example.com/careers"],
    max_credits=50
)

# Check status for long-running jobs
job = app.agent(prompt="...", model="spark-1-pro")
status = app.get_agent_status(job["id"])
```

**Models:** `spark-1-mini` (default, cheaper) for straightforward tasks. `spark-1-pro` for complex multi-step extraction.

**When to use:** Exploratory data gathering when you're not sure which pages contain the data. Use when the task is easier to describe than to program.

## Choosing the Right Endpoint

```
Need content from a known URL?
  --> /scrape

Need content from many pages on one site?
  --> /crawl

Need a list of URLs on a site (no content)?
  --> /map

Need to find pages by keyword AND get content?
  --> /search

Need specific structured data from known URLs?
  --> /extract

Not sure where the data lives?
  --> /agent
```

## WAT System Integration

### Tool Template

Every Firecrawl-based tool in a WAT system should follow this pattern:

```python
"""
Scrapes/extracts/crawls [description of what this tool does].

Inputs: [describe inputs]
Outputs: [describe outputs]
"""

import logging
import os
import sys

from firecrawl import Firecrawl

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY not set")
        sys.exit(1)

    app = Firecrawl(api_key=api_key)

    try:
        # ... endpoint call here ...
        pass
    except Exception as e:
        logger.error("Firecrawl request failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### requirements.txt

```
firecrawl-py
```

### .env.example

```
FIRECRAWL_API_KEY=fc-your-api-key-here
```

The `FIRECRAWL_API_KEY` is provided via `LLM_SECRETS` in the Docker agent environment, so tools can read it from `os.environ` directly.

## Credit Costs

| Operation | Cost |
|-----------|------|
| Scrape | 1 credit/page |
| Crawl | 1 credit/page |
| Map | 1 credit/call |
| Search | 2 credits/10 results + scrape costs |
| Extract | varies by pages processed |
| Agent | varies; use `max_credits` to cap |

## Error Handling

The SDK raises exceptions on API errors. Always wrap calls in try/except:

```python
try:
    result = app.scrape("https://example.com")
except Exception as e:
    logger.error("Scrape failed: %s", e)
    sys.exit(1)
```

Common failure causes: invalid API key, rate limiting, target site blocking, timeout on large crawls.
