"""
Ingest Leads — Reads, validates, and deduplicates a CSV of leads for the marketing pipeline.

Inputs:
    - input_path (str): Path to a CSV file containing leads. Must have a 'company_name' column.

Outputs:
    - dict with:
        - leads (list[dict]): Validated, deduplicated lead records
        - total_ingested (int): Number of leads after deduplication
        - duplicates_removed (int): Number of duplicate records removed
        - columns (list[str]): Column names detected in the CSV

Usage:
    python ingest_leads.py --input input/leads.csv --output output/ingested_leads.json

Environment Variables:
    None required.
"""

import argparse
import csv
import io
import json
import logging
import os
import pathlib
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_input_csv(input_arg: str | None) -> str | None:
    """Locate the input CSV from CLI arg, env var, or input/ directory."""
    # Check CLI argument first
    if input_arg and os.path.isfile(input_arg):
        return input_arg

    # Check TASK_INPUT env var
    env_path = os.environ.get("TASK_INPUT", "")
    if env_path and os.path.isfile(env_path):
        return env_path

    # Check input/ directory for most recent CSV
    input_dir = pathlib.Path("input")
    if input_dir.is_dir():
        csvs = sorted(input_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if csvs:
            return str(csvs[0])

    return None


def read_csv(path: str) -> tuple[list[dict], list[str]]:
    """Read a CSV file with encoding auto-detection."""
    p = pathlib.Path(path)

    # Try utf-8-sig first (handles BOM), then utf-8, then latin-1
    for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            text = p.read_text(encoding=encoding)
            reader = csv.DictReader(io.StringIO(text))
            rows = [dict(row) for row in reader]
            columns = reader.fieldnames or []
            return rows, list(columns)
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Could not decode CSV file at {path} with any supported encoding")


def normalize_lead(lead: dict) -> dict:
    """Normalize lead data: trim whitespace, preserve original values."""
    normalized = {}
    for key, value in lead.items():
        clean_key = key.strip().lower().replace(" ", "_")
        clean_value = value.strip() if isinstance(value, str) else value
        normalized[clean_key] = clean_value
    return normalized


def deduplicate(leads: list[dict]) -> tuple[list[dict], int]:
    """Remove duplicate leads by company_name (case-insensitive)."""
    seen = set()
    unique = []
    dupes = 0

    for lead in leads:
        name = lead.get("company_name", "").lower()
        if name and name not in seen:
            seen.add(name)
            unique.append(lead)
        elif name:
            dupes += 1
        else:
            # Keep leads with empty company_name for error reporting
            unique.append(lead)

    return unique, dupes


def main() -> dict[str, Any]:
    """
    Main entry point. Ingests and validates a CSV of leads.

    Returns:
        dict: Validated lead data.
    """
    parser = argparse.ArgumentParser(description="Ingest and validate lead CSV")
    parser.add_argument("--input", help="Path to input CSV file")
    parser.add_argument("--output", default="output/ingested_leads.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting lead ingestion")

    try:
        # Find input CSV
        csv_path = find_input_csv(args.input)
        if not csv_path:
            msg = "No input CSV found. Provide --input path, set TASK_INPUT env var, or place a CSV in input/"
            logger.error(msg)
            return {"status": "error", "data": None, "message": msg}

        logger.info("Reading CSV from: %s", csv_path)

        # Read CSV
        rows, columns = read_csv(csv_path)
        logger.info("Read %d rows with columns: %s", len(rows), columns)

        # Normalize column names
        normalized_columns = [c.strip().lower().replace(" ", "_") for c in columns]

        # Validate required column
        if "company_name" not in normalized_columns:
            msg = f"Missing required column 'company_name'. Found columns: {columns}"
            logger.error(msg)
            return {"status": "error", "data": None, "message": msg}

        # Normalize all leads
        leads = [normalize_lead(row) for row in rows]

        # Filter out leads with empty company_name
        valid_leads = [l for l in leads if l.get("company_name")]
        empty_count = len(leads) - len(valid_leads)
        if empty_count > 0:
            logger.warning("Removed %d leads with empty company_name", empty_count)

        # Deduplicate
        unique_leads, dupes = deduplicate(valid_leads)
        logger.info("Deduplicated: %d unique leads, %d duplicates removed", len(unique_leads), dupes)

        result = {
            "status": "success",
            "data": {
                "leads": unique_leads,
                "total_ingested": len(unique_leads),
                "duplicates_removed": dupes,
                "empty_removed": empty_count,
                "columns": normalized_columns,
                "source_file": csv_path,
            },
            "message": f"Ingested {len(unique_leads)} leads from {csv_path}",
        }

        # Write output
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Ingested data written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except ValueError as e:
        logger.error("Validation error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
