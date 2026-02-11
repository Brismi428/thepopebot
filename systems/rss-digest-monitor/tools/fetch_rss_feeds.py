#!/usr/bin/env python
"""
Fetch RSS Feeds

Fetches and parses multiple RSS/Atom feeds using feedparser. Handles per-feed
errors gracefully so that one failed feed does not kill the entire run.

Usage:
    python fetch_rss_feeds.py config/feeds.json [timeout]

Inputs:
    - feeds_config_path: Path to JSON file with feed list
    - timeout: HTTP timeout per feed in seconds (default: 15)

Outputs:
    JSON object with feeds array, each containing entries or error status
"""

import json
import logging
import sys
from typing import Dict, Any, List
import feedparser
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(feeds_config_path: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Fetch and parse multiple RSS/Atom feeds.
    
    Args:
        feeds_config_path: Path to JSON config file with feed list
        timeout: HTTP timeout per feed in seconds
        
    Returns:
        Dictionary with feeds array containing entries or error status per feed
    """
    try:
        # Load feeds configuration
        logger.info(f"Loading feeds configuration from {feeds_config_path}")
        with open(feeds_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not isinstance(config, dict) or "feeds" not in config:
            raise ValueError("Config must contain 'feeds' key with array of feed objects")
        
        feeds_list = config["feeds"]
        if not isinstance(feeds_list, list):
            raise ValueError("'feeds' must be an array")
        
        logger.info(f"Found {len(feeds_list)} feeds to process")
        
        results = []
        
        # Process each feed independently
        for i, feed in enumerate(feeds_list, 1):
            feed_name = feed.get("name", f"Feed {i}")
            feed_url = feed.get("url")
            
            if not feed_url:
                logger.warning(f"Skipping {feed_name}: no URL provided")
                results.append({
                    "name": feed_name,
                    "url": "",
                    "entries": [],
                    "error": "No URL provided"
                })
                continue
            
            try:
                logger.info(f"Fetching {feed_name} ({feed_url})...")
                
                # Set User-Agent to avoid being blocked
                parsed = feedparser.parse(
                    feed_url,
                    request_headers={
                        "User-Agent": "RSS-Digest-Monitor/1.0 (feedparser)"
                    }
                )
                
                # Check for parsing errors
                if parsed.bozo:
                    logger.warning(
                        f"{feed_name} has malformed XML: {parsed.get('bozo_exception', 'Unknown error')}"
                    )
                    # Continue anyway - feedparser can often extract data despite errors
                
                # Extract entries
                entries = []
                for entry in parsed.entries:
                    # Extract fields with fallbacks
                    title = entry.get("title", "Untitled")
                    link = entry.get("link", "")
                    
                    # Summary can be in multiple fields
                    summary = entry.get("summary", entry.get("description", ""))
                    
                    # Truncate long summaries to 300 chars
                    if len(summary) > 300:
                        summary = summary[:297] + "..."
                    
                    # Published date with fallback to updated date
                    published = entry.get("published", entry.get("updated", ""))
                    
                    # GUID with fallback to link
                    guid = entry.get("id", entry.get("link", ""))
                    
                    entries.append({
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "published": published,
                        "guid": guid
                    })
                
                logger.info(f"✓ {feed_name}: fetched {len(entries)} entries")
                
                results.append({
                    "name": feed_name,
                    "url": feed_url,
                    "entries": entries,
                    "error": None
                })
                
            except Exception as e:
                logger.error(f"✗ Failed to fetch {feed_name}: {e}")
                results.append({
                    "name": feed_name,
                    "url": feed_url,
                    "entries": [],
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r["error"] is None)
        failed = len(results) - successful
        total_entries = sum(len(r["entries"]) for r in results)
        
        logger.info(f"✓ Fetch complete: {successful} successful, {failed} failed, {total_entries} total entries")
        
        return {"feeds": results}
        
    except Exception as e:
        logger.error(f"Fatal error processing feeds: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_rss_feeds.py <feeds_config_path> [timeout]")
        sys.exit(1)
    
    config_path = sys.argv[1]
    timeout_val = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    
    result = main(config_path, timeout_val)
    print(json.dumps(result, indent=2))
    sys.exit(0)
