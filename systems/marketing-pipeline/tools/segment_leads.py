"""
Segment Leads — Sorts scored leads into Hot (80+), Warm (50-79), and Cold (<50) tiers.

Inputs:
    - scored_leads (list[dict]): Scored lead data from score_leads.py

Outputs:
    - dict with:
        - hot (list[dict]): Leads scoring 80+
        - warm (list[dict]): Leads scoring 50-79
        - cold (list[dict]): Leads scoring below 50
        - segment_counts (dict): Count per tier

Usage:
    python segment_leads.py --input output/scored_leads.json --output output/segmented_leads.json

Environment Variables:
    None required.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tier thresholds
HOT_THRESHOLD = 80
WARM_THRESHOLD = 50


def segment(leads: list[dict], hot_threshold: int = HOT_THRESHOLD, warm_threshold: int = WARM_THRESHOLD) -> dict:
    """Segment scored leads into tiers."""
    hot = []
    warm = []
    cold = []

    for lead in leads:
        score = lead.get("total_score", 0)
        if score >= hot_threshold:
            lead["tier"] = "hot"
            hot.append(lead)
        elif score >= warm_threshold:
            lead["tier"] = "warm"
            warm.append(lead)
        else:
            lead["tier"] = "cold"
            cold.append(lead)

    # Sort each tier by score descending
    hot.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    warm.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    cold.sort(key=lambda x: x.get("total_score", 0), reverse=True)

    return {"hot": hot, "warm": warm, "cold": cold}


def main() -> dict[str, Any]:
    """
    Main entry point. Segments scored leads into tiers.

    Returns:
        dict: Segmented lead data.
    """
    parser = argparse.ArgumentParser(description="Segment scored leads into tiers")
    parser.add_argument("--input", required=True, help="Path to scored leads JSON")
    parser.add_argument("--output", default="output/segmented_leads.json", help="Output file path")
    parser.add_argument("--hot-threshold", type=int, default=HOT_THRESHOLD, help="Minimum score for Hot tier")
    parser.add_argument("--warm-threshold", type=int, default=WARM_THRESHOLD, help="Minimum score for Warm tier")
    args = parser.parse_args()

    logger.info("Starting lead segmentation (Hot >= %d, Warm >= %d)", args.hot_threshold, args.warm_threshold)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            scored = json.load(f)

        leads = scored.get("data", {}).get("scored", [])
        if not leads:
            logger.warning("No leads to segment")
            return {"status": "success", "data": {"hot": [], "warm": [], "cold": [], "segment_counts": {}},
                    "message": "No leads to segment"}

        logger.info("Segmenting %d scored leads", len(leads))

        segments = segment(leads, hot_threshold=args.hot_threshold, warm_threshold=args.warm_threshold)
        total = len(leads)

        segment_counts = {
            "hot": len(segments["hot"]),
            "warm": len(segments["warm"]),
            "cold": len(segments["cold"]),
            "total": total,
            "hot_pct": round(len(segments["hot"]) / total * 100, 1) if total else 0,
            "warm_pct": round(len(segments["warm"]) / total * 100, 1) if total else 0,
            "cold_pct": round(len(segments["cold"]) / total * 100, 1) if total else 0,
        }

        logger.info("Segments: Hot=%d (%.1f%%), Warm=%d (%.1f%%), Cold=%d (%.1f%%)",
                     segment_counts["hot"], segment_counts["hot_pct"],
                     segment_counts["warm"], segment_counts["warm_pct"],
                     segment_counts["cold"], segment_counts["cold_pct"])

        if segment_counts["hot"] == 0 and segment_counts["warm"] == 0:
            logger.warning("No Hot or Warm leads found. Consider broadening the lead list or adjusting scoring criteria.")

        result = {
            "status": "success",
            "data": {
                "hot": segments["hot"],
                "warm": segments["warm"],
                "cold": segments["cold"],
                "segment_counts": segment_counts,
            },
            "message": f"Segmented {total} leads: {segment_counts['hot']} hot, {segment_counts['warm']} warm, {segment_counts['cold']} cold",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Segmented data written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON: {e}"}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
