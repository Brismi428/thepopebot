"""
Enrich Profile — Supplements a company profile with additional search data.

Uses web search (Brave Search MCP or fallback) to find additional information
about the company from external sources like Crunchbase, LinkedIn, review sites.

Inputs:
    - profile_path (str): Path to the extracted profile JSON
    - company_name (str): Company name to search for (overrides profile data)

Outputs:
    - Enriched profile JSON with additional data merged in

Usage:
    python enrich_profile.py --profile profile.json --output enriched.json

Environment Variables:
    - BRAVE_SEARCH_API_KEY: Brave Search API key (optional — skips enrichment if missing)
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


def search_brave(query: str, api_key: str, count: int = 5) -> list[dict]:
    """Search using Brave Search API."""
    try:
        import requests
    except ImportError:
        logger.error("requests not installed")
        return []

    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            params={"q": query, "count": count},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
            })
        return results
    except Exception as e:
        logger.warning("Brave Search failed: %s", e)
        return []


def extract_enrichment(search_results: list[dict], field: str) -> dict[str, Any]:
    """Extract enrichment data from search results for a specific field."""
    snippets = []
    sources = []
    for result in search_results:
        desc = result.get("description", "")
        if desc:
            snippets.append(desc)
            sources.append(result.get("url", ""))

    if not snippets:
        return {"data": None, "sources": [], "confidence": "none"}

    return {
        "data": " | ".join(snippets[:3]),
        "sources": sources[:3],
        "confidence": "low",
    }


def main() -> dict[str, Any]:
    """Enrich a company profile with additional search data."""
    parser = argparse.ArgumentParser(description="Enrich company profile with search data")
    parser.add_argument("--profile", required=True, help="Path to profile JSON")
    parser.add_argument("--output", default="enriched.json", help="Output enriched profile path")
    args = parser.parse_args()

    logger.info("Enriching profile from: %s", args.profile)

    try:
        with open(args.profile, "r", encoding="utf-8") as f:
            profile = json.load(f)

        brave_key = os.environ.get("BRAVE_SEARCH_API_KEY")
        if not brave_key:
            logger.info("No BRAVE_SEARCH_API_KEY — skipping enrichment")
            profile["enrichment_sources"] = []
            profile["enrichment_note"] = "Skipped — no search API key available"
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)
            return {"status": "success", "data": profile, "message": "Enrichment skipped"}

        company_name = profile.get("company_name", "")
        if not company_name:
            logger.warning("No company name in profile — skipping enrichment")
            profile["enrichment_sources"] = []
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)
            return {"status": "success", "data": profile, "message": "No company name to search"}

        logger.info("Searching for additional info on: %s", company_name)
        enrichment_sources = []

        # Search for company overview
        overview_results = search_brave(f'"{company_name}" company overview', brave_key)
        if overview_results:
            enrichment_sources.extend([r["url"] for r in overview_results[:2]])

        # Search for funding/team info
        funding_results = search_brave(f'"{company_name}" funding team size employees', brave_key)
        if funding_results:
            enrichment = extract_enrichment(funding_results, "team_size_signals")
            if enrichment["data"] and profile.get("confidence", {}).get("team_size_signals") in ("none", "low"):
                profile["team_size_signals"] = enrichment["data"]
                profile.setdefault("confidence", {})["team_size_signals"] = "low"
                enrichment_sources.extend(enrichment["sources"])

        # Search for tech stack
        tech_results = search_brave(f'"{company_name}" tech stack technology', brave_key)
        if tech_results:
            enrichment = extract_enrichment(tech_results, "tech_stack")
            if enrichment["data"]:
                enrichment_sources.extend(enrichment["sources"])

        profile["enrichment_sources"] = list(set(enrichment_sources))
        logger.info("Enrichment complete — %d additional sources found", len(profile["enrichment_sources"]))

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        return {"status": "success", "data": profile}

    except Exception as e:
        logger.error("Enrichment failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
