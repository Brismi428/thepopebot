#!/usr/bin/env python3
"""
Fallback HTTP crawler using direct requests (no JS rendering).

This tool provides a simple HTTP-based crawler as a fallback when Firecrawl
is unavailable. It will not handle JavaScript-rendered content but provides
basic crawling functionality.
"""

import sys
import json
import argparse
import logging
import time
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_path_allowed(url_path: str, disallowed_paths: List[str]) -> bool:
    """Check if a URL path is allowed by robots.txt."""
    for disallowed in disallowed_paths:
        if url_path.startswith(disallowed):
            return False
    return True


def extract_links(html: str, base_url: str) -> List[str]:
    """Extract absolute URLs from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_url = urljoin(base_url, href)
        links.append(absolute_url)
    
    return links


def crawl_http_fallback(
    domain: str,
    max_pages: int = 200,
    disallowed_paths: List[str] = None
) -> List[Dict]:
    """
    Crawl a domain using direct HTTP requests (no JS rendering).
    
    Args:
        domain: Domain to crawl
        max_pages: Maximum pages to crawl
        disallowed_paths: List of paths to skip from robots.txt
    
    Returns:
        List of page dicts with url, title, content, status, discovered_from
    """
    disallowed = disallowed_paths or []
    base_url = f"https://{domain}"
    
    to_visit = [base_url]
    visited: Set[str] = set()
    pages = []
    
    # Rate limiting: 1 request per second
    rate_limit_delay = 1.0
    
    # Try some common important paths explicitly
    common_paths = [
        "/pricing", "/faq", "/about", "/contact",
        "/privacy", "/terms", "/careers", "/blog"
    ]
    
    for path in common_paths:
        to_visit.append(f"{base_url}{path}")
    
    logger.info(f"Starting HTTP fallback crawl for {domain}")
    
    while to_visit and len(pages) < max_pages:
        url = to_visit.pop(0)
        
        # Skip if already visited
        if url in visited:
            continue
        
        # Check robots.txt compliance
        parsed = urlparse(url)
        if not is_path_allowed(parsed.path, disallowed):
            logger.debug(f"Skipping disallowed: {url}")
            visited.add(url)
            continue
        
        # Skip non-HTTP(S) URLs
        if parsed.scheme not in ("http", "https"):
            visited.add(url)
            continue
        
        # Skip different domains
        if parsed.netloc != domain and not parsed.netloc.endswith(f".{domain}"):
            visited.add(url)
            continue
        
        visited.add(url)
        
        try:
            # Rate limiting
            time.sleep(rate_limit_delay)
            
            logger.info(f"Fetching ({len(pages)+1}/{max_pages}): {url}")
            
            resp = httpx.get(
                url,
                follow_redirects=True,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SiteIntelligencePack/1.0)"}
            )
            
            # Skip non-200 responses
            if resp.status_code != 200:
                logger.warning(f"Skipping {url} (status {resp.status_code})")
                continue
            
            # Skip non-HTML content
            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type.lower():
                logger.debug(f"Skipping non-HTML: {url}")
                continue
            
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.string if title_tag else ""
            
            # Extract text content (simplified markdown)
            for script_or_style in soup(['script', 'style']):
                script_or_style.extract()
            
            text_content = soup.get_text(separator='\n', strip=True)
            
            pages.append({
                "url": url,
                "title": title,
                "content": text_content[:10000],  # Limit content size
                "status": resp.status_code,
                "discovered_from": "http_crawl"
            })
            
            # Extract and queue new links (only if we have room)
            if len(pages) < max_pages:
                new_links = extract_links(html, url)
                for link in new_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
        
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            continue
    
    logger.info(f"HTTP fallback crawl completed: {len(pages)} pages")
    
    return pages


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Crawl a domain using HTTP fallback (no JS rendering)"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Domain to crawl"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum pages to crawl"
    )
    parser.add_argument(
        "--disallowed-paths",
        nargs="*",
        default=[],
        help="Paths to skip from robots.txt"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    try:
        result = crawl_http_fallback(
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
        
        if len(result) < 5:
            logger.warning(f"Only {len(result)} pages crawled (threshold: 5)")
            return 1
        
        return 0
    
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
