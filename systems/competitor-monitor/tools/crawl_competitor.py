#!/usr/bin/env python3
"""
Competitor Web Scraper

Scrapes a single competitor's blog, pricing, and feature pages via Firecrawl API
with fallback to HTTP + BeautifulSoup. Returns structured JSON snapshot.

Inputs:
    --config: Path to competitor config JSON (name, slug, urls, selectors)

Outputs:
    JSON snapshot to stdout with structure:
    {
        "competitor": "slug",
        "timestamp": "ISO8601",
        "pages": {
            "blog": {"url": "...", "posts": [...]},
            "pricing": {"url": "...", "plans": [...]},
            "features": {"url": "...", "features": [...]}
        }
    }

Exit codes:
    0: Success (full or partial content extracted)
    1: Fatal error (no content extracted)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def firecrawl_scrape(url: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Scrape URL via Firecrawl API.
    
    Args:
        url: Target URL to scrape
        api_key: Firecrawl API key
        
    Returns:
        Dict with markdown content and metadata, or None if failed
    """
    try:
        logger.info(f"Attempting Firecrawl scrape: {url}")
        resp = httpx.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "formats": ["markdown", "html"]
            },
            timeout=30.0
        )
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("success"):
            logger.warning(f"Firecrawl returned success=false for {url}")
            return None
            
        logger.info(f"Firecrawl scrape successful: {url}")
        return {
            "markdown": data.get("data", {}).get("markdown", ""),
            "html": data.get("data", {}).get("html", ""),
            "metadata": data.get("data", {}).get("metadata", {})
        }
    except Exception as e:
        logger.warning(f"Firecrawl scrape failed for {url}: {e}")
        return None


def http_scrape(url: str) -> Optional[Dict[str, Any]]:
    """
    Fallback HTTP scrape with BeautifulSoup.
    
    Args:
        url: Target URL to scrape
        
    Returns:
        Dict with HTML content, or None if failed
    """
    try:
        logger.info(f"Attempting HTTP fallback scrape: {url}")
        resp = httpx.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CompetitorMonitor/1.0)"
            },
            timeout=30.0,
            follow_redirects=True
        )
        resp.raise_for_status()
        
        logger.info(f"HTTP scrape successful: {url}")
        return {
            "html": resp.text,
            "markdown": "",
            "metadata": {"status_code": resp.status_code}
        }
    except Exception as e:
        logger.error(f"HTTP scrape failed for {url}: {e}")
        return None


def extract_blog_posts(html: str, markdown: str, selector: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extract blog posts from HTML content.
    
    Args:
        html: Raw HTML content
        markdown: Markdown content (if available)
        selector: CSS selector for blog post elements
        base_url: Base URL for resolving relative links
        
    Returns:
        List of blog post dicts with title, url, published, excerpt
    """
    posts = []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Try selector-based extraction
        if selector:
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements matching selector: {selector}")
            
            for elem in elements[:20]:  # Limit to 20 posts
                # Extract title
                title_elem = (
                    elem.select_one("h1, h2, h3, h4") or
                    elem.select_one("a") or
                    elem
                )
                title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                
                # Extract URL
                link_elem = elem.select_one("a[href]")
                url = ""
                if link_elem:
                    href = link_elem.get("href", "")
                    url = urljoin(base_url, href)
                
                # Extract date (try common patterns)
                date_elem = elem.select_one("time, .date, .published, [class*='date']")
                published = ""
                if date_elem:
                    published = date_elem.get("datetime") or date_elem.get_text(strip=True)
                
                # Extract excerpt
                excerpt_elem = elem.select_one("p, .excerpt, .summary")
                excerpt = excerpt_elem.get_text(strip=True)[:200] if excerpt_elem else ""
                
                if title and (url or excerpt):  # Require at least title + (url or content)
                    posts.append({
                        "title": title,
                        "url": url,
                        "published": published,
                        "excerpt": excerpt
                    })
        
        # Fallback: extract all article links if selector failed
        if not posts:
            logger.info("Selector failed, falling back to link extraction")
            article_links = soup.select("article a[href], .post a[href], [class*='blog'] a[href]")
            
            for link in article_links[:20]:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                url = urljoin(base_url, href)
                
                if title and url and len(title) > 10:  # Filter out short/navigation links
                    posts.append({
                        "title": title,
                        "url": url,
                        "published": "",
                        "excerpt": ""
                    })
        
    except Exception as e:
        logger.error(f"Blog post extraction failed: {e}")
    
    logger.info(f"Extracted {len(posts)} blog posts")
    return posts


def extract_pricing(html: str, markdown: str, selector: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extract pricing plans from HTML content.
    
    Args:
        html: Raw HTML content
        markdown: Markdown content (if available)
        selector: CSS selector for pricing elements
        base_url: Base URL for context
        
    Returns:
        List of pricing plan dicts with name, price, features
    """
    plans = []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Try selector-based extraction
        if selector:
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} pricing elements matching selector: {selector}")
            
            for elem in elements:
                # Extract plan name
                name_elem = elem.select_one("h1, h2, h3, h4, .plan-name, [class*='title']")
                name = name_elem.get_text(strip=True) if name_elem else "Unnamed Plan"
                
                # Extract price
                price_elem = elem.select_one(
                    ".price, [class*='price'], [class*='amount'], strong, b"
                )
                price = price_elem.get_text(strip=True) if price_elem else ""
                
                # Extract features
                feature_elems = elem.select("li, .feature, [class*='feature']")
                features = [f.get_text(strip=True) for f in feature_elems if f.get_text(strip=True)]
                
                plans.append({
                    "name": name,
                    "price": price,
                    "features": features[:10]  # Limit features
                })
        
        # Fallback: look for common pricing patterns
        if not plans:
            logger.info("Selector failed, falling back to pattern matching")
            # Look for elements with price-like text
            price_texts = soup.find_all(string=lambda t: t and ("$" in t or "€" in t or "£" in t))
            
            for price_text in price_texts[:5]:  # Limit to 5 potential plans
                parent = price_text.parent
                if parent:
                    name_elem = parent.find_previous(["h1", "h2", "h3", "h4"])
                    name = name_elem.get_text(strip=True) if name_elem else "Plan"
                    
                    plans.append({
                        "name": name,
                        "price": price_text.strip(),
                        "features": []
                    })
        
    except Exception as e:
        logger.error(f"Pricing extraction failed: {e}")
    
    logger.info(f"Extracted {len(plans)} pricing plans")
    return plans


