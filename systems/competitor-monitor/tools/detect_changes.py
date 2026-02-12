#!/usr/bin/env python3
"""
Change Detector

Compares current snapshot against previous snapshot to identify new blog posts,
pricing changes, and new features. Handles first-run initialization.

Inputs:
    --current: Path to current snapshot JSON
    --previous: Path to previous snapshot JSON (optional)

Outputs:
    JSON changes object to stdout with structure:
    {
        "competitor": "slug",
        "new_posts": [{title, url, published, excerpt}],
        "pricing_changes": [{plan, old_price, new_price, delta}],
        "new_features": [{title, description, url}],
        "summary": {new_posts_count, pricing_changes_count, new_features_count}
    }

Exit codes:
    0: Success (with or without changes)
    1: Fatal error
"""

import argparse
import json
import logging
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def normalize_price(price_str: str) -> Optional[float]:
    """
    Extract numeric price value from price string.
    
    Args:
        price_str: Price string (e.g., "$99/mo", "€1,234.56")
        
    Returns:
        Float value or None if not parseable
    """
    if not price_str:
        return None
    
    # Remove common formatting
    cleaned = re.sub(r"[^\d.,]", "", price_str)
    cleaned = cleaned.replace(",", "")
    
    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def detect_new_blog_posts(current_posts: List[Dict], previous_posts: List[Dict]) -> List[Dict]:
    """
    Identify blog posts in current that are not in previous.
    
    Args:
        current_posts: List of current blog post dicts
        previous_posts: List of previous blog post dicts
        
    Returns:
        List of new blog post dicts
    """
    # Build set of previous post URLs and titles
    prev_urls = {p.get("url") for p in previous_posts if p.get("url")}
    prev_titles = {p.get("title", "").lower() for p in previous_posts if p.get("title")}
    
    new_posts = []
    for post in current_posts:
        url = post.get("url", "")
        title = post.get("title", "").lower()
        
        # Post is new if URL is not in previous OR title is not in previous
        is_new_url = url and url not in prev_urls
        is_new_title = title and title not in prev_titles
        
        if is_new_url or (is_new_title and not url):
            new_posts.append(post)
    
    logger.info(f"Detected {len(new_posts)} new blog posts")
    return new_posts


def detect_pricing_changes(current_plans: List[Dict], previous_plans: List[Dict]) -> List[Dict]:
    """
    Identify pricing changes between current and previous plans.
    
    Args:
        current_plans: List of current pricing plan dicts
        previous_plans: List of previous pricing plan dicts
        
    Returns:
        List of pricing change dicts with old_price, new_price, delta
    """
    changes = []
    
    # Build map of previous plans by name
    prev_map = {p.get("name", "").lower(): p for p in previous_plans}
    
    for curr_plan in current_plans:
        plan_name = curr_plan.get("name", "")
        curr_price_str = curr_plan.get("price", "")
        curr_price = normalize_price(curr_price_str)
        
        # Find matching previous plan
        prev_plan = prev_map.get(plan_name.lower())
        
        if prev_plan:
            prev_price_str = prev_plan.get("price", "")
            prev_price = normalize_price(prev_price_str)
            
            # Compare prices
            if curr_price is not None and prev_price is not None:
                if abs(curr_price - prev_price) > 0.01:  # Allow for floating point variance
                    delta = curr_price - prev_price
                    delta_pct = (delta / prev_price * 100) if prev_price > 0 else 0
                    
                    changes.append({
                        "plan": plan_name,
                        "old_price": prev_price_str,
                        "new_price": curr_price_str,
                        "delta": f"{'+' if delta > 0 else ''}{delta:.2f}",
                        "delta_pct": f"{'+' if delta_pct > 0 else ''}{delta_pct:.1f}%"
                    })
            elif curr_price_str != prev_price_str:
                # Text changed but couldn't parse numbers - still flag it
                changes.append({
                    "plan": plan_name,
                    "old_price": prev_price_str,
                    "new_price": curr_price_str,
                    "delta": "unknown",
                    "delta_pct": "unknown"
                })
    
    logger.info(f"Detected {len(changes)} pricing changes")
    return changes


