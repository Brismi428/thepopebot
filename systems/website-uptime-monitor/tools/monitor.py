#!/usr/bin/env python3
"""
Website Uptime Monitor Tool

Checks if a target URL is responding, measures response time, and logs results
to a CSV file. Exits with code 0 if the site is up, code 1 if the site is down.

Usage:
    python monitor.py --url https://example.com [--timeout 10]

Outputs:
    - Appends log entry to data/uptime_log.csv
    - Prints status to stdout
    - Exits 0 (up) or 1 (down)
"""

import argparse
import csv
import logging
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Tuple

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_url(url: str, timeout: int) -> Tuple[int, int, bool]:
    """
    Make HTTP GET request to URL and measure response time.
    
    Args:
        url: Target URL to check (must include protocol)
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (status_code, response_time_ms, is_up)
        - status_code: HTTP status code (0 if request failed)
        - response_time_ms: Response time in milliseconds
        - is_up: True if 200-399 status, False otherwise
    """
    try:
        start = time.perf_counter()
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={'User-Agent': 'WAT-Uptime-Monitor/1.0'}
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        status_code = response.status_code
        is_up = 200 <= status_code < 400
        
        logger.info(f"Check completed: {status_code} in {elapsed_ms}ms")
        return status_code, elapsed_ms, is_up
        
    except requests.exceptions.Timeout:
        logger.warning(f"Request timed out after {timeout}s")
        return 0, timeout * 1000, False
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection failed: {e}")
        return 0, timeout * 1000, False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return 0, timeout * 1000, False


def log_to_csv(csv_path: pathlib.Path, timestamp: str, url: str, 
               status_code: int, response_time_ms: int, is_up: bool) -> None:
    """
    Append check result to CSV file with retry logic.
    
    Args:
        csv_path: Path to CSV log file
        timestamp: ISO 8601 UTC timestamp
        url: Target URL that was checked
        status_code: HTTP status code (0 if failed)
        response_time_ms: Response time in milliseconds
        is_up: Boolean status
    """
    # Create directory if missing
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize CSV with headers if missing
    if not csv_path.exists():
        logger.info(f"Creating new CSV file: {csv_path}")
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "url", "status_code", "response_time_ms", "is_up"])
    
    # Append result with retry logic
    for attempt in range(3):
        try:
            with csv_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, url, status_code, response_time_ms, is_up])
            logger.info(f"Logged to CSV: {csv_path}")
            return
            
        except Exception as e:
            if attempt == 2:
                logger.error(f"CSV append failed after 3 attempts: {e}")
                raise
            logger.warning(f"CSV append attempt {attempt + 1} failed, retrying: {e}")
            time.sleep(1)


def main() -> int:
    """
    Main entry point for the uptime monitor tool.
    
    Returns:
        Exit code: 0 if site is up, 1 if site is down
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Check website uptime and log results to CSV"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL to monitor (must include http:// or https://)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default="data/uptime_log.csv",
        help="Path to CSV log file (default: data/uptime_log.csv)"
    )
    
    args = parser.parse_args()
    
    # Validate URL format
    if not args.url.startswith(("http://", "https://")):
        logger.error("URL must include protocol (http:// or https://)")
        return 1
    
    # Generate timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Check URL
    logger.info(f"Checking URL: {args.url}")
    status_code, response_time_ms, is_up = check_url(args.url, args.timeout)
    
    # Log to CSV
    try:
        csv_path = pathlib.Path(args.csv_path)
        log_to_csv(csv_path, timestamp, args.url, status_code, response_time_ms, is_up)
    except Exception as e:
        logger.error(f"Failed to log to CSV: {e}")
        # Print to stdout as fallback
        print(f"{timestamp},{args.url},{status_code},{response_time_ms},{is_up}")
        return 1
    
    # Print status summary
    status_text = "UP" if is_up else "DOWN"
    print(f"{timestamp} | {args.url} | {status_code} | {response_time_ms}ms | {status_text}")
    
    # Exit with appropriate code (0=up, 1=down)
    return 0 if is_up else 1


if __name__ == "__main__":
    sys.exit(main())
