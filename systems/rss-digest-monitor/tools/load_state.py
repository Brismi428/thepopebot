#!/usr/bin/env python
"""
Load RSS Monitor State

Reads the state file (last_run timestamp and seen_guids list) or initializes
an empty state on first run. Handles corrupted state files gracefully.

Usage:
    python load_state.py [state_file_path]

Inputs:
    - state_file_path: Path to state JSON file (default: state/rss_state.json)

Outputs:
    JSON object: {"last_run": ISO timestamp or null, "seen_guids": [list]}
"""

import json
import logging
import pathlib
import sys
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(state_file_path: str = "state/rss_state.json") -> Dict[str, Any]:
    """
    Load RSS monitoring state from file or initialize empty state.
    
    Args:
        state_file_path: Path to state JSON file
        
    Returns:
        Dictionary with last_run (ISO timestamp or None) and seen_guids (list)
    """
    try:
        path = pathlib.Path(state_file_path)
        
        # Check if state file exists
        if not path.exists():
            logger.info(f"State file not found at {state_file_path} - initializing empty state (first run)")
            return {
                "last_run": None,
                "seen_guids": []
            }
        
        # Load and parse JSON
        logger.info(f"Loading state from {state_file_path}")
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        
        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("State file must contain a JSON object")
        
        if "last_run" not in data or "seen_guids" not in data:
            raise ValueError("State file missing required keys (last_run, seen_guids)")
        
        if not isinstance(data["seen_guids"], list):
            raise ValueError("seen_guids must be a list")
        
        logger.info(f"✓ Loaded state: last_run={data['last_run']}, {len(data['seen_guids'])} seen GUIDs")
        return data
        
    except json.JSONDecodeError as e:
        logger.warning(f"State file corrupted (invalid JSON): {e}")
        logger.warning("Initializing empty state - this will cause posts to be re-processed")
        return {
            "last_run": None,
            "seen_guids": []
        }
    
    except ValueError as e:
        logger.warning(f"State file has invalid structure: {e}")
        logger.warning("Initializing empty state")
        return {
            "last_run": None,
            "seen_guids": []
        }
    
    except Exception as e:
        logger.error(f"Unexpected error loading state: {e}")
        logger.warning("Initializing empty state")
        return {
            "last_run": None,
            "seen_guids": []
        }


if __name__ == "__main__":
    state_path = sys.argv[1] if len(sys.argv) > 1 else "state/rss_state.json"
    result = main(state_path)
    print(json.dumps(result, indent=2))
    sys.exit(0)
