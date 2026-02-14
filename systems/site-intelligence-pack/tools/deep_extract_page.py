#!/usr/bin/env python3
"""
Extract structured business data from a page with evidence tracking.

Uses Claude API to extract structured information with quoted evidence for every claim.
"""

import sys
import json
import argparse
import logging
import os
from typing import Dict
from anthropic import Anthropic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JSON Schema for extraction
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "extracted_entities": {
            "type": "object",
            "properties": {
                "company_name": {"type": ["string", "null"]},
                "product_names": {"type": "array", "items": {"type": "string"}},
                "audience": {"type": ["string", "null"]},
                "locations": {"type": "array", "items": {"type": "string"}},
                "contact_points": {"type": "array", "items": {"type": "string"}}
            }
        },
        "offers": {"type": "array"},
        "pricing": {"type": "object"},
        "how_it_works": {"type": "object"},
        "faq": {"type": "array"},
        "testimonials": {"type": "array"},
        "policies": {"type": "object"},
        "constraints": {"type": "object"},
        "evidence": {"type": "object"}
    },
    "required": ["summary"]
}


def deep_extract(url: str, content: str) -> Dict:
    """
    Extract structured data from a page with evidence tracking.
    
    Args:
        url: Page URL
        content: Page content (markdown or text)
    
    Returns:
        Dict with structured extraction and evidence index
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    client = Anthropic(api_key=api_key)
    
    system_prompt = """Extract structured business intelligence from the page content.

CRITICAL RULES:
1. Every extracted field MUST have an "evidence" array with evidence IDs (EV_001, EV_002, etc.)
2. Evidence excerpts MUST be 50-150 chars, directly quoted from content
3. If a field is not found, omit it or set to null (do not guess)
4. Mark pages requiring login or blocked by robots.txt in "constraints"
5. Return ONLY valid JSON

Generate evidence entries in this format:
{
  "EV_001": {
    "excerpt": "exact quote from content (50-150 chars)",
    "context": "surrounding context if needed"
  }
}

Structure your response as:
{
  "summary": "Brief page summary (2-3 sentences)",
  "extracted_entities": {
    "company_name": "Company name" or null,
    "product_names": ["Product 1", "Product 2"],
    "audience": "Target audience" or null,
    "locations": ["Location 1"],
    "contact_points": ["email@example.com"]
  },
  "offers": [
    {
      "name": "Offer name",
      "description": "Description",
      "price": "Price",
      "billing_terms": "Terms",
      "guarantees": "Guarantees",
      "evidence": ["EV_001", "EV_002"]
    }
  ],
  "pricing": {
    "model": "Pricing model",
    "tiers": [{"name": "Tier", "price": "Price"}],
    "evidence": ["EV_003"]
  },
  "how_it_works": {
    "steps": ["Step 1", "Step 2"],
    "evidence": ["EV_004"]
  },
  "faq": [
    {
      "q": "Question",
      "a": "Answer",
      "evidence": ["EV_005"]
    }
  ],
  "testimonials": [
    {
      "quote": "Testimonial quote",
      "name": "Person name",
      "source_context": "Title/Company",
      "evidence": ["EV_006"]
    }
  ],
  "policies": {
    "privacy": "Summary",
    "terms": "Summary",
    "refunds": "Summary",
    "cancellations": "Summary",
    "evidence": ["EV_007"]
  },
  "constraints": {
    "requires_login": false,
    "blocked_by_robots": false
  },
  "evidence": {
    "EV_001": {
      "excerpt": "Quoted text from content",
      "context": "Optional context"
    }
  }
}
"""
    
    # Truncate content if too long
    content_truncated = content[:50000] if len(content) > 50000 else content
    
    user_message = f"""URL: {url}

Content:
{content_truncated}"""
    
    try:
        logger.info(f"Extracting data from {url} ({len(content)} chars)")
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.0,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_message
            }]
        )
        
        raw_text = response.content[0].text.strip()
        
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        extracted = json.loads(raw_text)
        extracted["url"] = url
        extracted["canonical_url"] = url
        
        # Count evidence entries
        evidence_count = len(extracted.get("evidence", {}))
        logger.info(f"Extraction complete: {evidence_count} evidence entries")
        
        return extracted
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude: {e}")
        return {
            "url": url,
            "canonical_url": url,
            "summary": f"Extraction failed: invalid JSON response",
            "constraints": {"requires_login": False, "blocked_by_robots": False},
            "evidence": {}
        }
    
    except Exception as e:
        logger.error(f"Extraction failed for {url}: {e}", exc_info=True)
        return {
            "url": url,
            "canonical_url": url,
            "summary": f"Extraction failed: {str(e)}",
            "constraints": {"requires_login": False, "blocked_by_robots": False},
            "evidence": {}
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured data from a page"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Page URL"
    )
    parser.add_argument(
        "--content-file",
        help="File containing page content"
    )
    parser.add_argument(
        "--content",
        help="Page content as string"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Get content from file or argument
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        logger.error("Either --content-file or --content required")
        return 1
    
    try:
        result = deep_extract(args.url, content)
        
        output_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Wrote extraction to {args.output}")
        else:
            print(output_json)
        
        return 0
    
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
