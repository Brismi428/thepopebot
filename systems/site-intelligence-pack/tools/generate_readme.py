#!/usr/bin/env python3
"""Generate human-readable README from intelligence pack."""

import sys
import json
import argparse
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_readme(pack: dict) -> str:
    """Generate README content from intelligence pack."""
    site = pack.get("site", {})
    domain = site.get("domain", "unknown")
    crawled_at = site.get("crawled_at_iso", "unknown")
    
    meta = pack.get("run_metadata", {})
    pages_crawled = meta.get("pages_crawled", 0)
    pages_extracted = len(pack.get("deep_extract_notes", {}).get("pages_extracted", 0))
    
    findings = pack.get("synthesized_findings", {})
    
    readme = f"""# Site Intelligence Pack: {domain}

Generated: {crawled_at}

## Summary

Crawled {pages_crawled} pages, extracted {pages_extracted} deep pages.

## Key Findings

### Positioning
"""
    
    # Add positioning claims
    pos_claims = findings.get("positioning", {}).get("claims", [])
    if pos_claims:
        for claim in pos_claims[:5]:
            readme += f"- {claim.get('claim', 'N/A')}\n"
    else:
        readme += "- No positioning insights extracted\n"
    
    readme += "\n### Offers and Pricing\n"
    
    # Add pricing claims
    pricing_claims = findings.get("offers_and_pricing", {}).get("claims", [])
    if pricing_claims:
        for claim in pricing_claims[:5]:
            readme += f"- {claim.get('claim', 'N/A')}\n"
    else:
        readme += "- No pricing information extracted\n"
    
    readme += "\n### Trust Signals\n"
    
    # Add trust signals
    trust_claims = findings.get("trust_signals", {}).get("claims", [])
    if trust_claims:
        for claim in trust_claims[:3]:
            readme += f"- {claim.get('claim', 'N/A')}\n"
    else:
        readme += "- No trust signals extracted\n"
    
    readme += "\n## Files\n\n"
    readme += f"- `inventory.json`: Full page inventory ({pages_crawled} pages)\n"
    readme += f"- `ranked_pages.json`: Relevance-ranked pages\n"
    readme += f"- `deep_extract.json`: Structured extractions ({pages_extracted} pages)\n"
    readme += f"- `site_intelligence_pack.json`: Final intelligence pack with evidence\n"
    
    return readme


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Intelligence pack JSON")
    parser.add_argument("--output", help="README output path")
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r') as f:
            pack = json.load(f)
        
        readme = generate_readme(pack)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(readme)
            logger.info(f"Wrote README to {args.output}")
        else:
            print(readme)
        
        return 0
    
    except Exception as e:
        logger.error(f"README generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
