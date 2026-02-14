#!/usr/bin/env python3
"""
Prune old content pack archives (keep last 12 weeks).
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Clean up old archives")
    parser.add_argument("--archive-dir", default="output/instagram")
    parser.add_argument("--retention-weeks", type=int, default=12)
    
    args = parser.parse_args()
    
    try:
        archive_dir = Path(args.archive_dir)
        if not archive_dir.exists():
            logging.info("Archive directory does not exist, nothing to clean")
            return 0
        
        cutoff = datetime.utcnow() - timedelta(weeks=args.retention_weeks)
        deleted = []
        
        for item in archive_dir.iterdir():
            if not item.is_dir():
                continue
            
            # Check if directory name is a date (YYYY-MM-DD)
            try:
                dir_date = datetime.strptime(item.name, "%Y-%m-%d")
                if dir_date < cutoff:
                    logging.info(f"Deleting old archive: {item.name}")
                    import shutil
                    shutil.rmtree(item)
                    deleted.append(item.name)
            except ValueError:
                # Not a date directory, skip
                continue
        
        logging.info(f"Cleanup complete: {len(deleted)} directories deleted")
        print(json.dumps({"deleted": deleted, "count": len(deleted)}, indent=2))
        return 0
        
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
