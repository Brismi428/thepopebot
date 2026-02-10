"""
Output Pipeline — Generates all output files: enriched CSV, hot leads CSV, warm leads CSV,
and pipeline summary JSON.

Inputs:
    - segmented_leads (dict): Segmented lead data from segment_leads.py
    - scored_leads (dict): Scored lead data from score_leads.py
    - outreach_results (dict): Outreach generation results
    - nurture_results (dict): Nurture generation results

Outputs:
    - output/enriched_leads_{timestamp}.csv — Full enriched data
    - output/hot_leads.csv — Hot tier leads
    - output/warm_leads.csv — Warm tier leads
    - output/pipeline_summary.json — Run statistics and breakdown

Usage:
    python output_pipeline.py --segmented output/segmented_leads.json --scored output/scored_leads.json --outreach output/outreach_results.json --nurture output/nurture_results.json

Environment Variables:
    None required.
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# CSV columns for the enriched output
ENRICHED_COLUMNS = [
    "company_name", "website", "industry", "company_size", "location",
    "revenue_estimate", "total_score", "tier",
    "size_fit_score", "tech_stack_score", "budget_signals_score",
    "accessibility_score", "pain_signals_score",
    "tech_stack", "decision_makers", "pain_signals",
    "blog_posts", "job_listings", "funding_news",
    "social_linkedin", "social_twitter", "social_crunchbase",
    "enrichment_status", "enrichment_sources",
]

# CSV columns for tier-specific outputs
TIER_COLUMNS = [
    "company_name", "website", "industry", "company_size", "location",
    "total_score", "decision_makers", "pain_signals",
    "tech_stack", "enrichment_status",
]


def flatten_lead(lead: dict) -> dict:
    """Flatten a lead record for CSV output."""
    breakdown = lead.get("score_breakdown", {})
    social = lead.get("social_profiles", {})

    # Format lists as semicolon-separated strings
    tech_stack = "; ".join(lead.get("tech_stack", [])[:10]) if isinstance(lead.get("tech_stack"), list) else str(lead.get("tech_stack", ""))
    decision_makers = "; ".join(
        f"{dm.get('name', '')} ({dm.get('title', '')}) <{dm.get('email', '')}>"
        for dm in lead.get("decision_makers", [])[:5]
    ) if isinstance(lead.get("decision_makers"), list) else str(lead.get("decision_makers", ""))
    pain_signals = "; ".join(lead.get("pain_signals", [])[:5]) if isinstance(lead.get("pain_signals"), list) else str(lead.get("pain_signals", ""))
    blog_posts = "; ".join(
        p.get("title", "") for p in lead.get("blog_posts", [])[:3]
    ) if isinstance(lead.get("blog_posts"), list) else ""
    job_listings = "; ".join(
        j.get("title", "") for j in lead.get("job_listings", [])[:3]
    ) if isinstance(lead.get("job_listings"), list) else ""
    funding_news = "; ".join(
        f.get("title", "") for f in lead.get("funding_news", [])[:3]
    ) if isinstance(lead.get("funding_news"), list) else ""
    enrichment_sources = ", ".join(lead.get("enrichment_sources", [])) if isinstance(lead.get("enrichment_sources"), list) else ""

    return {
        "company_name": lead.get("company_name", ""),
        "website": lead.get("website", lead.get("url", "")),
        "industry": lead.get("industry", ""),
        "company_size": lead.get("company_size", ""),
        "location": lead.get("location", ""),
        "revenue_estimate": lead.get("revenue_estimate", ""),
        "total_score": lead.get("total_score", 0),
        "tier": lead.get("tier", ""),
        "size_fit_score": breakdown.get("size_fit", 0),
        "tech_stack_score": breakdown.get("tech_stack", 0),
        "budget_signals_score": breakdown.get("budget_signals", 0),
        "accessibility_score": breakdown.get("accessibility", 0),
        "pain_signals_score": breakdown.get("pain_signals", 0),
        "tech_stack": tech_stack,
        "decision_makers": decision_makers,
        "pain_signals": pain_signals,
        "blog_posts": blog_posts,
        "job_listings": job_listings,
        "funding_news": funding_news,
        "social_linkedin": social.get("linkedin", "") if isinstance(social, dict) else "",
        "social_twitter": social.get("twitter", "") if isinstance(social, dict) else "",
        "social_crunchbase": social.get("crunchbase", "") if isinstance(social, dict) else "",
        "enrichment_status": lead.get("enrichment_status", ""),
        "enrichment_sources": enrichment_sources,
    }


def write_csv(leads: list[dict], filepath: str, columns: list[str]) -> int:
    """Write leads to a CSV file. Returns number of rows written."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    flattened = [flatten_lead(lead) for lead in leads]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flattened)

    return len(flattened)


