#!/usr/bin/env python3
"""Create GitHub Issue for failed runs."""

import sys
import json
import argparse
import logging
import os
import httpx

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_issue(repo: str, title: str, body: str, labels: list = None) -> dict:
    """Create a GitHub Issue."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "title": title,
        "body": body,
        "labels": labels or ["site-intelligence-pack", "failed-run"]
    }
    
    resp = httpx.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json=payload,
        timeout=15
    )
    resp.raise_for_status()
    
    data = resp.json()
    
    logger.info(f"Created issue #{data['number']}: {data['html_url']}")
    
    return {
        "number": data["number"],
        "url": data["url"],
        "html_url": data["html_url"]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--body", required=True, help="Issue body")
    parser.add_argument("--labels", nargs="*", default=[], help="Issue labels")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    try:
        result = create_issue(args.repo, args.title, args.body, args.labels)
        
        output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
        else:
            print(output)
        
        return 0
    
    except Exception as e:
        logger.error(f"Failed to create issue: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
