#!/usr/bin/env python3
"""
Uptime monitor tool: Check a URL and log the result to CSV.

This tool sends an HTTP GET request to a specified URL, measures response time,
determines up/down status based on HTTP status code, and appends the result to
a CSV log file. It is designed to run autonomously on a schedule via GitHub Actions.

Usage:
    python check_url.py --url https://example.com --timeout 10 --csv logs/uptime_log.csv

Exit Codes:
    0 - URL is up (status_code < 400)
    1 - URL is down (status_code >= 400, timeout, or connection error)

Author: WAT Systems Factory
Pattern: rest_client (simplified) + csv_read_write (append mode)
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import requests


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_url(url: str, timeout: int) -> Dict[str, Any]:
    """
    Execute HTTP GET request to the target URL and measure response time.
    
    Args:
        url: The URL to check (http:// or https://)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing:
            - timestamp: ISO 8601 timestamp with UTC timezone
            - status_code: HTTP status code (0 if timeout/error)
            - response_time_ms: Response time in milliseconds
            - is_up: Boolean indicating if the service is up
            - error: Error message if request failed (optional)
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        logger.info(f"Checking URL: {url}")
        start_time = time.monotonic()
        
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={'User-Agent': 'WAT-Uptime-Monitor/1.0'}
        )
        
        elapsed_ms = (time.monotonic() - start_time) * 1000
        status_code = response.status_code
        
        # Status codes < 400 are considered "up"
        is_up = status_code < 400
        
        logger.info(f"Response: {status_code} in {elapsed_ms:.2f}ms - {'UP' if is_up else 'DOWN'}")
        
        return {
            'timestamp': timestamp,
            'status_code': status_code,
            'response_time_ms': round(elapsed_ms, 2),
            'is_up': is_up,
        }
        
    except requests.exceptions.Timeout:
        # Timeout counts as down with response_time = timeout period
        elapsed_ms = timeout * 1000
        logger.warning(f"Request timed out after {timeout}s")
        return {
            'timestamp': timestamp,
            'status_code': 0,
            'response_time_ms': elapsed_ms,
            'is_up': False,
            'error': 'Timeout',
        }
        
    except requests.exceptions.ConnectionError as exc:
        # Connection errors (DNS failure, connection refused, etc.)
        logger.error(f"Connection error: {exc}")
        return {
            'timestamp': timestamp,
            'status_code': 0,
            'response_time_ms': 0,
            'is_up': False,
            'error': f'ConnectionError: {str(exc)[:100]}',
        }
        
    except requests.exceptions.RequestException as exc:
        # Catch-all for any other request errors
        logger.error(f"Request error: {exc}")
        return {
            'timestamp': timestamp,
            'status_code': 0,
            'response_time_ms': 0,
            'is_up': False,
            'error': f'RequestException: {str(exc)[:100]}',
        }


def append_to_csv(csv_path: Path, url: str, check_result: Dict[str, Any]) -> None:
    """
    Append the check result to the CSV log file.
    
    Creates the file with headers if it doesn't exist.
    Opens in append mode to add new records.
    
    Args:
        csv_path: Path to the CSV log file
        url: The URL that was checked
        check_result: Dictionary returned from check_url()
        
    Raises:
        OSError: If directory creation or file write fails
    """
    # Ensure the logs directory exists
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists to determine if we need to write headers
    file_exists = csv_path.exists()
    
    try:
        # Open in append mode with newline='' to prevent blank rows on Windows
        with csv_path.open('a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers only if this is a new file
            if not file_exists:
                writer.writerow(['timestamp', 'url', 'status_code', 'response_time_ms', 'is_up'])
                logger.info(f"Created new CSV log file: {csv_path}")
            
            # Write the data row
            writer.writerow([
                check_result['timestamp'],
                url,
                check_result['status_code'],
                check_result['response_time_ms'],
                check_result['is_up'],
            ])
            
        logger.info(f"Appended result to {csv_path}")
        
    except OSError as exc:
        logger.error(f"Failed to write to CSV file: {exc}")
        raise


def main() -> int:
    """
    Main entry point for the uptime checker.
    
    Parses command-line arguments, executes the URL check,
    appends the result to CSV, and returns an appropriate exit code.
    
    Returns:
        0 if URL is up, 1 if URL is down or an error occurred
    """
    parser = argparse.ArgumentParser(
        description='Check URL uptime and log results to CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a URL with default timeout
  python check_url.py --url https://example.com
  
  # Check with custom timeout and CSV path
  python check_url.py --url https://example.com --timeout 5 --csv logs/custom.csv
  
  # Use environment variables
  export MONITOR_URL="https://example.com"
  export TIMEOUT_SECONDS="10"
  python check_url.py

Exit codes:
  0 - URL is up (status code < 400)
  1 - URL is down (status code >= 400, timeout, or error)
        """
    )
    
    parser.add_argument(
        '--url',
        default=os.getenv('MONITOR_URL'),
        help='URL to monitor (or set MONITOR_URL environment variable)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=int(os.getenv('TIMEOUT_SECONDS', '10')),
        help='Request timeout in seconds (default: 10, or TIMEOUT_SECONDS env var)'
    )
    
    parser.add_argument(
        '--csv',
        default='logs/uptime_log.csv',
        help='Path to CSV log file (default: logs/uptime_log.csv)'
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.url:
        logger.error("URL is required. Provide --url argument or set MONITOR_URL environment variable.")
        return 1
    
    if not args.url.startswith(('http://', 'https://')):
        logger.error(f"Invalid URL format: {args.url}. Must start with http:// or https://")
        return 1
    
    # Execute the URL check
    try:
        check_result = check_url(args.url, args.timeout)
    except Exception as exc:
        logger.error(f"Unexpected error during URL check: {exc}")
        return 1
    
    # Append result to CSV
    try:
        csv_path = Path(args.csv)
        append_to_csv(csv_path, args.url, check_result)
    except Exception as exc:
        logger.error(f"Failed to log result to CSV: {exc}")
        return 1
    
    # Output JSON summary to stdout for logging/debugging
    output = {
        'timestamp': check_result['timestamp'],
        'url': args.url,
        'status_code': check_result['status_code'],
        'response_time_ms': check_result['response_time_ms'],
        'is_up': check_result['is_up'],
        'csv_updated': str(csv_path.resolve()),
    }
    
    if 'error' in check_result:
        output['error'] = check_result['error']
    
    print(json.dumps(output, indent=2))
    
    # Exit code: 0 if up, 1 if down
    # This allows GitHub Actions to show workflow as "failed" when site is down
    return 0 if check_result['is_up'] else 1


if __name__ == '__main__':
    sys.exit(main())
