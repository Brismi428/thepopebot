#!/usr/bin/env python3
"""
Update latest.md with links to current content pack.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Update latest index")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--weekly-theme", required=True)
    parser.add_argument("--review-score", type=float, required=True)
    parser.add_argument("--publish-status", required=True)
    
    args = parser.parse_args()
    
    try:
        output_dir = Path(args.output_dir)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        latest = f"""# Latest Instagram Content Pack

**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
**Theme:** {args.weekly_theme}
**Quality Score:** {args.review_score}/100
**Status:** {args.publish_status}

## Files

- [Content Pack (Markdown)](./{date_str}/content_pack_{date_str}.md)
- [Content Pack (JSON)](./{date_str}/content_pack_{date_str}.json)
- [Review Report](./{date_str}/review_report.json)
- [Upload Checklist](./{date_str}/upload_checklist_{date_str}.md)

## Quick Stats

- **Date:** {date_str}
- **Theme:** {args.weekly_theme}
- **Score:** {args.review_score}/100
- **Status:** {args.publish_status}
"""
        
        latest_path = output_dir.parent / "latest.md"
        latest_path.write_text(latest)
        
        logging.info(f"Latest index updated: {latest_path}")
        print(json.dumps({"path": str(latest_path)}, indent=2))
        return 0
        
    except Exception as e:
        logging.error(f"Failed to update latest index: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
