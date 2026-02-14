#!/usr/bin/env python3
"""
Synthesize findings from deep extractions into final intelligence pack.

Combines all extractions, builds evidence index, generates synthesized insights.
"""

import sys
import json
import argparse
import logging
import os
from datetime import datetime
from typing import Dict, List
from anthropic import Anthropic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def synthesize(
    domain: str,
    robots_data: Dict,
    inventory: List[Dict],
    ranked_pages: List[Dict],
    deep_extract: Dict,
    run_metadata: Dict
) -> Dict:
    """
    Synthesize all data into final intelligence pack.
    
    Returns complete site intelligence pack with evidence index.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    client = Anthropic(api_key=api_key)
    
    # Build evidence index from all extractions
    evidence_index = {}
    for page in deep_extract.get("pages", []):
        page_evidence = page.get("evidence", {})
        for ev_id, ev_data in page_evidence.items():
            evidence_index[ev_id] = {
                "url": page.get("url"),
                "excerpt": ev_data.get("excerpt", ""),
                "page_title": page.get("title", ""),
                "extracted_at_iso": datetime.utcnow().isoformat() + "Z"
            }
    
    logger.info(f"Built evidence index with {len(evidence_index)} entries")
    
    # Prepare synthesis prompt
    synthesis_context = json.dumps({
        "domain": domain,
        "page_count": len(inventory),
        "ranked_pages": ranked_pages[:20],  # Top 20
        "deep_extractions": deep_extract.get("pages", [])
    }, indent=2)
    
    system_prompt = """Synthesize business intelligence findings across 5 dimensions.

Analyze the provided page extractions and generate synthesized insights in these areas:
1. Positioning: target market, value proposition, competitive differentiation
2. Offers and pricing: product/service offerings, pricing models, tiers
3. Customer journey: how customers discover, evaluate, purchase, onboard
4. Trust signals: testimonials, guarantees, certifications, social proof
5. Compliance and policies: privacy, terms, refunds, security

CRITICAL: Every claim MUST reference evidence IDs from the extractions.
Identify unknowns and gaps where information was not found.

Return JSON in this format:
{
  "positioning": {
    "claims": [
      {
        "id": "POS_001",
        "claim": "Your insight here",
        "evidence": ["EV_015", "EV_022"]
      }
    ]
  },
  "offers_and_pricing": { "claims": [] },
  "customer_journey": { "claims": [] },
  "trust_signals": { "claims": [] },
  "compliance_and_policies": { "claims": [] },
  "unknowns_and_gaps": [
    "Gap: No pricing information found",
    "Gap: No customer testimonials available"
  ]
}
"""
    
    try:
        logger.info("Synthesizing findings via Claude...")
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.1,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Synthesize findings for {domain}:\n\n{synthesis_context}"
            }]
        )
        
        raw_text = response.content[0].text.strip()
        
        # Strip code fences
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        synthesized_findings = json.loads(raw_text)
        
    except Exception as e:
        logger.error(f"Synthesis failed, using minimal structure: {e}")
        synthesized_findings = {
            "positioning": {"claims": []},
            "offers_and_pricing": {"claims": []},
            "customer_journey": {"claims": []},
            "trust_signals": {"claims": []},
            "compliance_and_policies": {"claims": []},
            "unknowns_and_gaps": [f"Synthesis error: {str(e)}"]
        }
    
    # Build final pack
    site_pack = {
        "site": {
            "target_url": f"https://{domain}",
            "domain": domain,
            "crawled_at_iso": datetime.utcnow().isoformat() + "Z",
            "robots": robots_data
        },
        "inventory": inventory,
        "ranked_pages": ranked_pages,
        "deep_extract_notes": {
            "pages_extracted": len(deep_extract.get("pages", [])),
            "evidence_entries": len(evidence_index)
        },
        "synthesized_findings": synthesized_findings,
        "evidence_index": evidence_index,
        "run_metadata": run_metadata
    }
    
    logger.info("Synthesis complete")
    
    return site_pack


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Synthesize findings into intelligence pack"
    )
    parser.add_argument("--domain", required=True)
    parser.add_argument("--robots-file", required=True)
    parser.add_argument("--inventory-file", required=True)
    parser.add_argument("--ranked-file", required=True)
    parser.add_argument("--deep-extract-file", required=True)
    parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    try:
        with open(args.robots_file, 'r') as f:
            robots_data = json.load(f)
        with open(args.inventory_file, 'r') as f:
            inventory = json.load(f)
        with open(args.ranked_file, 'r') as f:
            ranked_pages = json.load(f)
        with open(args.deep_extract_file, 'r') as f:
            deep_extract = json.load(f)
        
        run_metadata = {
            "max_pages": 200,
            "pages_crawled": len(inventory),
            "pages_extracted": len(deep_extract.get("pages", [])),
            "errors": []
        }
        
        result = synthesize(
            args.domain,
            robots_data,
            inventory,
            ranked_pages,
            deep_extract,
            run_metadata
        )
        
        output_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Wrote site pack to {args.output}")
        else:
            print(output_json)
        
        return 0
    
    except Exception as e:
        logger.error(f"Synthesis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
