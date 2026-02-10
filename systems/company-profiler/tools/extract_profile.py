"""
Extract Profile — Processes scraped website content into structured company profile data.

Uses Claude (via the Anthropic API) to analyze scraped text and extract key
business information into a structured JSON format.

Inputs:
    - scraped_data (str): Path to the scraped content JSON from scrape_website.py

Outputs:
    - Structured company profile JSON with confidence scores

Usage:
    python extract_profile.py --scraped-data scraped.json --output profile.json

Environment Variables:
    - ANTHROPIC_API_KEY: Required for Claude API calls
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

EXTRACTION_PROMPT = """Analyze the following scraped website content and extract a structured company profile.

For each field, provide your best extraction and a confidence level (high, medium, low, none).

Extract these fields:
- company_name: Official company name
- description: What the company does (1-2 sentences)
- industry: Primary industry/sector
- products_services: List of main product or service offerings
- target_market: Who they sell to (B2B, B2C, enterprise, SMB, developer, consumer, etc.)
- pricing_model: How they charge (free, freemium, subscription, usage-based, enterprise/sales, one-time, etc.)
- team_size_signals: Any indicators of team size (number of job postings, "team of X", headcount mentions)
- tech_stack: Technologies mentioned (programming languages, frameworks, cloud providers, tools)
- founded: Year founded if mentioned
- location: HQ location if mentioned
- social_links: Any social media or professional profile links found

Return ONLY valid JSON in this exact format:
{
  "company_name": "...",
  "description": "...",
  "industry": "...",
  "products_services": ["..."],
  "target_market": "...",
  "pricing_model": "...",
  "team_size_signals": "...",
  "tech_stack": ["..."],
  "founded": "...",
  "location": "...",
  "social_links": {"linkedin": "...", "twitter": "...", "github": "..."},
  "confidence": {
    "company_name": "high",
    "description": "high",
    "industry": "medium",
    "products_services": "high",
    "target_market": "medium",
    "pricing_model": "low",
    "team_size_signals": "low",
    "tech_stack": "medium",
    "founded": "none",
    "location": "medium",
    "social_links": "medium"
  }
}

Website content:
"""


def extract_with_anthropic(content: str, api_key: str) -> dict[str, Any]:
    """Use Anthropic Claude API to extract structured data from website content."""
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed")
        return {"error": "anthropic package not installed. Run: pip install anthropic"}

    client = anthropic.Anthropic(api_key=api_key)

    # Truncate content if too long
    max_content = 15000
    if len(content) > max_content:
        content = content[:max_content] + "\n\n[Content truncated]"

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT + content,
            }
        ],
    )

    response_text = message.content[0].text

    # Parse JSON from response
    # Handle cases where the response might have markdown code fences
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())


def extract_basic(content: str) -> dict[str, Any]:
    """Basic extraction without AI — pattern matching fallback."""
    logger.warning("Using basic extraction (no AI). Results will be limited.")

    profile = {
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
        "confidence": {k: "none" for k in [
            "company_name", "description", "industry", "products_services",
            "target_market", "pricing_model", "team_size_signals",
            "tech_stack", "founded", "location", "social_links",
        ]},
    }

    # Try to extract title as company name (first non-empty line)
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if lines:
        profile["company_name"] = lines[0][:100]
        profile["confidence"]["company_name"] = "low"

    return profile


def main() -> dict[str, Any]:
    """Extract a company profile from scraped website content."""
    parser = argparse.ArgumentParser(description="Extract company profile from scraped content")
    parser.add_argument("--scraped-data", required=True, help="Path to scraped content JSON")
    parser.add_argument("--output", default="profile.json", help="Output profile JSON path")
    args = parser.parse_args()

    logger.info("Extracting profile from: %s", args.scraped_data)

    try:
        with open(args.scraped_data, "r", encoding="utf-8") as f:
            scraped = json.load(f)

        # Combine all scraped page content
        all_content = []
        for page_path, page_data in scraped.get("pages", {}).items():
            content = page_data.get("content", "")
            if content:
                all_content.append(f"=== Page: {page_path} ===\n{content}")

        combined_content = "\n\n".join(all_content)

        if not combined_content:
            logger.error("No content to extract from")
            return {"status": "error", "data": None, "message": "No scraped content available"}

        # Extract using Anthropic API if available
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            logger.info("Using Anthropic Claude for extraction")
            profile = extract_with_anthropic(combined_content, api_key)
        else:
            logger.warning("No ANTHROPIC_API_KEY — using basic extraction")
            profile = extract_basic(combined_content)

        # Add metadata
        profile["url"] = scraped.get("base_url", "")
        profile["scraped_at"] = scraped.get("scraped_at", "")
        profile["scraper"] = scraped.get("scraper", "unknown")

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        logger.info("Profile extracted and written to %s", args.output)
        return {"status": "success", "data": profile}

    except json.JSONDecodeError as e:
        logger.error("Failed to parse scraped data: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON: {e}"}
    except Exception as e:
        logger.error("Extraction failed: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
