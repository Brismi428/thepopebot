"""
Generate CSV — Formats scored leads into a ranked CSV file and generates a run summary.

Inputs:
    - scored_leads (list[dict]): Scored and ranked leads from score_leads.py
    - profile (dict): Ideal customer profile used for this run

Outputs:
    - CSV file at output/leads_{timestamp}.csv
    - JSON summary at output/run_summary.json

Usage:
    python generate_csv.py --input output/scored_leads.json --profile '{"industry":"SaaS",...}'

Environment Variables:
    None required.
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "rank",
    "company_name",
    "website",
    "industry",
    "company_size",
    "location",
    "match_score",
    "email",
    "phone",
    "description",
    "scraped_at",
]


def format_lead_for_csv(lead: dict) -> dict:
    """Format a lead record for CSV output."""
    return {
        "rank": lead.get("rank", ""),
        "company_name": lead.get("company_name", lead.get("search_title", "")),
        "website": lead.get("url", ""),
        "industry": lead.get("industry", "unknown"),
        "company_size": lead.get("company_size", "unknown"),
        "location": lead.get("location", ""),
        "match_score": lead.get("match_score", 0),
        "email": lead.get("email", ""),
        "phone": lead.get("phone", ""),
        "description": lead.get("description", lead.get("search_snippet", "")),
        "scraped_at": lead.get("scraped_at", ""),
    }


def main() -> dict[str, Any]:
    """
    Main entry point. Generates CSV and run summary.

    Returns:
        dict: Result with file paths and statistics.
    """
    parser = argparse.ArgumentParser(description="Generate leads CSV and run summary")
    parser.add_argument("--input", required=True, help="Path to scored leads JSON")
    parser.add_argument("--profile", required=True, help="JSON string of ideal customer profile")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    logger.info("Starting CSV generation")

    try:
        # Load scored leads
        with open(args.input, "r", encoding="utf-8") as f:
            scored_data = json.load(f)

        profile = json.loads(args.profile)
        qualified_leads = scored_data.get("data", {}).get("scored", [])
        stats = scored_data.get("data", {}).get("stats", {})

        os.makedirs(args.output_dir, exist_ok=True)

        # Generate timestamp
        timestamp = time.strftime("%Y-%m-%d_%H%M", time.gmtime())

        # Write CSV
        csv_filename = f"leads_{timestamp}.csv"
        csv_path = os.path.join(args.output_dir, csv_filename)

        rows_written = 0
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()

            for lead in qualified_leads:
                row = format_lead_for_csv(lead)
                writer.writerow(row)
                rows_written += 1

        logger.info("CSV written: %s (%d rows)", csv_path, rows_written)

        # Generate run summary
        summary = {
            "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "input_profile": profile,
            "results": {
                "total_companies_found": stats.get("total_scored", 0),
                "total_qualified": stats.get("qualified_count", 0),
                "min_score_threshold": stats.get("min_score_threshold", 0),
                "score_distribution": stats.get("score_distribution", {}),
            },
            "output_files": {
                "csv": csv_filename,
                "csv_path": csv_path,
            },
        }

        summary_path = os.path.join(args.output_dir, "run_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info("Run summary written: %s", summary_path)

        # Also write/update a latest symlink-like file
        latest_path = os.path.join(args.output_dir, "latest_leads.csv")
        with open(latest_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for lead in qualified_leads:
                writer.writerow(format_lead_for_csv(lead))

        logger.info("Latest leads file updated: %s", latest_path)

        result = {
            "status": "success",
            "data": {
                "csv_path": csv_path,
                "summary_path": summary_path,
                "latest_path": latest_path,
                "rows_written": rows_written,
            },
            "message": f"Generated CSV with {rows_written} qualified leads",
        }

        return result

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)

        # Fallback: try to write whatever we have as JSON
        try:
            fallback_path = os.path.join(args.output_dir, "leads_fallback.json")
            with open(fallback_path, "w", encoding="utf-8") as f:
                json.dump({"error": str(e), "data": None}, f, indent=2)
            logger.info("Fallback JSON written to %s", fallback_path)
        except Exception:
            pass

        return {"status": "error", "data": None, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
