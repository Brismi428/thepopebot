"""
{Tool Name} — {Brief description of what this tool does}

Inputs:
    - {input_name} ({type}): {Description}

Outputs:
    - {output_name} ({type}): {Description}

Usage:
    python {tool_filename}.py --{arg_name} {value}

Environment Variables:
    - {ENV_VAR_NAME}: {Description} (required/optional)

Import Safety:
    This tool is safe to import without side effects. All dependency checks
    and argument parsing happen inside main(), not at module level.
    This allows the API bridge to call main() directly via Python import.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

# Only standard library imports at module level.
# Third-party dependencies are imported inside main() to keep the module
# import-safe — no sys.exit() at module level, no side effects on import.
# This is required for the API bridge (FastAPI) to call main() directly.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _check_dependencies() -> str | None:
    """
    Verify third-party dependencies are installed.

    Returns None if all dependencies are available, or an error message string
    listing what is missing. Called at the start of main(), NOT at module level.
    """
    missing = []
    # {For each third-party dependency:}
    # try:
    #     import {package}
    # except ImportError:
    #     missing.append("{pip-package-name}")
    if missing:
        return f"Missing dependencies: {', '.join(missing)}. Run: pip install {' '.join(missing)}"
    return None


def main() -> dict[str, Any]:
    """
    Main entry point for the tool.

    Returns:
        dict: Result containing status, data, and any error messages.
    """
    # Check dependencies before doing anything else
    dep_error = _check_dependencies()
    if dep_error:
        logger.error(dep_error)
        return {"status": "error", "data": None, "message": dep_error}

    parser = argparse.ArgumentParser(description="{Tool description}")
    parser.add_argument("--input", required=True, help="{Input description}")
    parser.add_argument("--output", default="output.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting {tool_name} with input: %s", args.input)

    try:
        # Step 1: Validate inputs
        # {Validation logic here}

        # Step 2: Execute core logic
        # {Core tool logic here}
        result = {
            "status": "success",
            "data": {},
            "message": "Tool executed successfully",
        }

        # Step 3: Write output
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Results written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
