"""
Score Leads — Scores each lead based on how well it matches the ideal customer profile.

Inputs:
    - enriched_data (list[dict]): Enriched company data from extract_contacts.py
    - profile (dict): Ideal customer profile with industry, company_size, location, keywords

Outputs:
    - dict with:
        - scored (list[dict]): Leads with match_score and rank, sorted by score descending
        - qualified_count (int): Number of leads above min_score threshold

Usage:
    python score_leads.py --input output/enriched_data.json --profile '{"industry":"SaaS",...}' --min-score 40

Environment Variables:
    None required.
"""

import argparse
import json
import logging
import re
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Size range mapping for comparison
SIZE_RANGES = {
    "1-10": (1, 10),
    "11-50": (11, 50),
    "51-200": (51, 200),
    "50-200": (50, 200),
    "201-500": (201, 500),
    "200-500": (200, 500),
    "501-1000": (501, 1000),
    "500-1000": (500, 1000),
    "1001-5000": (1001, 5000),
    "1000-5000": (1000, 5000),
    "5001-10000": (5001, 10000),
    "5000+": (5000, 999999),
    "10000+": (10000, 999999),
    "1000+": (1000, 999999),
}

# Industry synonyms for fuzzy matching
INDUSTRY_SYNONYMS = {
    "saas": ["software", "cloud", "platform", "tech", "technology"],
    "healthcare": ["health", "medical", "pharma", "biotech", "wellness"],
    "fintech": ["financial", "finance", "banking", "payments", "insurtech"],
    "ecommerce": ["e-commerce", "retail", "online store", "marketplace"],
    "edtech": ["education", "learning", "ed-tech", "training"],
    "ai": ["artificial intelligence", "machine learning", "ml", "deep learning"],
    "cybersecurity": ["security", "infosec", "cyber"],
    "logistics": ["supply chain", "shipping", "freight", "transportation"],
    "real estate": ["proptech", "property", "realty"],
    "marketing": ["martech", "advertising", "adtech", "digital marketing"],
}


def parse_size_range(size_str: str) -> tuple[int, int] | None:
    """Parse a company size string into a numeric range."""
    if not size_str or size_str == "unknown":
        return None

    # Check predefined ranges
    normalized = size_str.strip().lower().replace(" ", "")
    for key, range_val in SIZE_RANGES.items():
        if key.lower().replace(" ", "") == normalized:
            return range_val

    # Try to extract numbers
    numbers = re.findall(r'\d+', size_str)
    if len(numbers) >= 2:
        return (int(numbers[0]), int(numbers[1]))
    elif len(numbers) == 1:
        n = int(numbers[0])
        if "+" in size_str:
            return (n, 999999)
        return (n, n)

    return None


def score_industry(company_industry: str, target_industry: str) -> int:
    """Score industry match (0-30 points)."""
    if not company_industry or company_industry == "unknown":
        return 5  # Small benefit of the doubt

    company_lower = company_industry.lower()
    target_lower = target_industry.lower()

    # Exact match
    if target_lower in company_lower or company_lower in target_lower:
        return 30

    # Synonym match
    synonyms = INDUSTRY_SYNONYMS.get(target_lower, [])
    for syn in synonyms:
        if syn in company_lower:
            return 20

    # Reverse synonym check
    for key, syns in INDUSTRY_SYNONYMS.items():
        if target_lower in syns or key == target_lower:
            for syn in syns:
                if syn in company_lower:
                    return 15

    return 0


def score_size(company_size: str, target_size: str) -> int:
    """Score company size match (0-25 points)."""
    target_range = parse_size_range(target_size)
    company_range = parse_size_range(company_size)

    if not target_range or not company_range:
        return 5  # Unknown size gets small benefit of the doubt

    target_min, target_max = target_range
    company_min, company_max = company_range

    # Check overlap
    if company_min <= target_max and company_max >= target_min:
        return 25  # Within range

    # Check adjacency (within 2x of target range)
    target_mid = (target_min + min(target_max, 50000)) / 2
    company_mid = (company_min + min(company_max, 50000)) / 2

    ratio = max(target_mid, company_mid) / max(min(target_mid, company_mid), 1)
    if ratio <= 3:
        return 12  # Adjacent range

    return 0


