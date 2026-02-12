#!/usr/bin/env python3
"""
Snapshot Storage Manager

Saves current snapshot to state/snapshots/{slug}/ directory with atomic writes.
Updates latest.json symlink/copy and handles pruning of old snapshots.

Inputs:
    --snapshot: Path to snapshot JSON file
    --slug: Competitor slug (directory name)
    --date: Date in YYYY-MM-DD format

Outputs:
    JSON to stdout with saved file paths and success status

Exit codes:
    0: Success (snapshot saved)
    1: Fatal error (snapshot not saved)
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Maximum number of snapshots to keep (52 weeks = 1 year)
MAX_SNAPSHOTS = 52


def atomic_write(path: Path, content: str) -> None:
    """
    Write file atomically using temp file + rename.
    
    Args:
        path: Target file path
        content: Content to write
    """
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.rename(path)
    logger.debug(f"Atomic write complete: {path}")


def prune_old_snapshots(snapshot_dir: Path, max_keep: int = MAX_SNAPSHOTS) -> int:
    """
    Remove old snapshot files, keeping only the most recent N.
    
    Args:
        snapshot_dir: Directory containing snapshot files
        max_keep: Maximum number of snapshots to keep
        
    Returns:
        Number of snapshots pruned
    """
    # Find all dated snapshot files (YYYY-MM-DD.json)
    snapshot_files = sorted(
        [f for f in snapshot_dir.glob("????-??-??.json")],
        key=lambda f: f.name,
        reverse=True
    )
    
    if len(snapshot_files) <= max_keep:
        logger.info(f"No pruning needed: {len(snapshot_files)} snapshots (limit: {max_keep})")
        return 0
    
    # Delete oldest snapshots
    to_delete = snapshot_files[max_keep:]
    for old_file in to_delete:
        old_file.unlink()
        logger.info(f"Pruned old snapshot: {old_file.name}")
    
    logger.info(f"Pruned {len(to_delete)} old snapshots")
    return len(to_delete)


def validate_snapshot(snapshot: Dict[str, Any]) -> bool:
    """
    Validate snapshot structure before saving.
    
    Args:
        snapshot: Snapshot dict to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["competitor", "timestamp", "pages"]
    for field in required_fields:
        if field not in snapshot:
            logger.error(f"Missing required field in snapshot: {field}")
            return False
    
    if not isinstance(snapshot["pages"], dict):
        logger.error("Snapshot 'pages' field must be a dict")
        return False
    
    logger.debug("Snapshot validation passed")
    return True


def check_snapshot_size(snapshot_json: str, max_size_mb: float = 10.0) -> bool:
    """
    Check if snapshot size is within limits.
    
    Args:
        snapshot_json: JSON string of snapshot
        max_size_mb: Maximum size in MB
        
    Returns:
        True if within limits, False if too large
    """
    size_bytes = len(snapshot_json.encode("utf-8"))
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_size_mb:
        logger.warning(f"Snapshot size ({size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)")
        return False
    
    logger.debug(f"Snapshot size: {size_mb:.2f} MB (within limit)")
    return True


def compress_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compress snapshot by dropping excerpts and limiting data.
    
    Args:
        snapshot: Original snapshot dict
        
    Returns:
        Compressed snapshot dict
    """
    logger.info("Compressing snapshot (dropping excerpts, limiting features)")
    compressed = dict(snapshot)
    
    for page_type, page_data in compressed.get("pages", {}).items():
        data = page_data.get("data", [])
        
        if page_type == "blog" and isinstance(data, list):
            # Drop excerpts from blog posts
            for post in data:
                if "excerpt" in post:
                    post["excerpt"] = ""
        
        elif page_type == "features" and isinstance(data, list):
            # Limit features to first 20
            page_data["data"] = data[:20]
            # Drop descriptions
            for feature in page_data["data"]:
                if "description" in feature:
                    feature["description"] = ""
    
    return compressed


def save_snapshot(snapshot: Dict[str, Any], slug: str, date: str) -> Dict[str, Any]:
    """
    Main save function - stores snapshot with all safety checks.
    
    Args:
        snapshot: Snapshot dict to save
        slug: Competitor slug
        date: Date in YYYY-MM-DD format
        
    Returns:
        Result dict with paths and status
    """
    # Validate snapshot
    if not validate_snapshot(snapshot):
        raise ValueError("Snapshot validation failed")
    
    # Create output directory
    output_dir = Path("state/snapshots") / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Prepare snapshot JSON
    snapshot_json = json.dumps(snapshot, indent=2, ensure_ascii=False)
    
    # Check size and compress if needed
    if not check_snapshot_size(snapshot_json):
        logger.warning("Snapshot too large, attempting compression")
        compressed = compress_snapshot(snapshot)
        snapshot_json = json.dumps(compressed, indent=2, ensure_ascii=False)
        
        if not check_snapshot_size(snapshot_json):
            raise ValueError("Snapshot still too large after compression")
        
        logger.info("Snapshot compressed successfully")
    
    # Save dated snapshot
    dated_path = output_dir / f"{date}.json"
    atomic_write(dated_path, snapshot_json)
    logger.info(f"Saved dated snapshot: {dated_path}")
    
    # Update latest.json
    latest_path = output_dir / "latest.json"
    atomic_write(latest_path, snapshot_json)
    logger.info(f"Updated latest snapshot: {latest_path}")
    
    # Prune old snapshots
    pruned_count = prune_old_snapshots(output_dir)
    
    return {
        "success": True,
        "paths": [str(dated_path.resolve()), str(latest_path.resolve())],
        "pruned_count": pruned_count,
        "size_bytes": len(snapshot_json.encode("utf-8"))
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Save competitor snapshot")
    parser.add_argument("--snapshot", required=True, help="Path to snapshot JSON file")
    parser.add_argument("--slug", required=True, help="Competitor slug")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    try:
        # Validate date format
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date} (expected YYYY-MM-DD)")
            return 1
        
        # Load snapshot
        snapshot_path = Path(args.snapshot)
        if not snapshot_path.exists():
            logger.error(f"Snapshot file not found: {args.snapshot}")
            return 1
        
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        
        # Save snapshot
        logger.info(f"Saving snapshot for {args.slug} ({args.date})")
        result = save_snapshot(snapshot, args.slug, args.date)
        
        # Output result as JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        logger.info("Snapshot save complete")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
