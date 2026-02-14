#!/usr/bin/env python3
"""
Build inventory of crawled pages with URL normalization, canonical detection,
content hashing, and duplicate clustering.
"""

import sys
import json
import argparse
import logging
import hashlib
from typing import List, Dict
from urllib.parse import urlparse, urlunparse
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize a URL: lowercase domain, remove fragment, strip trailing slash."""
    parsed = urlparse(url)
    
    # Lowercase domain
    netloc = parsed.netloc.lower()
    
    # Remove fragment
    fragment = ""
    
    # Strip trailing slash from path
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    
    # Rebuild URL
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        parsed.query,
        fragment
    ))
    
    return normalized


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"


def build_inventory(raw_pages: List[Dict]) -> List[Dict]:
    """
    Build normalized inventory with canonical URLs, content hashing, and deduplication.
    
    Args:
        raw_pages: List of page dicts from crawler
    
    Returns:
        List of inventory dicts with:
            - url: Original URL
            - canonical_url: Normalized canonical URL
            - title: Page title
            - discovered_from: Source (crawl, sitemap, etc.)
            - http_status: HTTP status code
            - content_hash: SHA256 hash of content
            - dedup_cluster_id: Cluster ID for duplicates
            - notes: Any warnings or issues
    """
    inventory = []
    hash_to_cluster: Dict[str, str] = {}
    cluster_counter = 1
    
    logger.info(f"Building inventory from {len(raw_pages)} pages")
    
    for page in raw_pages:
        url = page.get("url", "")
        content = page.get("content", "")
        
        # Normalize URL
        canonical_url = normalize_url(url)
        
        # Compute content hash
        content_hash = compute_content_hash(content)
        
        # Assign or create cluster ID
        if content_hash in hash_to_cluster:
            cluster_id = hash_to_cluster[content_hash]
            notes = f"Duplicate content (cluster: {cluster_id})"
        else:
            cluster_id = f"cluster_{cluster_counter:03d}"
            hash_to_cluster[content_hash] = cluster_id
            cluster_counter += 1
            notes = None
        
        inventory.append({
            "url": url,
            "canonical_url": canonical_url,
            "title": page.get("title", ""),
            "discovered_from": page.get("discovered_from", "unknown"),
            "http_status": page.get("status", 200),
            "content_hash": content_hash,
            "dedup_cluster_id": cluster_id,
            "notes": notes
        })
    
    # Log deduplication stats
    unique_clusters = len(set(item["dedup_cluster_id"] for item in inventory))
    duplicates = len(inventory) - unique_clusters
    
    logger.info(
        f"Inventory built: {len(inventory)} pages, "
        f"{unique_clusters} unique clusters, "
        f"{duplicates} duplicates"
    )
    
    return inventory


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build inventory from raw crawled pages"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON file with raw pages"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            raw_pages = json.load(f)
        
        result = build_inventory(raw_pages)
        
        output_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Wrote inventory to {args.output}")
        else:
            print(output_json)
        
        return 0
    
    except Exception as e:
        logger.error(f"Failed to build inventory: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
