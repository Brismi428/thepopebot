#!/usr/bin/env python3
"""
scrape_blog_post.py

Fetches and extracts clean content from a blog post URL.
Tries Firecrawl API first, falls back to direct HTTP + BeautifulSoup.

Usage:
    python scrape_blog_post.py --url https://example.com/blog/post

Output:
    JSON to stdout with status, markdown_content, title, author, publish_date, url, error
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

try:
    import httpx
    from bs4 import BeautifulSoup
    import html2text
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_with_firecrawl(url: str) -> Dict[str, Any]:
    """
    Scrape URL using Firecrawl API.
    
    Args:
        url: Target blog post URL
    
    Returns:
        Dict with status, content, and metadata
    
    Raises:
        Exception: If Firecrawl scraping fails
    """
    if not FIRECRAWL_AVAILABLE:
        raise ImportError("firecrawl-py not installed")
    
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")
    
    logger.info(f"Attempting Firecrawl scrape of {url}")
    app = FirecrawlApp(api_key=api_key)
    
    result = app.scrape_url(url, params={"formats": ["markdown"]})
    
    markdown = result.get("markdown", "")
    metadata = result.get("metadata", {})
    
    if not markdown or len(markdown.strip()) < 100:
        raise ValueError(f"Firecrawl returned insufficient content: {len(markdown)} chars")
    
    return {
        "status": "success",
        "markdown_content": markdown.strip(),
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "publish_date": metadata.get("publishedTime", ""),
        "url": url,
        "error": None,
        "method": "firecrawl"
    }


def scrape_with_http_fallback(url: str) -> Dict[str, Any]:
    """
    Fallback scraper using direct HTTP + BeautifulSoup.
    
    Args:
        url: Target blog post URL
    
    Returns:
        Dict with status, content, and metadata
    
    Raises:
        Exception: If HTTP scraping fails
    """
    if not FALLBACK_AVAILABLE:
        raise ImportError("httpx, beautifulsoup4, or html2text not installed")
    
    logger.info(f"Attempting HTTP fallback scrape of {url}")
    
    response = httpx.get(
        url,
        timeout=30,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ContentRepurposer/1.0; +https://github.com/yourusername/content-repurposer)"
        }
    )
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text().strip() if title_tag else ""
    
    # Try to find article content in common semantic tags
    article = (
        soup.find("article") or
        soup.find("main") or
        soup.find("div", class_=lambda c: c and any(
            word in c.lower() for word in ["content", "post", "article", "entry"]
        )) or
        soup.find("div", id=lambda i: i and any(
            word in i.lower() for word in ["content", "post", "article", "entry"]
        ))
    )
    
    if not article:
        # Last resort: find largest div with significant text
        divs = soup.find_all("div")
        article = max(divs, key=lambda d: len(d.get_text()), default=None)
    
    if not article:
        raise ValueError("Could not locate article content in HTML")
    
    # Remove script, style, nav, header, footer tags
    for tag in article.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    
    # Convert HTML to Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Don't wrap lines
    markdown = h.handle(str(article))
    
    if len(markdown.strip()) < 100:
        raise ValueError(f"Extracted content too short: {len(markdown)} chars")
    
    # Try to extract author from meta tags
    author = ""
    author_meta = (
        soup.find("meta", attrs={"name": "author"}) or
        soup.find("meta", property="article:author") or
        soup.find("a", class_=lambda c: c and "author" in c.lower())
    )
    if author_meta:
        author = author_meta.get("content", "") or author_meta.get_text().strip()
    
    # Try to extract publish date
    publish_date = ""
    date_meta = (
        soup.find("meta", property="article:published_time") or
        soup.find("time") or
        soup.find("span", class_=lambda c: c and "date" in c.lower())
    )
    if date_meta:
        publish_date = date_meta.get("content", "") or date_meta.get("datetime", "") or date_meta.get_text().strip()
    
    return {
        "status": "success",
        "markdown_content": markdown.strip(),
        "title": title,
        "author": author,
        "publish_date": publish_date,
        "url": url,
        "error": None,
        "method": "http_fallback"
    }


def main(url: str) -> Dict[str, Any]:
    """
    Main scraping function. Tries Firecrawl first, falls back to HTTP.
    
    Args:
        url: Blog post URL to scrape
    
    Returns:
        Dict with scraping results
    """
    errors = []
    
    # Try Firecrawl first
    if FIRECRAWL_AVAILABLE and os.environ.get("FIRECRAWL_API_KEY"):
        try:
            result = scrape_with_firecrawl(url)
            logger.info(f"Successfully scraped with Firecrawl: {len(result['markdown_content'])} chars")
            return result
        except Exception as e:
            error_msg = f"Firecrawl failed: {str(e)}"
            logger.warning(error_msg)
            errors.append(error_msg)
    else:
        logger.info("Firecrawl not available, skipping to fallback")
    
    # Try HTTP fallback
    if FALLBACK_AVAILABLE:
        try:
            result = scrape_with_http_fallback(url)
            logger.info(f"Successfully scraped with HTTP fallback: {len(result['markdown_content'])} chars")
            return result
        except Exception as e:
            error_msg = f"HTTP fallback failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    else:
        errors.append("HTTP fallback libraries not installed")
    
    # Both methods failed
    return {
        "status": "error",
        "markdown_content": "",
        "title": "",
        "author": "",
        "publish_date": "",
        "url": url,
        "error": " | ".join(errors),
        "method": "none"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape blog post content and convert to markdown"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Blog post URL to scrape"
    )
    args = parser.parse_args()
    
    try:
        result = main(args.url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Exit with non-zero code if scraping failed
        sys.exit(0 if result["status"] == "success" else 1)
    
    except Exception as e:
        logger.exception("Unexpected error during scraping")
        error_result = {
            "status": "error",
            "markdown_content": "",
            "title": "",
            "author": "",
            "publish_date": "",
            "url": args.url,
            "error": f"Unexpected error: {str(e)}",
            "method": "none"
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)
