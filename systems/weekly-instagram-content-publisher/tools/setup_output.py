#!/usr/bin/env python3
"""
Initialize output directory structure for Instagram content generation.

Creates dated output directory with subdirectories for various output types.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Setup output directory structure"
    )
    parser.add_argument(
        "--base-path",
        default="output/instagram",
        help="Base output path (default: output/instagram)"
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date for output directory (YYYY-MM-DD, default: today)"
    )
    
    args = parser.parse_args()
    
    try:
        # Determine output date
        if args.date:
            output_date = args.date
        else:
            output_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Create output directory
        base = Path(args.base_path)
        output_dir = base / output_date
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories if needed
        subdirs = ["logs", "temp"]
        for subdir in subdirs:
            (output_dir / subdir).mkdir(exist_ok=True)
        
        # Check if directory already exists (overwrite scenario)
        if any(output_dir.iterdir()):
            logging.warning(f"Output directory already exists: {output_dir}")
            logging.warning("Existing files may be overwritten")
        
        result = {
            "output_dir": str(output_dir.resolve()),
            "date": output_date,
            "exists": True
        }
        
        logging.info(f"Output directory initialized: {output_dir}")
        print(json.dumps(result, indent=2))
        return 0
        
    except Exception as e:
        logging.error(f"Failed to create output directory: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
