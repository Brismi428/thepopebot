#!/usr/bin/env python3
"""
Gate decision logic: determine whether to auto-publish or generate manual content pack.

Decision rules:
- IF review pass_fail == "PASS" AND publishing_mode == "auto_publish" -> publish
- ELSE -> manual_pack
"""

import argparse
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Determine publishing action based on review and mode"
    )
    parser.add_argument(
        "--review-report",
        required=True,
        help="Path to review report JSON"
    )
    parser.add_argument(
        "--publishing-mode",
        required=True,
        choices=["auto_publish", "content_pack_only"],
        help="Publishing mode"
    )
    parser.add_argument(
        "--output",
        default="publish_decision.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    try:
        # Load review report
        with open(args.review_report) as f:
            review = json.load(f)
        
        pass_fail = review.get("pass_fail", "FAIL")
        overall_score = review.get("overall_score", 0)
        
        # Apply gate logic
        if pass_fail == "PASS" and args.publishing_mode == "auto_publish":
            action = "publish"
            rationale = f"Quality gates passed (score: {overall_score}/100), auto-publish enabled"
        elif pass_fail == "FAIL":
            action = "manual_pack"
            rationale = f"Quality score {overall_score}/100 - gates not met, manual review required"
        else:  # content_pack_only mode
            action = "manual_pack"
            rationale = "Content pack only mode enabled, skipping auto-publish"
        
        decision = {
            "action": action,
            "rationale": rationale,
            "review_score": overall_score,
            "review_pass_fail": pass_fail,
            "publishing_mode": args.publishing_mode
        }
        
        # Write output
        with open(args.output, 'w') as f:
            json.dump(decision, f, indent=2)
        
        logging.info(f"Decision: {action} - {rationale}")
        print(json.dumps(decision, indent=2))
        return 0
        
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