def main() -> dict[str, Any]:
    """
    Main entry point. Generates all output CSVs and summary JSON.

    Returns:
        dict: Summary of generated outputs.
    """
    parser = argparse.ArgumentParser(description="Generate pipeline output files")
    parser.add_argument("--segmented", required=True, help="Path to segmented leads JSON")
    parser.add_argument("--scored", required=True, help="Path to scored leads JSON")
    parser.add_argument("--outreach", default="", help="Path to outreach results JSON")
    parser.add_argument("--nurture", default="", help="Path to nurture results JSON")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    logger.info("Starting output generation")

    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")

        # Load segmented leads
        with open(args.segmented, "r", encoding="utf-8") as f:
            segmented = json.load(f)

        seg_data = segmented.get("data", {})
        hot_leads = seg_data.get("hot", [])
        warm_leads = seg_data.get("warm", [])
        cold_leads = seg_data.get("cold", [])
        all_leads = hot_leads + warm_leads + cold_leads

        # Load scored data for stats
        with open(args.scored, "r", encoding="utf-8") as f:
            scored = json.load(f)
        score_stats = scored.get("data", {}).get("stats", {})

        # Load outreach results if available
        outreach_data = {}
        if args.outreach and os.path.isfile(args.outreach):
            with open(args.outreach, "r", encoding="utf-8") as f:
                outreach_data = json.load(f).get("data", {})

        # Load nurture results if available
        nurture_data = {}
        if args.nurture and os.path.isfile(args.nurture):
            with open(args.nurture, "r", encoding="utf-8") as f:
                nurture_data = json.load(f).get("data", {})

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Write enriched leads CSV (all leads)
        enriched_path = os.path.join(output_dir, f"enriched_leads_{timestamp}.csv")
        enriched_count = write_csv(all_leads, enriched_path, ENRICHED_COLUMNS)
        logger.info("Wrote %d leads to %s", enriched_count, enriched_path)

        # Write hot leads CSV
        hot_path = os.path.join(output_dir, "hot_leads.csv")
        hot_count = write_csv(hot_leads, hot_path, TIER_COLUMNS)
        logger.info("Wrote %d hot leads to %s", hot_count, hot_path)

        # Write warm leads CSV
        warm_path = os.path.join(output_dir, "warm_leads.csv")
        warm_count = write_csv(warm_leads, warm_path, TIER_COLUMNS)
        logger.info("Wrote %d warm leads to %s", warm_count, warm_path)

        # Generate summary
        segment_counts = seg_data.get("segment_counts", {})
        summary = {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_leads_processed": len(all_leads),
            "enrichment_stats": {
                "full": sum(1 for l in all_leads if l.get("enrichment_status") == "full"),
                "partial": sum(1 for l in all_leads if l.get("enrichment_status") == "partial"),
                "failed": sum(1 for l in all_leads if l.get("enrichment_status") == "failed"),
            },
            "score_distribution": score_stats.get("score_distribution", {}),
            "dimension_averages": score_stats.get("dimension_averages", {}),
            "segment_breakdown": {
                "hot": {"count": len(hot_leads), "pct": segment_counts.get("hot_pct", 0)},
                "warm": {"count": len(warm_leads), "pct": segment_counts.get("warm_pct", 0)},
                "cold": {"count": len(cold_leads), "pct": segment_counts.get("cold_pct", 0)},
            },
            "outreach": {
                "sequences_generated": outreach_data.get("generated_count", 0),
                "companies": [s.get("company", "") for s in outreach_data.get("sequences", [])],
                "failed": outreach_data.get("failed", []),
            },
            "nurture": {
                "generated": nurture_data.get("sequence") is not None,
                "email_count": nurture_data.get("email_count", 0),
                "warm_leads_analyzed": nurture_data.get("warm_leads_analyzed", 0),
            },
            "output_files": {
                "enriched_csv": enriched_path,
                "hot_csv": hot_path,
                "warm_csv": warm_path,
                "outreach_dir": "output/outreach/",
                "nurture_dir": "output/nurture/",
            },
        }

        summary_path = os.path.join(output_dir, "pipeline_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info("Summary written to %s", summary_path)

        result = {
            "status": "success",
            "data": {
                "files_written": [enriched_path, hot_path, warm_path, summary_path],
                "summary": summary,
            },
            "message": f"Generated {len(all_leads)} enriched leads: {len(hot_leads)} hot, {len(warm_leads)} warm, {len(cold_leads)} cold",
        }

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
