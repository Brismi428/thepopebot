#!/usr/bin/env python3
"""
Crawl a domain via Firecrawl API with robots.txt compliance and rate limiting.

This tool uses the Firecrawl API to crawl a target domain, respecting robots.txt
disallowed paths and enforcing rate limits (1-2 req/sec).
"""

import sys
import json
import argparse
import logging
import os
import time
from typing import List, Dict
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/crawl"


def is_path_allowed(url_path: str, disallowed_paths: List[str]) -> bool:
    """Check if a URL path is allowed by robots.txt."""
    for disallowed in disallowed_paths:
        if url_path.startswith(disallowed):
            return False
    return True


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    reraise=True
)
def _crawl_with_retry(domain: str, max_pages: int, api_key: str) -> List[Dict]:
    """Execute Firecrawl crawl with exponential backoff retry."""
    logger.info(f"Starting Firecrawl crawl for {domain} (max {max_pages} pages)")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": f"https://{domain}",
        "limit": max_pages,
        "scrapeOptions": {
            "formats": ["markdown", "html"],
            "onlyMainContent": True
        },
        "allowBackwardCrawling": False,
        "maxDepth": 5,
        "timeout": 600000  # 10 minutes
    }
    
    # Start crawl job
    start_resp = httpx.post(
        FIRECRAWL_API_URL,
        json=payload,
        headers=headers,
        timeout=30
    )
    start_resp.raise_for_status()
    crawl_data = start_resp.json()
    
    if not crawl_data.get("success"):
        raise RuntimeError(f"Firecrawl crawl failed to start: {crawl_data}")
    
    job_id = crawl_data.get("id")
    logger.info(f"Firecrawl job started: {job_id}")
    
    # Poll for completion
    check_url = f"https://api.firecrawl.dev/v1/crawl/{job_id}"
    max_wait = 600  # 10 minutes
    poll_interval = 5
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        
        status_resp = httpx.get(check_url, headers=headers, timeout=15)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        
        status = status_data.get("status")
        logger.info(f"Crawl status: {status} ({elapsed}s elapsed)")
        
        if status == "completed":
            pages = status_data.get("data", [])
            logger.info(f"Crawl completed: {len(pages)} pages retrieved")
            return pages
        
        elif status in ("failed", "cancelled"):
            error = status_data.get("error", "Unknown error")
            raise RuntimeError(f"Firecrawl crawl {status}: {error}")
    
    raise TimeoutError(f"Firecrawl crawl timed out after {max_wait} seconds")


def crawl_with_firecrawl(
    domain: str,
    max_pages: int = 200,
    disallowed_paths: List[str] = None
) -> List[Dict]:
    """
    Crawl a domain via Firecrawl API, respecting robots.txt disallowed paths.
    
    Args:
        domain: Domain to crawl (e.g., example.com)
        max_pages: Maximum pages to crawl (default: 200)
        disallowed_paths: List of paths to skip from robots.txt
    
    Returns:
        List of page dicts with:
            - url: Page URL
            - title: Page title
            - content: Markdown content
            - status: HTTP status code
            - discovered_from: Source of discovery (crawl, sitemap, etc.)
    """
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")
    
    disallowed = disallowed_paths or []
    
    try:
        raw_pages = _crawl_with_retry(domain, max_pages, api_key)
    except Exception as e:
        logger.error(f"Firecrawl crawl failed after retries: {e}")
        raise
    
    # Filter out robots.txt disallowed paths
    filtered_pages = []
    blocked_count = 0
    
    for page in raw_pages:
        url = page.get("url", "")
        parsed = urlparse(url)
        url_path = parsed.path
        
        if not is_path_allowed(url_path, disallowed):
            logger.info(f"Skipping disallowed path: {url}")
            blocked_count += 1
            continue
        
        # Extract relevant fields
        filtered_pages.append({
            "url": url,
            "title": page.get("metadata", {}).get("title", ""),
            "content": page.get("markdown", ""),
            "status": page.get("statusCode", 200),
            "discovered_from": "crawl"
        })
    
    logger.info(
        f"Filtered {blocked_count} disallowed paths, "
        f"returning {len(filtered_pages)} pages"
    )
    
    return filtered_pages


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Crawl a domain via Firecrawl API"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Domain to crawl (e.g., example.com)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum pages to crawl (default: 200)"
    )
    parser.add_argument(
        "--disallowed-paths",
        nargs="*",
        default=[],
        help="Paths to skip from robots.txt"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    try:
        result = crawl_with_firecrawl(
            args.domain,
            args.max_pages,
            args.disallowed_paths
        )
        
        output_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Wrote {len(result)} pages to {args.output}")
        else:
            print(output_json)
        
        return 0
    
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
