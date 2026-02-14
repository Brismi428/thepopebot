#!/usr/bin/env python3
"""
Fetch and parse robots.txt for a domain.

This tool fetches robots.txt from a target domain, parses User-agent: * rules,
and returns a structured summary of allowed/disallowed paths.
"""

import sys
import json
import argparse
import logging
from typing import Dict, List
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_robots(domain: str) -> Dict[str, any]:
    """
    Fetch and parse robots.txt for a domain.
    
    Args:
        domain: Domain to fetch robots.txt from (e.g., example.com)
    
    Returns:
        Dict with:
            - fetched_url: Full robots.txt URL
            - allowed_summary: Human-readable allowed paths summary
            - disallowed_summary: Human-readable disallowed paths summary
            - disallowed_paths: List of disallowed path strings
            - raw_excerpt: First 500 chars of robots.txt content
    """
    url = f"https://{domain}/robots.txt"
    
    try:
        logger.info(f"Fetching robots.txt from {url}")
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        
        # Handle 404 gracefully -- many sites don't have robots.txt
        if resp.status_code == 404:
            logger.info(f"robots.txt not found at {url} (404)")
            return {
                "fetched_url": url,
                "allowed_summary": "All paths allowed (no robots.txt)",
                "disallowed_summary": "None",
                "disallowed_paths": [],
                "raw_excerpt": ""
            }
        
        resp.raise_for_status()
        raw_text = resp.text
        
        # Parse User-agent: * rules
        disallowed: List[str] = []
        in_user_agent_all = False
        
        for line in raw_text.splitlines():
            line_stripped = line.strip()
            
            # Check for User-agent: * section
            if line_stripped.lower().startswith("user-agent:"):
                agent = line_stripped.split(":", 1)[1].strip()
                in_user_agent_all = (agent == "*")
            
            # Extract Disallow rules for User-agent: *
            if in_user_agent_all and line_stripped.lower().startswith("disallow:"):
                path = line_stripped.split(":", 1)[1].strip()
                if path:
                    disallowed.append(path)
        
        logger.info(f"Found {len(disallowed)} disallowed paths")
        
        return {
            "fetched_url": url,
            "allowed_summary": "All paths allowed" if not disallowed else "Restricted paths found",
            "disallowed_summary": ", ".join(disallowed) if disallowed else "None",
            "disallowed_paths": disallowed,
            "raw_excerpt": raw_text[:500]
        }
    
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch robots.txt: {e}")
        return {
            "fetched_url": url,
            "allowed_summary": "All paths allowed (fetch failed)",
            "disallowed_summary": "Unknown",
            "disallowed_paths": [],
            "raw_excerpt": f"Error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching robots.txt: {e}", exc_info=True)
        return {
            "fetched_url": url,
            "allowed_summary": "All paths allowed (error)",
            "disallowed_summary": "Unknown",
            "disallowed_paths": [],
            "raw_excerpt": f"Error: {str(e)}"
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and parse robots.txt for a domain"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Domain to fetch robots.txt from (e.g., example.com)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    result = fetch_robots(args.domain)
    
    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        logger.info(f"Wrote output to {args.output}")
    else:
        print(output_json)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