def extract_features(html: str, markdown: str, selector: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extract feature items from HTML content.
    
    Args:
        html: Raw HTML content
        markdown: Markdown content (if available)
        selector: CSS selector for feature elements
        base_url: Base URL for resolving relative links
        
    Returns:
        List of feature dicts with title, description, url
    """
    features = []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Try selector-based extraction
        if selector:
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} feature elements matching selector: {selector}")
            
            for elem in elements[:30]:  # Limit to 30 features
                # Extract title
                title_elem = elem.select_one("h1, h2, h3, h4, strong, b, .title")
                title = title_elem.get_text(strip=True) if title_elem else "Untitled Feature"
                
                # Extract description
                desc_elem = elem.select_one("p, .description, [class*='desc']")
                description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                
                # Extract URL if present
                link_elem = elem.select_one("a[href]")
                url = ""
                if link_elem:
                    href = link_elem.get("href", "")
                    url = urljoin(base_url, href)
                
                features.append({
                    "title": title,
                    "description": description,
                    "url": url
                })
        
        # Fallback: extract section headings as features
        if not features:
            logger.info("Selector failed, falling back to heading extraction")
            headings = soup.select("h2, h3")
            
            for heading in headings[:30]:
                title = heading.get_text(strip=True)
                next_p = heading.find_next("p")
                description = next_p.get_text(strip=True)[:200] if next_p else ""
                
                features.append({
                    "title": title,
                    "description": description,
                    "url": ""
                })
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
    
    logger.info(f"Extracted {len(features)} features")
    return features


def crawl_competitor(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main crawl function for a single competitor.
    
    Args:
        config: Competitor configuration dict
        
    Returns:
        Snapshot dict with all extracted content
    """
    snapshot = {
        "competitor": config["slug"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "pages": {}
    }
    
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    
    # Define extraction functions by page type
    extractors = {
        "blog": extract_blog_posts,
        "pricing": extract_pricing,
        "features": extract_features
    }
    
    # Crawl each page type
    for page_type, url in config.get("urls", {}).items():
        logger.info(f"Crawling {page_type} page: {url}")
        
        # Try Firecrawl first
        content = None
        if api_key:
            content = firecrawl_scrape(url, api_key)
            time.sleep(2)  # Rate limit protection
        
        # Fallback to HTTP if Firecrawl failed
        if not content:
            content = http_scrape(url)
        
        # Skip this page if all methods failed
        if not content:
            logger.error(f"All scraping methods failed for {page_type}: {url}")
            snapshot["pages"][page_type] = {
                "url": url,
                "error": "scraping_failed",
                "data": []
            }
            continue
        
        # Extract structured data
        html = content.get("html", "")
        markdown = content.get("markdown", "")
        selector = config.get("selectors", {}).get(f"{page_type}_items", "")
        
        extractor = extractors.get(page_type)
        if extractor:
            data = extractor(html, markdown, selector, url)
        else:
            logger.warning(f"No extractor defined for page type: {page_type}")
            data = []
        
        snapshot["pages"][page_type] = {
            "url": url,
            "data": data,
            "scraped_at": datetime.utcnow().isoformat() + "Z"
        }
    
    return snapshot


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Crawl competitor website")
    parser.add_argument("--config", required=True, help="Path to competitor config JSON")
    args = parser.parse_args()
    
    try:
        # Load competitor config
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config file not found: {args.config}")
            return 1
        
        config = json.loads(config_path.read_text(encoding="utf-8"))
        
        # Validate config
        required_fields = ["name", "slug", "urls"]
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required config field: {field}")
                return 1
        
        # Crawl competitor
        logger.info(f"Starting crawl for competitor: {config['name']}")
        snapshot = crawl_competitor(config)
        
        # Output snapshot as JSON
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        
        logger.info(f"Crawl complete for {config['name']}")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
