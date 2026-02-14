#!/usr/bin/env python3
"""
Rank pages by relevance using path keywords and semantic analysis.

Scoring dimensions:
1. Path keywords (pricing, faq, about, contact, etc.)
2. Title keywords
3. Content preview analysis
"""

import sys
import json
import argparse
import logging
import re
from typing import List, Dict, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Category priority (higher = more important)
CATEGORIES = {
    "offers_and_pricing": 100,
    "how_it_works": 80,
    "policies": 70,
    "testimonials": 65,
    "about": 60,
    "faq": 55,
    "contact": 50,
    "blog": 20,
    "other": 10
}

# Path keyword scoring
PATH_KEYWORDS = {
    "offers_and_pricing": ["pricing", "plans", "price", "cost", "subscription", "buy", "purchase", "offers", "deal"],
    "how_it_works": ["how-it-works", "features", "product", "solutions", "platform", "technology"],
    "policies": ["privacy", "terms", "policy", "legal", "compliance", "security", "gdpr"],
    "testimonials": ["testimonial", "review", "case-stud", "customer", "success", "story"],
    "about": ["about", "company", "team", "mission", "vision", "who-we-are"],
    "faq": ["faq", "help", "support", "question", "answer"],
    "contact": ["contact", "reach", "sales", "demo", "quote"],
    "blog": ["blog", "news", "article", "post"]
}

# Title keyword scoring
TITLE_KEYWORDS = {
    "offers_and_pricing": ["pricing", "plans", "cost", "buy"],
    "how_it_works": ["features", "how it works", "product"],
    "policies": ["privacy", "terms"],
    "testimonials": ["testimonials", "reviews", "case studies"],
    "about": ["about us", "our team", "company"],
    "faq": ["faq", "frequently asked"],
    "contact": ["contact", "get in touch"]
}


def categorize_page(url: str, title: str) -> Tuple[str, int, List[str]]:
    """
    Categorize a page and assign a relevance score.
    
    Returns:
        (category, score, reasons)
    """
    url_lower = url.lower()
    title_lower = title.lower()
    
    reasons = []
    max_score = 0
    best_category = "other"
    
    # Check path keywords
    for category, keywords in PATH_KEYWORDS.items():
        for keyword in keywords:
            if keyword in url_lower:
                score = CATEGORIES[category]
                if score > max_score:
                    max_score = score
                    best_category = category
                reasons.append(f"Path contains '{keyword}'")
    
    # Check title keywords (boost score slightly)
    for category, keywords in TITLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                score = CATEGORIES[category] + 10
                if score > max_score:
                    max_score = score
                    best_category = category
                reasons.append(f"Title contains '{keyword}'")
    
    # Default score if no matches
    if max_score == 0:
        max_score = CATEGORIES["other"]
    
    return best_category, max_score, reasons


def rank_pages(inventory: List[Dict]) -> List[Dict]:
    """
    Rank pages by relevance.
    
    Args:
        inventory: List of inventory dicts
    
    Returns:
        List of ranked page dicts sorted by score (descending)
    """
    logger.info(f"Ranking {len(inventory)} pages")
    
    ranked = []
    
    for item in inventory:
        url = item.get("canonical_url", item.get("url", ""))
        title = item.get("title", "")
        
        category, score, reasons = categorize_page(url, title)
        
        ranked.append({
            "url": url,
            "canonical_url": url,
            "rank": score,
            "reasons": reasons if reasons else ["Default scoring"],
            "category": category
        })
    
    # Sort by rank (descending)
    ranked.sort(key=lambda x: x["rank"], reverse=True)
    
    # Assign final rank numbers
    for i, item in enumerate(ranked, 1):
        item["rank"] = i
    
    # Log category distribution
    category_counts = {}
    for item in ranked:
        cat = item["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    logger.info(f"Category distribution: {json.dumps(category_counts, indent=2)}")
    
    return ranked


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Rank pages by relevance"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON file with inventory"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        
        result = rank_pages(inventory)
        
        output_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Wrote ranked pages to {args.output}")
        else:
            print(output_json)
        
        return 0
    
    except Exception as e:
        logger.error(f"Failed to rank pages: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
