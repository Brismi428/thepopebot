#!/usr/bin/env python3
"""
Instagram Publish Result Writer

Writes publish results to output directories with timestamped filenames.

Success results go to: output/published/{timestamp}_{post_id}.json
Failure results go to: output/failed/{timestamp}_{hash}.json

Usage:
    python write_result.py \
        --result '{"status": "published", "post_id": "123", ...}' \
        --output-dir output/published

    python write_result.py --file result.json --output-dir output/failed

Returns:
    JSON: {"path": "...", "filename": "..."}
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_filename(result: dict[str, Any]) -> str:
    """
    Generate filename for result based on status.
    
    Success: {timestamp}_{post_id}.json
    Failure: {timestamp}_{hash}.json
    
    Args:
        result: Result dictionary
        
    Returns:
        Filename string
    """
    # Get timestamp (use result's timestamp if available, else now)
    timestamp_str = result.get("timestamp")
    if timestamp_str:
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)
    
    # Format timestamp as YYYYMMDD_HHMMSS
    timestamp_part = ts.strftime("%Y%m%d_%H%M%S")
    
    # Determine identifier based on status
    status = result.get("status", "unknown")
    
    if status in ("published", "success"):
        # Use post_id if available
        post_id = result.get("post_id", "unknown")
        identifier = str(post_id)
    else:
        # For failures, generate a hash from caption or image_url
        caption = result.get("caption", "")
        image_url = result.get("image_url", "")
        content = f"{caption}{image_url}"
        identifier = hashlib.md5(content.encode()).hexdigest()[:8]
    
    return f"{timestamp_part}_{identifier}.json"


def write_result(
    result: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    """
    Write result to output directory.
    
    Args:
        result: Result dictionary to write
        output_dir: Output directory path
        
    Returns:
        Dict with path and filename
    """
    try:
        output_path = Path(output_dir)
        
        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp if not present
        if "timestamp" not in result:
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Generate filename
        filename = generate_filename(result)
        file_path = output_path / filename
        
        # Write JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Wrote result to {file_path}")
        
        return {
            "path": str(file_path.resolve()),
            "filename": filename,
        }
        
    except OSError as e:
        logger.exception(f"File write error: {e}")
        # Don't raise - log the error but don't fail the workflow
        return {
            "path": "",
            "filename": "",
            "error": f"File write failed: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Unexpected error writing result: {e}")
        return {
            "path": "",
            "filename": "",
            "error": f"Unexpected error: {str(e)}",
        }


def main(
    result: dict[str, Any] | None = None,
    file_path: str | None = None,
    output_dir: str = "output",
) -> dict[str, str]:
    """
    Main entry point.
    
    Args:
        result: Result dictionary (if provided directly)
        file_path: Path to JSON file containing result
        output_dir: Output directory (default: "output")
        
    Returns:
        Write result dictionary
    """
    try:
        # Load result from file if provided
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                result = json.load(f)
        
        if not result:
            raise ValueError("No result provided (use --result or --file)")
        
        # Determine output directory based on status
        status = result.get("status", "unknown")
        
        if status in ("published", "success"):
            target_dir = Path(output_dir) / "published"
        else:
            target_dir = Path(output_dir) / "failed"
        
        return write_result(result, target_dir)
        
    except Exception as e:
        logger.exception(f"Write failed: {e}")
        return {
            "path": "",
            "filename": "",
            "error": str(e),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write Instagram publish result")
    parser.add_argument("--result", type=str, help="JSON result string")
    parser.add_argument("--file", type=str, help="Path to JSON file")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Base output directory (default: output)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    result_dict = None
    if args.result:
        result_dict = json.loads(args.result)
    
    write_result_data = main(
        result=result_dict,
        file_path=args.file,
        output_dir=args.output_dir,
    )
    
    if args.json:
        print(json.dumps(write_result_data, indent=2))
    else:
        if write_result_data.get("path"):
            print(f"✓ Result written to: {write_result_data['path']}")
        else:
            print(f"✗ Write failed: {write_result_data.get('error', 'unknown error')}", file=sys.stderr)
            sys.exit(1)
