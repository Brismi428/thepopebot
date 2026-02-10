"""
Enrich Leads — Enriches leads with company data, decision-maker contacts, tech stack,
and pain signals via Apollo.io, Hunter.io, Brave Search, and Claude APIs.

Inputs:
    - ingested_leads (list[dict]): Validated leads from ingest_leads.py

Outputs:
    - dict with:
        - enriched (list[dict]): Leads with enrichment data added
        - stats (dict): Enrichment success/partial/failed counts

Usage:
    python enrich_leads.py --input output/ingested_leads.json --output output/enriched_leads.json

Environment Variables:
    - APOLLO_API_KEY: Apollo.io API key (primary enrichment source)
    - HUNTER_API_KEY: Hunter.io API key (email verification/discovery)
    - BRAVE_API_KEY: Brave Search API key (company research)
    - ANTHROPIC_API_KEY: Claude API key (pain signal analysis)
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any
from urllib.parse import quote_plus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_http_client():
    """Get an HTTP client, preferring httpx over requests."""
    try:
        import httpx
        return httpx, "httpx"
    except ImportError:
        pass
    try:
        import requests
        return requests, "requests"
    except ImportError:
        raise ImportError("Neither httpx nor requests is installed. Install one: pip install httpx")


def enrich_via_apollo(company_name: str, domain: str | None, http_client: Any, client_type: str) -> dict:
    """Enrich a company via Apollo.io Organization Enrichment API."""
    api_key = os.environ.get("APOLLO_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "APOLLO_API_KEY not set", "source": "apollo"}

    try:
        headers = {
            "Cache-Control": "no-cache",
            "x-api-key": api_key,
        }

        # Use Organization Enrichment endpoint (GET, domain-based)
        enrich_url = "https://api.apollo.io/api/v1/organizations/enrich"
        params = {}
        if domain:
            clean_domain = domain.split("/")[0]
            params["domain"] = clean_domain
        else:
            # Without domain, use company name for search fallback
            params["organization_name"] = company_name

        if client_type == "httpx":
            resp = http_client.get(enrich_url, headers=headers, params=params, timeout=15)
        else:
            resp = http_client.get(enrich_url, headers=headers, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json()

        org = data.get("organization", {})
        if not org:
            return {"success": False, "error": "No organization data returned", "source": "apollo"}

        # Search for people at this company via people search
        people = []
        people_url = "https://api.apollo.io/api/v1/mixed_people/search"
        people_headers = {**headers, "Content-Type": "application/json"}
        people_payload = {
            "q_organization_name": company_name,
            "per_page": 5,
            "person_titles": ["CEO", "CTO", "VP Operations", "Head of Operations",
                              "Director of Operations", "COO", "VP Engineering",
                              "Head of Growth", "CMO", "VP Marketing"],
        }

        try:
            if client_type == "httpx":
                people_resp = http_client.post(people_url, json=people_payload, headers=people_headers, timeout=15)
            else:
                people_resp = http_client.post(people_url, json=people_payload, headers=people_headers, timeout=15)

            if people_resp.status_code == 200:
                people_data = people_resp.json()
                for person in people_data.get("people", [])[:5]:
                    people.append({
                        "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                        "title": person.get("title", ""),
                        "email": person.get("email", ""),
                        "linkedin_url": person.get("linkedin_url", ""),
                    })
        except Exception as pe:
            logger.info("  Apollo people search unavailable: %s", pe)

        return {
            "success": True,
            "source": "apollo",
            "data": {
                "company_size": org.get("estimated_num_employees", "unknown"),
                "revenue_estimate": org.get("annual_revenue_printed", "unknown"),
                "tech_stack": org.get("technology_names", [])[:20],
                "industry": org.get("industry", "unknown"),
                "location": f"{org.get('city', '')}, {org.get('state', '')} {org.get('country', '')}".strip(", "),
                "social_profiles": {
                    "linkedin": org.get("linkedin_url", ""),
                    "twitter": org.get("twitter_url", ""),
                    "crunchbase": org.get("crunchbase_url", ""),
                },
                "decision_makers": people,
                "founded_year": org.get("founded_year", ""),
                "description": org.get("short_description", ""),
            },
        }

    except Exception as e:
        logger.warning("Apollo enrichment failed for %s: %s", company_name, e)
        return {"success": False, "error": str(e), "source": "apollo"}


def enrich_via_hunter(domain: str, http_client: Any, client_type: str) -> dict:
    """Find and verify emails via Hunter.io API."""
    api_key = os.environ.get("HUNTER_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "HUNTER_API_KEY not set", "source": "hunter"}

    if not domain:
        return {"success": False, "error": "No domain provided", "source": "hunter"}

    try:
        url = f"https://api.hunter.io/v2/domain-search?domain={quote_plus(domain)}&api_key={api_key}&limit=5"

        if client_type == "httpx":
            resp = http_client.get(url, timeout=15)
        else:
            resp = http_client.get(url, timeout=15)

        resp.raise_for_status()
        data = resp.json().get("data", {})

        emails = []
        for email_entry in data.get("emails", []):
            emails.append({
                "name": f"{email_entry.get('first_name', '')} {email_entry.get('last_name', '')}".strip(),
                "email": email_entry.get("value", ""),
                "title": email_entry.get("position", ""),
                "confidence": email_entry.get("confidence", 0),
            })

        return {
            "success": True,
            "source": "hunter",
            "data": {
                "emails": emails,
                "organization": data.get("organization", ""),
                "pattern": data.get("pattern", ""),
            },
        }

    except Exception as e:
        logger.warning("Hunter enrichment failed for %s: %s", domain, e)
        return {"success": False, "error": str(e), "source": "hunter"}


def find_email_via_hunter(first_name: str, last_name: str, domain: str, http_client: Any, client_type: str) -> dict:
    """Find a specific person's email via Hunter.io Email Finder API."""
    api_key = os.environ.get("HUNTER_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "HUNTER_API_KEY not set", "source": "hunter_finder"}

    if not domain or not (first_name or last_name):
        return {"success": False, "error": "Missing name or domain", "source": "hunter_finder"}

    try:
        params = {
            "domain": domain,
            "api_key": api_key,
        }
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name

        url = "https://api.hunter.io/v2/email-finder"

        if client_type == "httpx":
            resp = http_client.get(url, params=params, timeout=15)
        else:
            resp = http_client.get(url, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json().get("data", {})

        email = data.get("email", "")
        confidence = data.get("confidence", 0)

        if email and confidence >= 70:
            return {
                "success": True,
                "source": "hunter_finder",
                "data": {
                    "email": email,
                    "confidence": confidence,
                    "first_name": data.get("first_name", first_name),
                    "last_name": data.get("last_name", last_name),
                },
            }

        return {"success": False, "error": f"Low confidence ({confidence})", "source": "hunter_finder"}

    except Exception as e:
        logger.warning("Hunter email finder failed for %s %s: %s", first_name, last_name, e)
        return {"success": False, "error": str(e), "source": "hunter_finder"}


def research_via_brave(company_name: str, http_client: Any, client_type: str) -> dict:
    """Research a company via Brave Search for blog posts, job listings, and news."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "BRAVE_API_KEY not set", "source": "brave"}

    try:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        }
        results = {
            "blog_posts": [],
            "job_listings": [],
            "funding_news": [],
            "general_info": [],
        }

        # Search for recent blog posts
        queries = [
            (f'"{company_name}" blog OR article', "blog_posts"),
            (f'"{company_name}" hiring OR "job opening" OR careers', "job_listings"),
            (f'"{company_name}" funding OR raised OR investment', "funding_news"),
        ]

        for query, category in queries:
            url = "https://api.search.brave.com/res/v1/web/search"
            params = {"q": query, "count": 5, "freshness": "pm"}

            if client_type == "httpx":
                resp = http_client.get(url, headers=headers, params=params, timeout=15)
            else:
                resp = http_client.get(url, headers=headers, params=params, timeout=15)

            if resp.status_code == 200:
                for item in resp.json().get("web", {}).get("results", []):
                    results[category].append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("description", ""),
                    })

            time.sleep(1)  # Rate limit: 1 req/sec

        return {"success": True, "source": "brave", "data": results}

    except Exception as e:
        logger.warning("Brave research failed for %s: %s", company_name, e)
        return {"success": False, "error": str(e), "source": "brave"}


def analyze_pain_signals(company_name: str, enrichment_data: dict) -> list[str]:
    """Use Claude to analyze enrichment data for pain signals."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Build context from enrichment data
        context_parts = [f"Company: {company_name}"]

        tech_stack = enrichment_data.get("tech_stack", [])
        if tech_stack:
            context_parts.append(f"Tech stack: {', '.join(tech_stack[:15])}")

        job_listings = enrichment_data.get("job_listings", [])
        if job_listings:
            context_parts.append("Recent job listings:")
            for job in job_listings[:5]:
                context_parts.append(f"  - {job.get('title', '')}: {job.get('description', '')[:100]}")

        blog_posts = enrichment_data.get("blog_posts", [])
        if blog_posts:
            context_parts.append("Recent blog posts:")
            for post in blog_posts[:3]:
                context_parts.append(f"  - {post.get('title', '')}")

        context = "\n".join(context_parts)

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            temperature=0.0,
            system="You are a B2B sales intelligence analyst. Identify pain signals that suggest a company needs automation or operational improvement. Return a JSON array of short signal descriptions.",
            messages=[{
                "role": "user",
                "content": f"Analyze this company data for pain signals related to manual processes, operational inefficiency, or need for automation:\n\n{context}\n\nReturn ONLY a JSON array of strings, each describing a detected pain signal. If no signals found, return an empty array [].",
            }],
        )

        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        signals = json.loads(raw)
        return signals if isinstance(signals, list) else []

    except ImportError:
        logger.warning("anthropic package not installed, skipping pain signal analysis")
        return []
    except Exception as e:
        logger.warning("Pain signal analysis failed for %s: %s", company_name, e)
        return []


def extract_domain(lead: dict) -> str | None:
    """Extract domain from a lead's website URL or company name."""
    website = lead.get("website", "")
    if website:
        # Strip protocol and path
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        return domain.lower()
    return None


def enrich_single_lead(lead: dict, http_client: Any, client_type: str) -> dict:
    """Enrich a single lead using all available sources."""
    company_name = lead.get("company_name", "")
    domain = extract_domain(lead)
    enriched = {**lead}  # Start with original data

    enrichment_data = {}
    enrichment_sources = []

    # Apollo enrichment (primary)
    apollo_result = enrich_via_apollo(company_name, domain, http_client, client_type)
    if apollo_result["success"]:
        enrichment_data.update(apollo_result["data"])
        enrichment_sources.append("apollo")
        logger.info("  Apollo: success")
    else:
        logger.info("  Apollo: %s", apollo_result.get("error", "failed"))

    time.sleep(1)  # Rate limit

    # Hunter enrichment (email verification)
    if domain:
        hunter_result = enrich_via_hunter(domain, http_client, client_type)
        if hunter_result["success"]:
            # Merge Hunter contacts with Apollo decision_makers
            existing_makers = enrichment_data.get("decision_makers", [])
            existing_emails = {dm.get("email", "").lower() for dm in existing_makers}

            for hunter_contact in hunter_result["data"].get("emails", []):
                if hunter_contact["email"].lower() not in existing_emails:
                    existing_makers.append({
                        "name": hunter_contact.get("name", ""),
                        "title": hunter_contact.get("title", ""),
                        "email": hunter_contact.get("email", ""),
                        "linkedin_url": "",
                    })
            enrichment_data["decision_makers"] = existing_makers
            enrichment_sources.append("hunter")
            logger.info("  Hunter: success")
        else:
            logger.info("  Hunter: %s", hunter_result.get("error", "failed"))

        time.sleep(1)

    # Hunter Email Finder — resolve emails for contacts with names but no email
    if domain and os.environ.get("HUNTER_API_KEY", ""):
        makers = enrichment_data.get("decision_makers", [])
        found_any = False
        for dm in makers:
            if dm.get("name") and not dm.get("email"):
                name_parts = dm["name"].split(None, 1)
                first = name_parts[0] if name_parts else ""
                last = name_parts[1] if len(name_parts) > 1 else ""
                if first and last:
                    finder_result = find_email_via_hunter(first, last, domain, http_client, client_type)
                    if finder_result["success"]:
                        dm["email"] = finder_result["data"]["email"]
                        found_any = True
                        logger.info("    Hunter finder: found email for %s", dm["name"])
                    time.sleep(0.5)
        if found_any and "hunter_finder" not in enrichment_sources:
            enrichment_sources.append("hunter_finder")

    # Brave Search research
    brave_result = research_via_brave(company_name, http_client, client_type)
    if brave_result["success"]:
        enrichment_data["blog_posts"] = brave_result["data"].get("blog_posts", [])
        enrichment_data["job_listings"] = brave_result["data"].get("job_listings", [])
        enrichment_data["funding_news"] = brave_result["data"].get("funding_news", [])
        enrichment_sources.append("brave")
        logger.info("  Brave: success")
    else:
        logger.info("  Brave: %s", brave_result.get("error", "failed"))

    # Pain signal analysis via Claude
    pain_signals = analyze_pain_signals(company_name, enrichment_data)
    enrichment_data["pain_signals"] = pain_signals
    if pain_signals:
        enrichment_sources.append("claude_analysis")
        logger.info("  Pain signals: %d detected", len(pain_signals))

    # Merge enrichment data into lead
    enriched.update(enrichment_data)
    enriched["enrichment_sources"] = enrichment_sources
    enriched["enrichment_status"] = "full" if len(enrichment_sources) >= 2 else ("partial" if enrichment_sources else "failed")

    return enriched


def main() -> dict[str, Any]:
    """
    Main entry point. Enriches leads via multiple APIs.

    Returns:
        dict: Enriched lead data.
    """
    parser = argparse.ArgumentParser(description="Enrich leads with company data and contacts")
    parser.add_argument("--input", required=True, help="Path to ingested leads JSON")
    parser.add_argument("--output", default="output/enriched_leads.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting lead enrichment")

    try:
        # Load ingested leads
        with open(args.input, "r", encoding="utf-8") as f:
            ingested = json.load(f)

        leads = ingested.get("data", {}).get("leads", [])
        if not leads:
            logger.warning("No leads to enrich")
            return {"status": "success", "data": {"enriched": [], "stats": {}},
                    "message": "No leads to enrich"}

        logger.info("Enriching %d leads", len(leads))

        # Initialize HTTP client
        http_client, client_type = _get_http_client()
        logger.info("Using HTTP client: %s", client_type)

        enriched_leads = []
        stats = {"full": 0, "partial": 0, "failed": 0}

        for i, lead in enumerate(leads):
            company = lead.get("company_name", "unknown")
            logger.info("Enriching %d/%d: %s", i + 1, len(leads), company)

            enriched = enrich_single_lead(lead, http_client, client_type)
            enriched_leads.append(enriched)

            status = enriched.get("enrichment_status", "failed")
            stats[status] = stats.get(status, 0) + 1

        result = {
            "status": "success",
            "data": {
                "enriched": enriched_leads,
                "total_processed": len(enriched_leads),
                "stats": stats,
            },
            "message": f"Enriched {len(enriched_leads)} leads: {stats['full']} full, {stats['partial']} partial, {stats['failed']} failed",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Enriched data written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON: {e}"}
    except ImportError as e:
        logger.error("Missing dependency: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
