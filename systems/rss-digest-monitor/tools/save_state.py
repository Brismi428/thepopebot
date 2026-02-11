#!/usr/bin/env python
"""
Save RSS Monitor State

Updates the state file with new timestamp and seen GUIDs. Enforces maximum
GUID list size to prevent unbounded state file growth.

Usage:
    python save_state.py state.json new_guids.json current_timestamp [max_guids]

Inputs:
    - state_path: Path to current state JSON
    - new_guids_path: Path to JSON file with new_guids array
    - current_timestamp: ISO format timestamp for last_run
    - max_guids: Maximum number of GUIDs to retain (default: 10000)

Outputs:
    Updated state file written to state_path
"""

import json
import logging
import sys
import pathlib
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(
    state_path: str,
    new_guids_path: str,
    current_timestamp: str,
    max_guids: int = 10000
) -> None:
    """
    Update RSS monitoring state with new timestamp and GUIDs.
    
    Args:
        state_path: Path to current state JSON file
        new_guids_path: Path to new_guids JSON file
        current_timestamp: ISO timestamp for this run
        max_guids: Maximum number of GUIDs to keep (prevents unbounded growth)
    """
    try:
        # Load current state
        logger.info(f"Loading current state from {state_path}")
        path = pathlib.Path(state_path)
        
        if path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            logger.info("State file does not exist - creating new state")
            state = {
                "last_run": None,
                "seen_guids": []
            }
        
        # Load new GUIDs
        logger.info(f"Loading new GUIDs from {new_guids_path}")
        with open(new_guids_path, 'r', encoding='utf-8') as f:
            new_guids_data = json.load(f)
        
        new_guids = new_guids_data.get("new_guids", [])
        logger.info(f"Adding {len(new_guids)} new GUIDs to state")
        
        # Merge GUIDs
        existing_guids = state.get("seen_guids", [])
        updated_guids = existing_guids + new_guids
        
        # Enforce maximum size by keeping most recent entries
        if len(updated_guids) > max_guids:
            logger.warning(
                f"GUID list size ({len(updated_guids)}) exceeds max ({max_guids})"
            )
            logger.warning(f"Keeping most recent {max_guids} GUIDs")
            updated_guids = updated_guids[-max_guids:]
        
        # Create updated state
        updated_state = {
            "last_run": current_timestamp,
            "seen_guids": updated_guids
        }
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write updated state
        logger.info(f"Writing updated state to {state_path}")
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(updated_state, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ State updated successfully")
        logger.info(f"  • last_run: {current_timestamp}")
        logger.info(f"  • seen_guids count: {len(updated_guids)}")
        
        # Calculate state file size
        size_kb = path.stat().st_size / 1024
        logger.info(f"  • state file size: {size_kb:.1f} KB")
        
        if size_kb > 500:
            logger.warning(
                f"State file is large ({size_kb:.1f} KB). Consider reducing max_guids."
            )
        
    except IOError as e:
        logger.error(f"✗ Failed to write state file: {e}")
        logger.error("State was not updated - posts will be retried on next run")
        raise
    
    except Exception as e:
        logger.error(f"✗ Fatal error updating state: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python save_state.py <state.json> <new_guids.json> <timestamp> [max_guids]")
        sys.exit(1)
    
    state_path = sys.argv[1]
    new_guids_path = sys.argv[2]
    timestamp = sys.argv[3]
    max_guids_val = int(sys.argv[4]) if len(sys.argv) > 4 else 10000
    
    main(state_path, new_guids_path, timestamp, max_guids_val)
    sys.exit(0)
