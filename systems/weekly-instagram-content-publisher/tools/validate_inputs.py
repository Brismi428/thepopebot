#!/usr/bin/env python3
"""
Validate and parse workflow inputs for Instagram content generation.

Inputs:
- brand_profile_path: Path to brand profile JSON file
- weekly_theme: Content theme for the week
- post_plan: JSON string with post counts and types
- reference_links: JSON array of reference URLs (optional)
- publishing_mode: auto_publish or content_pack_only

Outputs: validated_inputs.json with parsed and validated data
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def validate_brand_profile(profile: Dict[str, Any]) -> None:
    """Validate brand profile has all required fields."""
    required = [
        "brand_name", "tone", "target_audience", "products",
        "banned_topics", "prohibited_claims", "preferred_cta",
        "emoji_style", "hashtag_preferences"
    ]
    missing = [f for f in required if f not in profile]
    if missing:
        raise ValueError(f"Missing required fields in brand_profile: {', '.join(missing)}")
    
    # Validate hashtag_preferences structure
    if "hashtag_preferences" in profile:
        hp = profile["hashtag_preferences"]
        if not isinstance(hp, dict):
            raise ValueError("hashtag_preferences must be a dictionary")
        if "count" not in hp:
            raise ValueError("hashtag_preferences missing 'count' field")
    
    logging.info(f"Brand profile validated: {profile['brand_name']}")


def validate_post_plan(plan: Dict[str, Any]) -> None:
    """Validate post plan structure."""
    valid_types = ["reels", "carousels", "single_images", "stories"]
    has_posts = any(plan.get(t, 0) > 0 for t in valid_types)
    
    if not has_posts:
        raise ValueError("post_plan must specify at least one post type with count > 0")
    
    total = sum(plan.get(t, 0) for t in valid_types)
    logging.info(f"Post plan validated: {total} total posts")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Instagram content generation inputs"
    )
    parser.add_argument(
        "--brand-profile-path",
        required=True,
        help="Path to brand profile JSON file"
    )
    parser.add_argument(
        "--weekly-theme",
        required=True,
        help="Weekly content theme"
    )
    parser.add_argument(
        "--post-plan",
        required=True,
        help="JSON string with post counts and types"
    )
    parser.add_argument(
        "--reference-links",
        default="[]",
        help="JSON array of reference URLs (optional)"
    )
    parser.add_argument(
        "--publishing-mode",
        required=True,
        choices=["auto_publish", "content_pack_only"],
        help="Publishing mode"
    )
    parser.add_argument(
        "--output",
        default="validated_inputs.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    try:
        # Load and validate brand profile
        brand_path = Path(args.brand_profile_path)
        if not brand_path.exists():
            raise FileNotFoundError(f"Brand profile not found: {brand_path}")
        
        brand_profile = json.loads(brand_path.read_text())
        validate_brand_profile(brand_profile)
        
        # Parse and validate post plan
        post_plan = json.loads(args.post_plan)
        validate_post_plan(post_plan)
        
        # Parse reference links
        reference_links = json.loads(args.reference_links)
        if not isinstance(reference_links, list):
            raise ValueError("reference_links must be a JSON array")
        
        # Validate publishing mode (already validated by argparse choices)
        
        # Compile validated inputs
        output = {
            "brand_profile": brand_profile,
            "brand_profile_path": str(brand_path.resolve()),
            "weekly_theme": args.weekly_theme,
            "post_plan": post_plan,
            "reference_links": reference_links,
            "publishing_mode": args.publishing_mode,
            "validated": True
        }
        
        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2))
        
        logging.info(f"Inputs validated successfully. Output: {output_path}")
        print(json.dumps(output, indent=2))
        return 0
        
    except FileNotFoundError as e:
        logging.error(str(e))
        return 1
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON: {e}")
        return 1
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
