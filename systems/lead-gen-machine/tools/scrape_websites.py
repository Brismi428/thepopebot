"""
Scrape Websites — Scrapes company websites to extract raw content for contact extraction.

Inputs:
    - companies (list[dict]): Companies to scrape, each with url and domain fields
    - timeout (int): Per-request timeout in seconds (default: 15)

Outputs:
    - dict with:
        - scraped (list[dict]): Companies with scraped content added
        - success_count (int): Number of successfully scraped sites
        - failure_count (int): Number of failed scrapes

Usage:
    python scrape_websites.py --input output/search_results.json --output output/scraped_data.json

Environment Variables:
    - FIRECRAWL_API_KEY: Firecrawl API key (optional, enables better scraping)
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def scrape_firecrawl(url: str) -> dict:
    """Scrape a URL using the Firecrawl API."""
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "FIRECRAWL_API_KEY not set"}

    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=api_key)
        result = app.scrape_url(url, params={"formats": ["markdown"]})

        return {
            "success": True,
            "content": result.get("markdown", ""),
            "metadata": result.get("metadata", {}),
            "links": result.get("links", []),
        }
    except ImportError:
        return {"success": False, "error": "firecrawl-py not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def scrape_http(url: str, timeout: int = 15) -> dict:
    """Fallback scraper using httpx + basic HTML parsing."""
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        return {"success": False, "error": "httpx or beautifulsoup4 not installed"}

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LeadGenBot/1.0; research purposes)",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Truncate very long pages
        text = text[:15000]

        # Extract links
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:") or href.startswith("tel:"):
                links.append(href)
            elif href.startswith("/"):
                links.append(url.rstrip("/") + href)

        return {
            "success": True,
            "content": text,
            "metadata": {"title": soup.title.string if soup.title else ""},
            "links": links,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def scrape_url(url: str, timeout: int = 15) -> dict:
    """Scrape a URL, trying Firecrawl first then falling back to HTTP."""
    # Try Firecrawl first
    result = scrape_firecrawl(url)
    if result["success"]:
        return result

    logger.info("Firecrawl unavailable for %s, falling back to HTTP", url)
    return scrape_http(url, timeout)


def scrape_subpages(base_url: str, timeout: int = 15) -> dict:
    """Attempt to scrape common subpages for contact info."""
    subpages = ["/about", "/contact", "/team", "/about-us", "/contact-us"]
    combined_content = ""

    for subpage in subpages:
        full_url = base_url.rstrip("/") + subpage
        result = scrape_http(full_url, timeout)
        if result["success"] and result["content"]:
            combined_content += f"\n\n--- {subpage} ---\n" + result["content"][:5000]
            time.sleep(0.5)

    return {"content": combined_content, "subpages_tried": len(subpages)}


def main() -> dict[str, Any]:
    """
    Main entry point. Scrapes company websites for content.

    Returns:
        dict: Scraped data for each company.
    """
    parser = argparse.ArgumentParser(description="Scrape company websites")
    parser.add_argument("--input", required=True, help="Path to search results JSON")
    parser.add_argument("--output", default="output/scraped_data.json", help="Output file path")
    parser.add_argument("--timeout", type=int, default=15, help="Per-request timeout in seconds")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between requests in seconds")
    args = parser.parse_args()

    logger.info("Starting website scraping")

    try:
        # Load search results
        with open(args.input, "r", encoding="utf-8") as f:
            search_data = json.load(f)

        companies = search_data.get("data", {}).get("results", [])
        if not companies:
            logger.warning("No companies to scrape")
            return {"status": "success", "data": {"scraped": [], "success_count": 0, "failure_count": 0},
                    "message": "No companies to scrape"}

        logger.info("Scraping %d company websites", len(companies))

        scraped = []
        success_count = 0
        failure_count = 0

        for i, company in enumerate(companies):
            url = company.get("url", "")
            if not url:
                continue

            logger.info("Scraping %d/%d: %s", i + 1, len(companies), url)

            # Scrape main page
            result = scrape_url(url, args.timeout)

            company_data = {**company}
            if result["success"]:
                company_data["scraped_content"] = result["content"][:15000]
                company_data["scraped_metadata"] = result.get("metadata", {})
                company_data["scraped_links"] = result.get("links", [])[:50]
                company_data["scrape_status"] = "success"

                # Try subpages for more contact info
                time.sleep(0.5)
                subpage_result = scrape_subpages(url, args.timeout)
                if subpage_result["content"]:
                    company_data["subpage_content"] = subpage_result["content"][:10000]

                success_count += 1
            else:
                company_data["scraped_content"] = ""
                company_data["scrape_status"] = "failed"
                company_data["scrape_error"] = result.get("error", "Unknown error")
                failure_count += 1

            company_data["scraped_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            scraped.append(company_data)

            # Rate limiting
            if i < len(companies) - 1:
                time.sleep(args.delay)

        total = success_count + failure_count
        failure_rate = failure_count / total if total > 0 else 0
        if failure_rate > 0.8:
            logger.warning("High failure rate: %.0f%% of scrapes failed", failure_rate * 100)

        result = {
            "status": "success",
            "data": {
                "scraped": scraped,
                "success_count": success_count,
                "failure_count": failure_count,
            },
            "message": f"Scraped {success_count}/{total} companies successfully",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Scraped data written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
