#!/usr/bin/env python3
"""
Load company branding and tax configuration with sensible defaults.

Reads configuration from JSON file, providing default values for any
missing fields to ensure the system works even without a complete config.

Inputs:
    - config_path: str -- Path to config JSON file

Outputs:
    - JSON dict with config (uses defaults for missing fields) to stdout

Exit Codes:
    0: Always succeeds (uses defaults on error)
"""

import sys
import json
import logging
from pathlib import Path


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "company_name": "Your Company LLC",
    "company_address": "456 Vendor Ave, Austin, TX 78701",
    "company_email": "hello@yourcompany.com",
    "company_phone": "+1 (512) 555-0100",
    "company_logo_path": None,
    "tax_rate": 0.0,
    "tax_label": "Tax",
    "currency": "USD",
    "currency_symbol": "$"
}


def main(config_path: str) -> dict:
    """Load configuration from JSON file with default fallbacks."""
    config = dict(DEFAULT_CONFIG)

    try:
        logger.info(f"Loading config from {config_path}")
        loaded = json.loads(Path(config_path).read_text(encoding='utf-8'))
        config.update(loaded)
        logger.info("✓ Config loaded successfully")

    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
    except json.JSONDecodeError as e:
        logger.warning(f"Config file is invalid JSON: {e}. Using defaults.")
    except Exception as e:
        logger.warning(f"Error loading config: {e}. Using defaults.")

    return config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load invoice configuration")
    parser.add_argument(
        "config_path",
        help="Path to config JSON file"
    )
    args = parser.parse_args()

    result = main(args.config_path)
    print(json.dumps(result, indent=2))
