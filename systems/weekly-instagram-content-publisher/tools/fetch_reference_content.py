#!/usr/bin/env python3
"""
Fetch and extract content from reference URLs using Firecrawl with HTTP fallback.

Uses Firecrawl API (primary) or HTTP GET + BeautifulSoup (fallback) to extract
clean text content from reference URLs.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def fetch_with_firecrawl(url: str) -> Dict[str, Any]:
    """Fetch content using Firecrawl API."""
    try:
        from firecrawl import FirecrawlApp
        
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not set")
        
        app = FirecrawlApp(api_key=api_key)
        result = app.scrape_url(url, params={"formats": ["markdown"]})
        
        return {
            "url": url,
            "content": result.get("markdown", ""),
            "metadata": result.get("metadata", {}),
            "success": True,
            "method": "firecrawl"
        }
    except Exception as e:
        logging.warning(f"Firecrawl failed for {url}: {e}")
        raise


def fetch_with_http(url: str) -> Dict[str, Any]:
    """Fetch content using HTTP GET + BeautifulSoup."""
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract main content (heuristic: get all <p> tags)
        paragraphs = soup.find_all("p")
        content = "\n\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        
        # Get title
        title = soup.title.string if soup.title else ""
        
        return {
            "url": url,
            "content": content,
            "metadata": {"title": title},
            "success": True,
            "method": "http_fallback"
        }
    except Exception as e:
        logging.error(f"HTTP fallback failed for {url}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Fetch reference content from URLs"
    )
    parser.add_argument(
        "--reference-links",
        required=True,
        help="JSON array of reference link objects"
    )
    parser.add_argument(
        "--output",
        default="reference_content.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse reference links
        links = json.loads(args.reference_links)
        if not isinstance(links, list):
            raise ValueError("reference_links must be a JSON array")
        
        results = []
        
        for link in links:
            url = link.get("url") if isinstance(link, dict) else link
            if not url:
                continue
            
            logging.info(f"Fetching: {url}")
            
            # Try Firecrawl first
            try:
                result = fetch_with_firecrawl(url)
                results.append(result)
                logging.info(f"✓ Fetched via Firecrawl: {url}")
                continue
            except Exception:
                pass  # Fall through to HTTP fallback
            
            # Try HTTP fallback
            try:
                result = fetch_with_http(url)
                results.append(result)
                logging.info(f"✓ Fetched via HTTP: {url}")
                continue
            except Exception as e:
                # Both methods failed
                results.append({
                    "url": url,
                    "content": "",
                    "metadata": {},
                    "success": False,
                    "error": str(e),
                    "method": "none"
                })
                logging.error(f"✗ Failed to fetch: {url}")
        
        # Compile output
        output = {
            "reference_content": results,
            "total_urls": len(links),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"])
        }
        
        # Write output
        output_path = Path(args.output) if 'Path' in dir() else args.output
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logging.info(
            f"Reference content fetched: {output['successful']}/{output['total_urls']} successful"
        )
        print(json.dumps(output, indent=2))
        
        return 0
        
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    from pathlib import Path
    sys.exit(main())
