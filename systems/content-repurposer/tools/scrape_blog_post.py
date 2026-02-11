"""
Scrape Blog Post — Fetch and extract clean content from a blog post URL

Uses Firecrawl API as primary scraping method with HTTP + BeautifulSoup fallback.
Returns structured output with markdown content, metadata, and error information.

Inputs:
    - url (str): Target blog post URL to scrape

Outputs:
    - JSON: {status, markdown_content, title, author, publish_date, url, error}

Usage:
    python scrape_blog_post.py --url https://example.com/blog/post

Environment Variables:
    - FIRECRAWL_API_KEY: Firecrawl API key (optional, falls back to HTTP if missing)
"""

import argparse
import json
import logging
import os
import sys
from typing import Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def scrape_with_firecrawl(url: str) -> dict[str, Any]:
    """
    Scrape URL using Firecrawl API.

    Args:
        url: Target URL to scrape

    Returns:
        dict with markdown_content, title, author, publish_date

    Raises:
        Exception: If Firecrawl API call fails
    """
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        raise ImportError("firecrawl-py not installed. Install with: pip install firecrawl-py")

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")

    logger.info("Attempting Firecrawl scrape for: %s", url)
    app = FirecrawlApp(api_key=api_key)

    result = app.scrape_url(url, params={"formats": ["markdown"]})

    markdown_content = result.get("markdown", "")
    metadata = result.get("metadata", {})

    return {
        "markdown_content": markdown_content,
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "publish_date": metadata.get("publishedTime", ""),
    }


def scrape_with_http(url: str) -> dict[str, Any]:
    """
    Scrape URL using HTTP + BeautifulSoup fallback.

    Args:
        url: Target URL to scrape

    Returns:
        dict with markdown_content, title, author, publish_date

    Raises:
        Exception: If HTTP request or parsing fails
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
        import html2text
    except ImportError:
        raise ImportError(
            "Required packages not installed. Install with: pip install httpx beautifulsoup4 html2text"
        )

    logger.info("Attempting HTTP + BeautifulSoup scrape for: %s", url)

    # Fetch page
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ContentRepurposer/1.0; +https://github.com)"
    }
    resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
    resp.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text().strip()
    else:
        # Try h1 as fallback
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text().strip()

    # Extract author (common meta tags)
    author = ""
    author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find(
        "meta", attrs={"property": "article:author"}
    )
    if author_meta:
        author = author_meta.get("content", "")

    # Extract publish date (common meta tags)
    publish_date = ""
    date_meta = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find(
        "meta", attrs={"name": "publish_date"}
    )
    if date_meta:
        publish_date = date_meta.get("content", "")

    # Extract main content (try article, main, or first div with substantial text)
    content_elem = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=lambda c: c and "content" in c.lower())
    )

    if not content_elem:
        # Fallback: get body
        content_elem = soup.find("body")

    if not content_elem:
        raise ValueError("Could not find main content in page")

    # Remove script, style, nav, header, footer elements
    for tag in content_elem.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Convert to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0  # Don't wrap lines
    markdown_content = h.handle(str(content_elem))

    return {
        "markdown_content": markdown_content.strip(),
        "title": title,
        "author": author,
        "publish_date": publish_date,
    }


def main() -> dict[str, Any]:
    """
    Main entry point for the scrape tool.

    Returns:
        dict: Result containing status, markdown_content, metadata, and error info.
    """
    parser = argparse.ArgumentParser(description="Scrape blog post content from URL")
    parser.add_argument("--url", required=True, help="Blog post URL to scrape")
    args = parser.parse_args()

    logger.info("Starting scrape for URL: %s", args.url)

    result = {
        "status": "error",
        "markdown_content": "",
        "title": "",
        "author": "",
        "publish_date": "",
        "url": args.url,
        "error": None,
    }

    # Try Firecrawl first
    try:
        scraped = scrape_with_firecrawl(args.url)
        result.update(scraped)
        result["status"] = "success"
        logger.info("Firecrawl scrape succeeded")
        return result
    except Exception as e:
        logger.warning("Firecrawl scrape failed: %s. Falling back to HTTP.", str(e))

    # Fallback to HTTP + BeautifulSoup
    try:
        scraped = scrape_with_http(args.url)
        result.update(scraped)
        result["status"] = "success"
        logger.info("HTTP scrape succeeded")
        return result
    except Exception as e:
        logger.error("HTTP scrape failed: %s", str(e))
        result["error"] = str(e)
        return result


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] != "success":
        sys.exit(1)
