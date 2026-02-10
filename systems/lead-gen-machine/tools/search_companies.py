"""
Search Companies — Searches the web for companies matching an ideal customer profile.

Inputs:
    - queries (list[str]): Search queries to execute
    - max_results (int): Maximum total results to return (default: 100)

Outputs:
    - dict with:
        - results (list[dict]): Companies found, each with name, url, snippet
        - queries_used (list[str]): Queries that were executed
        - total_found (int): Total raw results before dedup

Usage:
    python search_companies.py --queries '["SaaS companies San Francisco AI"]' --max-results 100

Environment Variables:
    - BRAVE_API_KEY: Brave Search API key (required for primary search)
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Domains to filter out (not actual company websites)
EXCLUDED_DOMAINS = {
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "indeed.com", "glassdoor.com", "yelp.com", "wikipedia.org",
    "crunchbase.com", "bloomberg.com", "reuters.com", "youtube.com",
    "reddit.com", "quora.com", "pinterest.com", "instagram.com",
    "tiktok.com", "amazon.com", "ebay.com", "walmart.com",
    "gov", "edu",
}


def search_brave(query: str, count: int = 20) -> list[dict]:
    """Execute a search via the Brave Search API."""
    import httpx

    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        logger.warning("BRAVE_API_KEY not set, skipping Brave search")
        return []

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": min(count, 20)}

    try:
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
            })
        return results

    except Exception as e:
        logger.error("Brave search failed for query '%s': %s", query, e)
        return []


def search_fallback(query: str, count: int = 20) -> list[dict]:
    """Fallback search using httpx to scrape a search-results-like approach.

    This is a minimal fallback — returns empty if Brave is unavailable and
    no other search API is configured.
    """
    logger.warning("Using fallback search — limited results expected")
    return []


def is_company_domain(url: str) -> bool:
    """Check if a URL looks like an actual company website (not a directory/social site)."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

        for excluded in EXCLUDED_DOMAINS:
            if domain.endswith(excluded):
                return False

        return True
    except Exception:
        return False


def deduplicate_by_domain(results: list[dict]) -> list[dict]:
    """Remove duplicate results that point to the same domain."""
    seen_domains: set[str] = set()
    unique = []

    for result in results:
        try:
            domain = urlparse(result["url"]).netloc.lower().replace("www.", "")
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                result["domain"] = domain
                unique.append(result)
        except Exception:
            continue

    return unique


def build_queries(profile: dict) -> list[str]:
    """Build search queries from an ideal customer profile."""
    industry = profile.get("industry", "")
    location = profile.get("location", "")
    company_size = profile.get("company_size", "")
    keywords = profile.get("keywords", [])

    queries = []

    # Primary query: industry + location + first two keywords
    kw_part = " ".join(keywords[:2]) if keywords else ""
    primary = f'"{industry}" companies "{location}" {kw_part}'.strip()
    if primary:
        queries.append(primary)

    # Size-targeted query
    if company_size:
        size_q = f'"{industry}" companies "{location}" "{company_size} employees"'
        queries.append(size_q)

    # Keyword-focused queries (one per keyword)
    for kw in keywords[:3]:
        kw_q = f'"{industry}" "{kw}" companies "{location}"'
        if kw_q not in queries:
            queries.append(kw_q)

    # Broad fallback
    if not queries:
        queries.append(f"companies {industry} {location}")

    return queries[:5]


def main() -> dict[str, Any]:
    """
    Main entry point. Searches for companies matching the profile.

    Returns:
        dict: Results containing company list, queries used, and counts.
    """
    parser = argparse.ArgumentParser(description="Search for companies matching a profile")
    parser.add_argument("--profile", type=str, help="JSON string of ideal customer profile")
    parser.add_argument("--queries", type=str, help="JSON array of search queries (overrides profile)")
    parser.add_argument("--max-results", type=int, default=100, help="Max total results")
    parser.add_argument("--output", default="output/search_results.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting company search")

    try:
        # Build or parse queries
        if args.queries:
            queries = json.loads(args.queries)
        elif args.profile:
            profile = json.loads(args.profile)
            queries = build_queries(profile)
        else:
            logger.error("Either --profile or --queries is required")
            return {"status": "error", "data": None, "message": "No input provided"}

        logger.info("Using %d search queries", len(queries))

        # Execute searches
        all_results: list[dict] = []
        for i, query in enumerate(queries):
            logger.info("Executing query %d/%d: %s", i + 1, len(queries), query)

            results = search_brave(query)
            if not results:
                results = search_fallback(query)

            all_results.extend(results)

            # Rate limiting between queries
            if i < len(queries) - 1:
                time.sleep(1.0)

        total_raw = len(all_results)
        logger.info("Raw results collected: %d", total_raw)

        # Filter out non-company domains
        company_results = [r for r in all_results if is_company_domain(r["url"])]
        logger.info("After domain filtering: %d", len(company_results))

        # Deduplicate by domain
        unique_results = deduplicate_by_domain(company_results)
        logger.info("After deduplication: %d", len(unique_results))

        # Trim to max_results
        final_results = unique_results[:args.max_results]

        result = {
            "status": "success",
            "data": {
                "results": final_results,
                "queries_used": queries,
                "total_found": total_raw,
                "total_after_filter": len(company_results),
                "total_unique": len(unique_results),
                "total_returned": len(final_results),
            },
            "message": f"Found {len(final_results)} unique company results",
        }

        # Write output
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Results written to %s", args.output)
        return result

    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON input: {e}"}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
