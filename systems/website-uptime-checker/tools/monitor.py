"""
Website uptime monitor tool.

Performs HTTP GET requests to configured URLs and measures response times.
Returns structured JSON with check results for each URL.
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any

import requests


def check_url(url: str, timeout: int = 30) -> dict[str, Any]:
    """
    Check a single URL and return status information.
    
    Args:
        url: The URL to check (must include scheme)
        timeout: HTTP request timeout in seconds
    
    Returns:
        dict with:
        - timestamp: ISO 8601 timestamp
        - url: the URL checked
        - status_code: HTTP status code (0 if connection failed)
        - response_time_ms: response time in milliseconds (-1 if failed)
        - is_up: bool (true if status code 200-299)
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        start = time.monotonic()
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = (time.monotonic() - start) * 1000  # convert to ms
        
        return {
            "timestamp": timestamp,
            "url": url,
            "status_code": resp.status_code,
            "response_time_ms": round(elapsed, 2),
            "is_up": 200 <= resp.status_code < 300,
        }
    except requests.RequestException as exc:
        logging.error(f"Failed to check {url}: {exc}")
        return {
            "timestamp": timestamp,
            "url": url,
            "status_code": 0,
            "response_time_ms": -1,
            "is_up": False,
        }


def main():
    """Main entry point for the uptime monitor tool."""
    parser = argparse.ArgumentParser(description="Monitor website uptime")
    parser.add_argument("--urls", nargs="+", required=True, help="URLs to check")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout (seconds)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    results = []
    any_down = False
    
    for url in args.urls:
        logging.info(f"Checking {url}...")
        result = check_url(url, timeout=args.timeout)
        results.append(result)
        
        if not result["is_up"]:
            any_down = True
            logging.warning(f"{url} is DOWN (status: {result['status_code']})")
        else:
            logging.info(f"{url} is UP ({result['response_time_ms']}ms)")
    
    # Output results as JSON to stdout
    print(json.dumps(results, indent=2))
    
    # Exit code: 0 if all up, 1 if any down (for GitHub Actions UI)
    sys.exit(1 if any_down else 0)


if __name__ == "__main__":
    main()
