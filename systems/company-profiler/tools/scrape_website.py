"""
Scrape Website — Fetches a company website and returns clean text content.

Checks for available scraping tools in order of preference:
1. Firecrawl MCP (best quality, handles JS rendering)
2. Direct HTTP with requests + beautifulsoup4 (fallback)

Scrapes the homepage and key subpages: /about, /pricing, /careers, /products.

Inputs:
    - url (str): The company website URL to scrape

Outputs:
    - JSON file with scraped content keyed by page path

Usage:
    python scrape_website.py --url https://example.com --output scraped.json

Environment Variables:
    - FIRECRAWL_API_KEY: Firecrawl API key (optional — enables Firecrawl scraping)
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any
from urllib.parse import urljoin, urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SUBPAGES = [
    "/about",
    "/about-us",
    "/pricing",
    "/careers",
    "/jobs",
    "/products",
    "/services",
]


def scrape_with_requests(url: str) -> dict[str, Any]:
    """Scrape a URL using requests + beautifulsoup4."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("requests or beautifulsoup4 not installed")
        return {"url": url, "content": "", "error": "Missing dependencies: requests, beautifulsoup4"}

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; WATBot/1.0; +https://github.com/wat-systems)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        return {
            "url": url,
            "content": clean_text[:10000],  # Limit content size
            "status_code": response.status_code,
            "error": None,
        }
    except requests.RequestException as e:
        logger.warning("Failed to scrape %s: %s", url, e)
        return {"url": url, "content": "", "error": str(e)}


def scrape_with_firecrawl(url: str, api_key: str) -> dict[str, Any]:
    """Scrape a URL using the Firecrawl API."""
    try:
        import requests
    except ImportError:
        return {"url": url, "content": "", "error": "requests not installed"}

    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"url": url, "formats": ["markdown"]},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("data", {}).get("markdown", "")
        return {
            "url": url,
            "content": content[:10000],
            "error": None,
        }
    except Exception as e:
        logger.warning("Firecrawl failed for %s: %s", url, e)
        return {"url": url, "content": "", "error": str(e)}


def scrape_page(url: str, firecrawl_key: str | None = None) -> dict[str, Any]:
    """Scrape a single page using the best available method."""
    if firecrawl_key:
        logger.info("Scraping with Firecrawl: %s", url)
        result = scrape_with_firecrawl(url, firecrawl_key)
        if result["content"]:
            return result
        logger.warning("Firecrawl failed, falling back to requests")

    logger.info("Scraping with requests: %s", url)
    return scrape_with_requests(url)


def main() -> dict[str, Any]:
    """Scrape a company website and its key subpages."""
    parser = argparse.ArgumentParser(description="Scrape a company website")
    parser.add_argument("--url", required=True, help="Company website URL")
    parser.add_argument("--output", default="scraped.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting website scrape: %s", args.url)

    try:
        firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
        if firecrawl_key:
            logger.info("Firecrawl API key found — using Firecrawl as primary scraper")
        else:
            logger.info("No Firecrawl API key — using requests + beautifulsoup4")

        # Normalize base URL
        parsed = urlparse(args.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Scrape homepage
        pages = {}
        homepage = scrape_page(args.url, firecrawl_key)
        pages["/"] = homepage

        # Scrape subpages
        for subpage in SUBPAGES:
            full_url = urljoin(base_url, subpage)
            result = scrape_page(full_url, firecrawl_key)
            if result["content"]:
                pages[subpage] = result
            time.sleep(1)  # Rate limiting

        # Count successful scrapes
        successful = sum(1 for p in pages.values() if p.get("content"))
        logger.info("Scraped %d pages successfully out of %d attempted", successful, len(pages))

        output = {
            "base_url": base_url,
            "pages": pages,
            "total_pages": len(pages),
            "successful_pages": successful,
            "scraper": "firecrawl" if firecrawl_key else "requests+bs4",
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        logger.info("Scraped content written to %s", args.output)
        return {"status": "success", "data": output}

    except Exception as e:
        logger.error("Scraping failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
