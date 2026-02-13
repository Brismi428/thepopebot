"""
CSV logging tool for uptime check results.

Appends check results to a CSV file, creating it with headers if it doesn't exist.
"""
import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

FIELDNAMES = ["timestamp", "url", "status_code", "response_time_ms", "is_up"]


def append_results(log_file: Path, results: list[dict[str, Any]]) -> None:
    """
    Append check results to CSV file.
    
    Args:
        log_file: Path to CSV log file
        results: List of check result dictionaries
    
    Raises:
        IOError: If file write fails
    """
    # Create parent directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and has content
    file_exists = log_file.exists() and log_file.stat().st_size > 0
    
    # Open in append mode, write header if new file
    with log_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        
        if not file_exists:
            writer.writeheader()
            logging.info(f"Created new log file: {log_file}")
        
        for result in results:
            writer.writerow(result)
        
        logging.info(f"Appended {len(results)} rows to {log_file}")


def main():
    """Main entry point for the CSV logging tool."""
    parser = argparse.ArgumentParser(description="Log uptime check results to CSV")
    parser.add_argument("--results", required=True, help="JSON file or string with check results")
    parser.add_argument("--log-file", default="logs/uptime_log.csv", help="CSV log file path")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Parse results (from file or JSON string)
    try:
        results_path = Path(args.results)
        if results_path.exists():
            results = json.loads(results_path.read_text())
        else:
            results = json.loads(args.results)
    except Exception as exc:
        logging.error(f"Failed to parse results: {exc}")
        sys.exit(1)
    
    # Append to log file
    try:
        log_path = Path(args.log_file)
        append_results(log_path, results)
    except Exception as exc:
        logging.error(f"Failed to write log file: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