def score_location(company_location: str, target_location: str) -> int:
    """Score location match (0-20 points)."""
    if not company_location:
        return 3  # Small benefit of the doubt

    company_lower = company_location.lower()
    target_lower = target_location.lower()

    # Exact match or substring match
    if target_lower in company_lower or company_lower in target_lower:
        return 20

    # Country-level match
    target_parts = [p.strip() for p in target_lower.replace(",", " ").split()]
    company_parts = [p.strip() for p in company_lower.replace(",", " ").split()]

    common = set(target_parts) & set(company_parts)
    if common:
        # Partial location match (same country or state)
        return 10

    return 0


def score_keywords(company_text: str, keywords: list[str]) -> int:
    """Score keyword match (0-25 points)."""
    if not company_text or not keywords:
        return 0

    text_lower = company_text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)

    if not keywords:
        return 0

    match_ratio = matches / len(keywords)

    if match_ratio >= 0.75:
        return 25
    elif match_ratio >= 0.5:
        return 18
    elif match_ratio >= 0.25:
        return 12
    elif matches > 0:
        return 6

    return 0


def compute_score(company: dict, profile: dict) -> int:
    """Compute total match score for a company against the profile."""
    industry_score = score_industry(
        company.get("industry", ""),
        profile.get("industry", ""),
    )

    size_score = score_size(
        company.get("company_size", ""),
        profile.get("company_size", ""),
    )

    location_score = score_location(
        company.get("location", ""),
        profile.get("location", ""),
    )

    # Combine description + technologies for keyword matching
    keyword_text = " ".join([
        company.get("description", ""),
        company.get("search_snippet", ""),
        " ".join(company.get("technologies", [])),
    ])
    keyword_score = score_keywords(
        keyword_text,
        profile.get("keywords", []),
    )

    total = industry_score + size_score + location_score + keyword_score
    return min(total, 100)


def main() -> dict[str, Any]:
    """
    Main entry point. Scores and ranks leads.

    Returns:
        dict: Scored and ranked leads.
    """
    parser = argparse.ArgumentParser(description="Score and rank leads")
    parser.add_argument("--input", required=True, help="Path to enriched data JSON")
    parser.add_argument("--profile", required=True, help="JSON string of ideal customer profile")
    parser.add_argument("--min-score", type=float, default=40, help="Minimum score threshold")
    parser.add_argument("--output", default="output/scored_leads.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting lead scoring")

    try:
        # Load enriched data
        with open(args.input, "r", encoding="utf-8") as f:
            enriched_data = json.load(f)

        profile = json.loads(args.profile)
        companies = enriched_data.get("data", {}).get("enriched", [])

        if not companies:
            logger.warning("No companies to score")
            return {"status": "success", "data": {"scored": [], "qualified_count": 0},
                    "message": "No companies to score"}

        logger.info("Scoring %d companies against profile", len(companies))

        # Score each company
        scored = []
        for company in companies:
            score = compute_score(company, profile)
            company_scored = {**company, "match_score": score}
            scored.append(company_scored)

        # Sort by score descending
        scored.sort(key=lambda x: x["match_score"], reverse=True)

        # Filter by min_score
        qualified = [c for c in scored if c["match_score"] >= args.min_score]

        # Assign ranks
        for i, company in enumerate(qualified):
            company["rank"] = i + 1

        # Compute stats
        all_scores = [c["match_score"] for c in scored]
        qualified_scores = [c["match_score"] for c in qualified]

        stats = {
            "total_scored": len(scored),
            "qualified_count": len(qualified),
            "min_score_threshold": args.min_score,
            "score_distribution": {
                "min": min(all_scores) if all_scores else 0,
                "max": max(all_scores) if all_scores else 0,
                "avg": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
                "median": sorted(all_scores)[len(all_scores) // 2] if all_scores else 0,
            },
        }

        logger.info("Qualified leads: %d/%d (min score: %.0f)", len(qualified), len(scored), args.min_score)

        result = {
            "status": "success",
            "data": {
                "scored": qualified,
                "all_scored": scored,
                "qualified_count": len(qualified),
                "stats": stats,
            },
            "message": f"Scored {len(scored)} leads, {len(qualified)} qualified",
        }

        import os
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
