#!/usr/bin/env python3
"""
Atomically increment invoice counter with file locking.

Manages sequential invoice numbering using a JSON state file with
file locking to prevent race conditions in concurrent executions.

Inputs:
    - counter_path: str -- Path to counter JSON file
    - action: str -- 'get_next' or 'get_current'

Outputs:
    - JSON with {'invoice_number': 'INV-1043', 'numeric': 1043} to stdout

Exit Codes:
    0: Success
    1: Lock timeout or other error
"""

import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime

try:
    from filelock import FileLock, Timeout
except ImportError:
    print("Error: filelock not installed. Run: pip install filelock", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


DEFAULT_COUNTER = {
    "last_invoice_number": 1000,
    "prefix": "INV-",
    "padding": 4
}


def main(counter_path: str, action: str = "get_next") -> dict:
    """Get next or current invoice number with atomic file locking."""
    counter_file = Path(counter_path)
    lock_path = Path(f"{counter_path}.lock")

    try:
        # Create parent directories if they don't exist
        counter_file.parent.mkdir(parents=True, exist_ok=True)

        # Acquire file lock with 5 second timeout
        with FileLock(lock_path, timeout=5):
            logger.info(f"Acquired lock on {counter_path}")

            # Read or initialize counter
            try:
                counter = json.loads(counter_file.read_text(encoding='utf-8'))
                logger.info(f"Loaded counter: {counter['last_invoice_number']}")
            except (FileNotFoundError, json.JSONDecodeError):
                logger.warning("Counter file missing or corrupted. Initializing to 1000.")
                counter = dict(DEFAULT_COUNTER)

            # Increment if get_next
            if action == "get_next":
                counter["last_invoice_number"] += 1
                counter_file.write_text(json.dumps(counter, indent=2), encoding='utf-8')
                logger.info(f"Incremented counter to {counter['last_invoice_number']}")

            # Format invoice number
            invoice_number = f"{counter['prefix']}{counter['last_invoice_number']:0{counter['padding']}d}"

            return {
                "invoice_number": invoice_number,
                "numeric": counter["last_invoice_number"]
            }

    except Timeout:
        logger.error("Failed to acquire lock after 5 seconds. Using timestamp fallback.")
        # Fallback: timestamp-based invoice number
        timestamp = int(datetime.utcnow().timestamp())
        fallback_number = f"INV-{timestamp}"
        logger.warning(f"Using fallback invoice number: {fallback_number}")
        return {
            "invoice_number": fallback_number,
            "numeric": timestamp
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage invoice counter")
    parser.add_argument(
        "counter_path",
        help="Path to counter JSON file"
    )
    parser.add_argument(
        "action",
        choices=["get_next", "get_current"],
        default="get_next",
        nargs="?",
        help="Action to perform (default: get_next)"
    )
    args = parser.parse_args()

    result = main(args.counter_path, args.action)
    print(json.dumps(result, indent=2))