def detect_new_features(current_features: List[Dict], previous_features: List[Dict]) -> List[Dict]:
    """
    Identify features in current that are not in previous.
    
    Args:
        current_features: List of current feature dicts
        previous_features: List of previous feature dicts
        
    Returns:
        List of new feature dicts
    """
    # Build set of previous feature titles (case-insensitive)
    prev_titles = {f.get("title", "").lower() for f in previous_features if f.get("title")}
    
    new_features = []
    for feature in current_features:
        title = feature.get("title", "").lower()
        
        if title and title not in prev_titles:
            new_features.append(feature)
    
    logger.info(f"Detected {len(new_features)} new features")
    return new_features


def detect_changes(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main change detection function.
    
    Args:
        current: Current snapshot dict
        previous: Previous snapshot dict (or None if first run)
        
    Returns:
        Changes dict with all detected changes
    """
    competitor = current.get("competitor", "unknown")
    
    changes = {
        "competitor": competitor,
        "new_posts": [],
        "pricing_changes": [],
        "new_features": [],
        "summary": {
            "new_posts_count": 0,
            "pricing_changes_count": 0,
            "new_features_count": 0
        }
    }
    
    # If no previous snapshot, treat all content as "new"
    if previous is None:
        logger.info("No previous snapshot - treating all content as new (first run)")
        
        blog_data = current.get("pages", {}).get("blog", {}).get("data", [])
        pricing_data = current.get("pages", {}).get("pricing", {}).get("data", [])
        features_data = current.get("pages", {}).get("features", {}).get("data", [])
        
        changes["new_posts"] = blog_data
        changes["new_features"] = features_data
        changes["summary"]["new_posts_count"] = len(blog_data)
        changes["summary"]["new_features_count"] = len(features_data)
        
        # No pricing "changes" on first run, just note current pricing
        logger.info("First run: no pricing changes to report")
        
        return changes
    
    # Compare blog posts
    curr_blog = current.get("pages", {}).get("blog", {}).get("data", [])
    prev_blog = previous.get("pages", {}).get("blog", {}).get("data", [])
    changes["new_posts"] = detect_new_blog_posts(curr_blog, prev_blog)
    
    # Compare pricing
    curr_pricing = current.get("pages", {}).get("pricing", {}).get("data", [])
    prev_pricing = previous.get("pages", {}).get("pricing", {}).get("data", [])
    changes["pricing_changes"] = detect_pricing_changes(curr_pricing, prev_pricing)
    
    # Compare features
    curr_features = current.get("pages", {}).get("features", {}).get("data", [])
    prev_features = previous.get("pages", {}).get("features", {}).get("data", [])
    changes["new_features"] = detect_new_features(curr_features, prev_features)
    
    # Update summary
    changes["summary"]["new_posts_count"] = len(changes["new_posts"])
    changes["summary"]["pricing_changes_count"] = len(changes["pricing_changes"])
    changes["summary"]["new_features_count"] = len(changes["new_features"])
    
    return changes


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Detect changes between snapshots")
    parser.add_argument("--current", required=True, help="Path to current snapshot JSON")
    parser.add_argument("--previous", help="Path to previous snapshot JSON (optional)")
    args = parser.parse_args()
    
    try:
        # Load current snapshot
        current_path = Path(args.current)
        if not current_path.exists():
            logger.error(f"Current snapshot not found: {args.current}")
            return 1
        
        current = json.loads(current_path.read_text(encoding="utf-8"))
        
        # Load previous snapshot (if provided)
        previous = None
        if args.previous:
            previous_path = Path(args.previous)
            if previous_path.exists():
                previous = json.loads(previous_path.read_text(encoding="utf-8"))
                logger.info(f"Loaded previous snapshot: {args.previous}")
            else:
                logger.warning(f"Previous snapshot not found: {args.previous} (treating as first run)")
        else:
            logger.info("No previous snapshot provided (treating as first run)")
        
        # Detect changes
        logger.info("Starting change detection")
        changes = detect_changes(current, previous)
        
        # Output changes as JSON
        print(json.dumps(changes, indent=2, ensure_ascii=False))
        
        total_changes = (
            changes["summary"]["new_posts_count"] +
            changes["summary"]["pricing_changes_count"] +
            changes["summary"]["new_features_count"]
        )
        logger.info(f"Change detection complete: {total_changes} total changes detected")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
