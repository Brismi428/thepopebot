"""
Output Profile — Formats and writes the final company profile JSON.

Assembles the final profile from extraction and enrichment stages,
adds metadata, and writes it to the output directory. Supports both
single-URL and batch modes.

Inputs:
    - profile_path (str): Path to the enriched/extracted profile JSON
    - mode (str): "single" or "batch"
    - output_dir (str): Directory for output files

Outputs:
    - company_profile.json (single mode) or batch_profiles/{domain}.json (batch mode)

Usage:
    python output_profile.py --profile enriched.json --output-dir output/
    python output_profile.py --profile enriched.json --output-dir output/ --mode batch
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def format_profile(profile: dict) -> dict:
    """Ensure the profile has all expected fields with proper formatting."""
    template = {
        "url": "",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "company_name": None,
        "description": None,
        "industry": None,
        "products_services": [],
        "target_market": None,
        "pricing_model": None,
        "team_size_signals": None,
        "tech_stack": [],
        "founded": None,
        "location": None,
        "social_links": {},
        "confidence": {},
        "enrichment_sources": [],
        "scraper": "unknown",
    }

    # Merge profile data into template
    for key in template:
        if key in profile and profile[key] is not None:
            template[key] = profile[key]

    # Ensure scraped_at has a value
    if not template["scraped_at"]:
        template["scraped_at"] = datetime.now(timezone.utc).isoformat()

    return template


def get_domain(url: str) -> str:
    """Extract the domain from a URL for use as a filename."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # Sanitize for filename
    return domain.replace(".", "_").replace(":", "_")


def main() -> dict[str, Any]:
    """Format and write the final company profile."""
    parser = argparse.ArgumentParser(description="Output formatted company profile")
    parser.add_argument("--profile", required=True, help="Path to profile JSON")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--mode", choices=["single", "batch"], default="single", help="Output mode")
    args = parser.parse_args()

    logger.info("Formatting profile for output (mode: %s)", args.mode)

    try:
        with open(args.profile, "r", encoding="utf-8") as f:
            profile = json.load(f)

        formatted = format_profile(profile)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.mode == "single":
            output_path = output_dir / "company_profile.json"
        else:
            batch_dir = output_dir / "batch_profiles"
            batch_dir.mkdir(parents=True, exist_ok=True)
            domain = get_domain(formatted.get("url", "unknown"))
            output_path = batch_dir / f"{domain}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, indent=2, ensure_ascii=False)

        logger.info("Profile written to %s", output_path)

        # Print summary
        name = formatted.get("company_name", "Unknown")
        desc = formatted.get("description", "No description")
        logger.info("Profile: %s — %s", name, desc[:80])

        return {
            "status": "success",
            "output_path": str(output_path),
            "company_name": name,
        }

    except Exception as e:
        logger.error("Output failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
