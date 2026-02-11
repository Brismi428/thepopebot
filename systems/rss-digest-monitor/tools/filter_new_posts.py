#!/usr/bin/env python
"""
Filter New Posts

Compares fetched RSS entries against state to identify new posts since the last run.
Uses composite GUIDs (feed_url::guid) to prevent false deduplication.

Usage:
    python filter_new_posts.py feed_results.json state.json

Inputs:
    - feed_results_path: Path to JSON output from fetch_rss_feeds.py
    - state_path: Path to JSON state from load_state.py

Outputs:
    JSON object with new_posts array and new_guids array
"""

import json
import logging
import sys
from typing import Dict, Any, List
from datetime import datetime
from dateutil import parser as dateparser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(feed_results_path: str, state_path: str) -> Dict[str, Any]:
    """
    Filter fetched posts to identify new entries since last run.
    
    Args:
        feed_results_path: Path to feed results JSON from fetch_rss_feeds.py
        state_path: Path to state JSON from load_state.py
        
    Returns:
        Dictionary with new_posts array and new_guids array
    """
    try:
        # Load feed results
        logger.info(f"Loading feed results from {feed_results_path}")
        with open(feed_results_path, 'r', encoding='utf-8') as f:
            feed_results = json.load(f)
        
        # Load state
        logger.info(f"Loading state from {state_path}")
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        seen_guids = set(state.get("seen_guids", []))
        last_run_str = state.get("last_run")
        
        # Parse last_run timestamp if present
        last_run_dt = None
        if last_run_str:
            try:
                last_run_dt = dateparser.parse(last_run_str)
                logger.info(f"Filtering posts published after {last_run_str}")
            except Exception as e:
                logger.warning(f"Could not parse last_run timestamp: {e}")
        else:
            logger.info("No last_run timestamp - including all posts (first run)")
        
        new_posts = []
        new_guids = []
        
        # Process each feed
        for feed in feed_results.get("feeds", []):
            if feed.get("error"):
                logger.info(f"Skipping {feed['name']} - fetch failed: {feed['error']}")
                continue
            
            feed_name = feed["name"]
            feed_url = feed["url"]
            entries = feed.get("entries", [])
            
            logger.info(f"Processing {len(entries)} entries from {feed_name}")
            
            for entry in entries:
                # Create composite GUID: feed_url::entry_guid
                # This prevents false deduplication across feeds
                composite_guid = f"{feed_url}::{entry['guid']}"
                
                # Check if already seen
                if composite_guid in seen_guids:
                    continue
                
                # Check if published since last run
                if last_run_dt:
                    try:
                        published_dt = dateparser.parse(entry["published"])
                        
                        # Skip if published before last run
                        if published_dt < last_run_dt:
                            continue
                            
                    except Exception as e:
                        logger.warning(
                            f"Could not parse date '{entry['published']}' for '{entry['title']}': {e}"
                        )
                        logger.warning("Including post anyway (better to duplicate than miss)")
                
                # This is a new post!
                new_posts.append({
                    "feed_name": feed_name,
                    "title": entry["title"],
                    "link": entry["link"],
                    "summary": entry["summary"],
                    "published": entry["published"],
                    "guid": entry["guid"],
                    "feed_url": feed_url
                })
                new_guids.append(composite_guid)
        
        logger.info(f"✓ Found {len(new_posts)} new posts across all feeds")
        
        # Group by feed for logging
        by_feed: Dict[str, int] = {}
        for post in new_posts:
            by_feed[post["feed_name"]] = by_feed.get(post["feed_name"], 0) + 1
        
        for feed_name, count in by_feed.items():
            logger.info(f"  • {feed_name}: {count} new posts")
        
        return {
            "new_posts": new_posts,
            "new_guids": new_guids
        }
        
    except Exception as e:
        logger.error(f"Fatal error filtering posts: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python filter_new_posts.py <feed_results.json> <state.json>")
        sys.exit(1)
    
    feed_results_path = sys.argv[1]
    state_path = sys.argv[2]
    
    result = main(feed_results_path, state_path)
    print(json.dumps(result, indent=2))
    sys.exit(0)
