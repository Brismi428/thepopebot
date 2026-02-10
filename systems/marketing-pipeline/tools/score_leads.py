"""
Score Leads — Deep-scores each enriched lead on a 0-100 scale across 5 dimensions:
company size fit, tech stack compatibility, budget signals, decision maker accessibility,
and pain signal detection.

Inputs:
    - enriched_leads (list[dict]): Enriched lead data from enrich_leads.py

Outputs:
    - dict with:
        - scored (list[dict]): Leads with score breakdown and total_score
        - stats (dict): Score distribution statistics

Usage:
    python score_leads.py --input output/enriched_leads.json --output output/scored_leads.json

Environment Variables:
    None required.
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tools that indicate tech stack compatibility — weighted by automation relevance
AUTOMATION_TOOLS = {
    "high": ["n8n", "zapier", "make", "integromat", "workato", "tray.io", "tray",
             "celigo", "boomi", "mulesoft", "power automate", "automate.io"],
    "medium": ["airtable", "notion", "monday.com", "asana", "jira", "slack",
               "hubspot", "salesforce", "marketo", "pardot", "mailchimp",
               "klaviyo", "intercom", "zendesk", "freshdesk",
               "hootsuite", "sprout social", "semrush", "ahrefs", "moz"],
    "low": ["google workspace", "microsoft 365", "dropbox", "trello",
            "google analytics", "google tag manager", "cloudflare",
            "stripe", "wordpress"],
}

# Job title patterns indicating ops/automation hiring
OPS_HIRING_PATTERNS = [
    r"(?i)operations?\s+(manager|director|lead|head|vp)",
    r"(?i)automation\s+(engineer|specialist|manager)",
    r"(?i)process\s+(improvement|engineer|manager)",
    r"(?i)business\s+operations",
    r"(?i)rev\s*ops",
    r"(?i)sales\s*ops",
    r"(?i)marketing\s*ops",
    r"(?i)data\s+engineer",
    r"(?i)integration\s+(engineer|specialist)",
    r"(?i)workflow\s+(engineer|manager|automation)",
]

# Size range parsing
SIZE_RANGES = {
    "1-10": (1, 10), "11-50": (11, 50), "50-200": (50, 200),
    "51-200": (51, 200), "201-500": (201, 500), "200-500": (200, 500),
    "501-1000": (501, 1000), "500-1000": (500, 1000),
    "1001-5000": (1001, 5000), "1000-5000": (1000, 5000),
    "5001-10000": (5001, 10000), "5000+": (5000, 999999),
    "10000+": (10000, 999999), "1000+": (1000, 999999),
}

# Target company size range for scoring (configurable)
TARGET_SIZE_MIN = 20
TARGET_SIZE_MAX = 1000


def parse_size(size_str: str | int) -> tuple[int, int] | None:
    """Parse company size into a numeric range."""
    if isinstance(size_str, int):
        return (size_str, size_str)

    if not size_str or size_str == "unknown":
        return None

    normalized = str(size_str).strip().lower().replace(" ", "").replace(",", "")

    for key, range_val in SIZE_RANGES.items():
        if key.lower().replace(" ", "") == normalized:
            return range_val

    numbers = re.findall(r'\d+', normalized)
    if len(numbers) >= 2:
        return (int(numbers[0]), int(numbers[1]))
    elif len(numbers) == 1:
        n = int(numbers[0])
        if "+" in normalized:
            return (n, 999999)
        return (n, n)

    return None


def score_size_fit(lead: dict) -> int:
    """Score company size fit (0-20 points)."""
    size = lead.get("company_size", "unknown")
    parsed = parse_size(size)

    if not parsed:
        return 5  # No data — small benefit of the doubt

    company_min, company_max = parsed

    # Check if company falls within target range
    if company_min <= TARGET_SIZE_MAX and company_max >= TARGET_SIZE_MIN:
        return 20  # Perfect fit

    # Adjacent (within 2x of target)
    if company_min <= TARGET_SIZE_MAX * 2 and company_max >= TARGET_SIZE_MIN / 2:
        return 10

    return 2  # Way outside target


def score_tech_stack(lead: dict) -> int:
    """Score tech stack compatibility (0-25 points). Focus on automation tool usage."""
    tech_stack = lead.get("tech_stack", [])
    if not tech_stack:
        return 3  # No data

    tech_lower = [t.lower() for t in tech_stack]
    score = 0

    # Check for high-value automation tools
    for tool in AUTOMATION_TOOLS["high"]:
        if any(tool in t for t in tech_lower):
            score += 12
            break

    # Check for medium-value tools (marketing, CRM, SEO, social)
    medium_count = sum(1 for tool in AUTOMATION_TOOLS["medium"]
                       if any(tool in t for t in tech_lower))
    score += min(medium_count * 3, 12)

    # Check for low-value tools (analytics, infrastructure)
    low_count = sum(1 for tool in AUTOMATION_TOOLS["low"]
                    if any(tool in t for t in tech_lower))
    score += min(low_count * 2, 6)

    return min(score, 25)


def score_budget_signals(lead: dict) -> int:
    """Score budget signals (0-20 points): job postings, funding, growth indicators."""
    score = 0

    # Job listings indicating ops/automation hiring
    job_listings = lead.get("job_listings", [])
    ops_jobs = 0
    for job in job_listings:
        title = job.get("title", "") + " " + job.get("description", "")
        for pattern in OPS_HIRING_PATTERNS:
            if re.search(pattern, title):
                ops_jobs += 1
                break

    if ops_jobs >= 2:
        score += 8
    elif ops_jobs >= 1:
        score += 5

    # Recent funding
    funding_news = lead.get("funding_news", [])
    if funding_news:
        score += 6

    # Growth indicators (hiring volume)
    if len(job_listings) >= 5:
        score += 6
    elif len(job_listings) >= 2:
        score += 3

    return min(score, 20)


def score_accessibility(lead: dict) -> int:
    """Score decision maker accessibility (0-15 points)."""
    decision_makers = lead.get("decision_makers", [])
    if not decision_makers:
        return 2  # No contacts found

    score = 0

    # Check for direct emails
    has_email = any(dm.get("email") for dm in decision_makers)
    if has_email:
        score += 10

    # Check for LinkedIn profiles
    has_linkedin = any(dm.get("linkedin_url") for dm in decision_makers)
    if has_linkedin:
        score += 3

    # Multiple contacts available
    if len(decision_makers) >= 2:
        score += 2

    return min(score, 15)


def score_pain_signals(lead: dict) -> int:
    """Score pain signal detection (0-20 points)."""
    pain_signals = lead.get("pain_signals", [])
    if not pain_signals:
        return 2  # No analysis available

    score = 0

    signal_text = " ".join(pain_signals).lower()

    # Hiring for ops roles
    if any(kw in signal_text for kw in ["hiring", "recruiting", "operations role", "ops position"]):
        score += 7

    # Manual process complaints
    if any(kw in signal_text for kw in ["manual", "manual process", "spreadsheet", "time-consuming",
                                         "inefficient", "bottleneck"]):
        score += 7

    # Seeking automation
    if any(kw in signal_text for kw in ["automat", "streamline", "optimize", "workflow",
                                         "integration", "tool evaluation"]):
        score += 6

    # Even if no specific keywords matched, having signals is worth something
    if score == 0 and pain_signals:
        score = min(len(pain_signals) * 3, 10)

    return min(score, 20)


def compute_score(lead: dict) -> dict:
    """Compute the full multi-dimensional score for a lead."""
    size_fit = score_size_fit(lead)
    tech_stack = score_tech_stack(lead)
    budget = score_budget_signals(lead)
    accessibility = score_accessibility(lead)
    pain = score_pain_signals(lead)

    total = min(size_fit + tech_stack + budget + accessibility + pain, 100)

    return {
        "size_fit": size_fit,
        "tech_stack": tech_stack,
        "budget_signals": budget,
        "accessibility": accessibility,
        "pain_signals": pain,
        "total": total,
    }


def main() -> dict[str, Any]:
    """
    Main entry point. Scores enriched leads on 5 dimensions.

    Returns:
        dict: Scored lead data with breakdowns.
    """
    parser = argparse.ArgumentParser(description="Deep-score enriched leads")
    parser.add_argument("--input", required=True, help="Path to enriched leads JSON")
    parser.add_argument("--output", default="output/scored_leads.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting lead scoring")

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            enriched = json.load(f)

        leads = enriched.get("data", {}).get("enriched", [])
        if not leads:
            logger.warning("No leads to score")
            return {"status": "success", "data": {"scored": [], "stats": {}},
                    "message": "No leads to score"}

        logger.info("Scoring %d leads across 5 dimensions", len(leads))

        scored_leads = []
        for lead in leads:
            score_breakdown = compute_score(lead)
            scored_lead = {**lead, "score_breakdown": score_breakdown, "total_score": score_breakdown["total"]}
            scored_leads.append(scored_lead)

        # Sort by total score descending
        scored_leads.sort(key=lambda x: x["total_score"], reverse=True)

        # Compute stats
        all_scores = [l["total_score"] for l in scored_leads]
        stats = {
            "total_scored": len(scored_leads),
            "score_distribution": {
                "min": min(all_scores),
                "max": max(all_scores),
                "avg": round(sum(all_scores) / len(all_scores), 1),
                "median": sorted(all_scores)[len(all_scores) // 2],
            },
            "dimension_averages": {
                "size_fit": round(sum(l["score_breakdown"]["size_fit"] for l in scored_leads) / len(scored_leads), 1),
                "tech_stack": round(sum(l["score_breakdown"]["tech_stack"] for l in scored_leads) / len(scored_leads), 1),
                "budget_signals": round(sum(l["score_breakdown"]["budget_signals"] for l in scored_leads) / len(scored_leads), 1),
                "accessibility": round(sum(l["score_breakdown"]["accessibility"] for l in scored_leads) / len(scored_leads), 1),
                "pain_signals": round(sum(l["score_breakdown"]["pain_signals"] for l in scored_leads) / len(scored_leads), 1),
            },
        }

        result = {
            "status": "success",
            "data": {
                "scored": scored_leads,
                "stats": stats,
            },
            "message": f"Scored {len(scored_leads)} leads. Range: {stats['score_distribution']['min']}-{stats['score_distribution']['max']}, Avg: {stats['score_distribution']['avg']}",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Scored data written to %s", args.output)
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
