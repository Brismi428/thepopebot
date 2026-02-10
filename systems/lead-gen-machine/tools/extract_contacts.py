"""
Extract Contacts — Uses Claude to extract structured contact info from scraped website content.

Inputs:
    - scraped_data (list[dict]): Companies with scraped_content field from scrape_websites.py

Outputs:
    - dict with:
        - enriched (list[dict]): Companies with extracted structured contact fields
        - extraction_count (int): Number of successful extractions

Usage:
    python extract_contacts.py --input output/scraped_data.json --output output/enriched_data.json

Environment Variables:
    - ANTHROPIC_API_KEY: Anthropic API key for Claude (required)
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract the following information from this company's website content. Return ONLY valid JSON with these fields:

{
  "company_name": "Official company name",
  "industry": "Primary industry/sector",
  "company_size": "Employee count or range if mentioned (e.g., '50-200', '500+', 'unknown')",
  "location": "Headquarters or primary location (city, state/country)",
  "description": "One-sentence description of what the company does",
  "email": "General contact or sales email (or empty string if not found)",
  "phone": "Main phone number (or empty string if not found)",
  "technologies": ["Key technologies, products, or services mentioned"]
}

Rules:
- Only include information explicitly found in the content
- Use empty string "" for fields you cannot determine
- Use "unknown" for company_size if not mentioned
- Keep description to one sentence
- For email/phone, prefer sales or general contact over personal addresses
- Return ONLY the JSON object, no markdown fences or commentary"""


def extract_with_claude(content: str, url: str) -> dict:
    """Use Claude API to extract structured data from scraped content."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Truncate content to avoid excessive token usage
        truncated = content[:8000]

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.0,
            system="You are a data extraction assistant. Extract structured company information from website content. Return only valid JSON.",
            messages=[{
                "role": "user",
                "content": f"Website URL: {url}\n\nWebsite content:\n{truncated}\n\n{EXTRACTION_PROMPT}",
            }],
        )

        raw = msg.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw)
        return {"success": True, "data": parsed}

    except ImportError:
        return {"success": False, "error": "anthropic package not installed"}
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Claude response as JSON: %s", e)
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error("Claude extraction failed: %s", e)
        return {"success": False, "error": str(e)}


def extract_with_regex(content: str, url: str) -> dict:
    """Fallback regex-based extraction for when Claude API is unavailable."""
    data = {
        "company_name": "",
        "industry": "unknown",
        "company_size": "unknown",
        "location": "",
        "description": "",
        "email": "",
        "phone": "",
        "technologies": [],
    }

    # Try to extract email
    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', content)
    # Filter out common non-contact emails
    filtered_emails = [e for e in emails if not any(
        x in e.lower() for x in ["noreply", "no-reply", "unsubscribe", "privacy", "example.com"]
    )]
    if filtered_emails:
        data["email"] = filtered_emails[0]

    # Try to extract phone numbers
    phones = re.findall(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}', content)
    valid_phones = [p.strip() for p in phones if len(re.sub(r'\D', '', p)) >= 10]
    if valid_phones:
        data["phone"] = valid_phones[0]

    return data


def main() -> dict[str, Any]:
    """
    Main entry point. Extracts structured contact info from scraped data.

    Returns:
        dict: Enriched company data with extracted contacts.
    """
    parser = argparse.ArgumentParser(description="Extract contacts from scraped websites")
    parser.add_argument("--input", required=True, help="Path to scraped data JSON")
    parser.add_argument("--output", default="output/enriched_data.json", help="Output file path")
    args = parser.parse_args()

    logger.info("Starting contact extraction")

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            scraped_data = json.load(f)

        companies = scraped_data.get("data", {}).get("scraped", [])
        if not companies:
            logger.warning("No companies to extract from")
            return {"status": "success", "data": {"enriched": [], "extraction_count": 0},
                    "message": "No companies to process"}

        logger.info("Extracting contacts from %d companies", len(companies))

        enriched = []
        extraction_count = 0

        for i, company in enumerate(companies):
            url = company.get("url", "")
            content = company.get("scraped_content", "")
            subpage_content = company.get("subpage_content", "")

            # Combine main page and subpage content
            full_content = content
            if subpage_content:
                full_content += "\n\n" + subpage_content

            logger.info("Extracting %d/%d: %s", i + 1, len(companies), url)

            enriched_company = {
                "url": url,
                "domain": company.get("domain", ""),
                "search_title": company.get("title", ""),
                "search_snippet": company.get("snippet", ""),
                "scrape_status": company.get("scrape_status", "unknown"),
                "scraped_at": company.get("scraped_at", ""),
            }

            if full_content and company.get("scrape_status") == "success":
                # Try Claude extraction
                result = extract_with_claude(full_content, url)

                if result["success"]:
                    extracted = result["data"]
                    enriched_company.update(extracted)
                    enriched_company["extraction_status"] = "full"
                    extraction_count += 1
                else:
                    # Fallback to regex
                    logger.info("Using regex fallback for %s", url)
                    regex_data = extract_with_regex(full_content, url)
                    enriched_company.update(regex_data)
                    enriched_company["extraction_status"] = "partial"

                # Rate limit between Claude API calls
                if i < len(companies) - 1:
                    time.sleep(0.5)
            else:
                # No content available, use search snippet
                enriched_company["company_name"] = company.get("title", "")
                enriched_company["description"] = company.get("snippet", "")
                enriched_company["industry"] = "unknown"
                enriched_company["company_size"] = "unknown"
                enriched_company["location"] = ""
                enriched_company["email"] = ""
                enriched_company["phone"] = ""
                enriched_company["technologies"] = []
                enriched_company["extraction_status"] = "snippet_only"

            enriched.append(enriched_company)

        result = {
            "status": "success",
            "data": {
                "enriched": enriched,
                "extraction_count": extraction_count,
                "total_processed": len(enriched),
            },
            "message": f"Extracted contacts from {extraction_count}/{len(enriched)} companies",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Enriched data written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
