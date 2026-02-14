#!/usr/bin/env python3
"""
Multi-dimensional quality review for Instagram content.

Scores content across 5 dimensions:
1. Brand Voice Alignment (0-100)
2. Compliance Checks (0-100)
3. Hashtag Hygiene (0-100)
4. Format Validation (0-100)
5. Claims Verification (0-100)

Returns overall score and pass/fail decision (pass >= 80, compliance == 100, claims == 100).
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def score_with_llm(
    generated_content: Dict[str, Any],
    brand_profile: Dict[str, Any],
    reference_content: Dict[str, Any]
) -> Dict[str, Any]:
    """Score content using Claude across all dimensions."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        
        # Compile posts for review
        posts_text = "\n\n".join(
            f"**Post {p['post_id']}** ({p['type']})\n"
            f"Hook: {p.get('hook', '')}\n"
            f"Caption: {p.get('caption', '')[:200]}...\n"
            f"CTA: {p.get('cta', '')}\n"
            f"Hashtags: {', '.join(p.get('hashtags', []))}"
            for p in generated_content.get("posts", [])
            if p.get("status") != "failed"
        )
        
        # Compile reference facts
        ref_text = "\n\n".join(
            f"Source: {r['url']}\n{r['content'][:500]}"
            for r in reference_content.get("reference_content", [])
            if r.get("success")
        ) or "No reference material."
        
        prompt = f"""You are a content quality reviewer. Score the generated Instagram posts across 5 dimensions.

**Brand Profile:**
- Brand: {brand_profile['brand_name']}
- Tone: {brand_profile['tone']}
- Target Audience: {brand_profile['target_audience']}
- Banned Topics: {', '.join(brand_profile.get('banned_topics', []))}
- Prohibited Claims: {', '.join(brand_profile.get('prohibited_claims', []))}
- Preferred CTAs: {', '.join(brand_profile.get('preferred_cta', []))}
- Hashtag Preferences: {json.dumps(brand_profile.get('hashtag_preferences', {}))}

**Generated Posts:**
{posts_text}

**Reference Material:**
{ref_text}

**Task:** Score each dimension (0-100) and provide specific issues found.

Return ONLY valid JSON matching this schema:
{{
  "brand_voice": {{
    "score": 90,
    "issues": ["Post 3 uses slightly formal language"]
  }},
  "compliance": {{
    "score": 100,
    "issues": []
  }},
  "hashtags": {{
    "score": 85,
    "issues": ["Post 2 uses generic hashtag #love"]
  }},
  "format": {{
    "score": 95,
    "issues": []
  }},
  "claims": {{
    "score": 100,
    "issues": []
  }}
}}

**Scoring Criteria:**

**1. Brand Voice Alignment (0-100):**
- Tone matches brand guidelines (formal/casual/technical)
- Language resonates with target audience
- Emoji usage matches brand style
- Messaging is on-brand
Score: 90-100 (excellent), 80-89 (good), <80 (needs work)

**2. Compliance Checks (0-100):**
- CRITICAL: No banned topics detected
- CRITICAL: No prohibited claims found
- All CTAs from approved list
- Score MUST be 100 to pass

**3. Hashtag Hygiene (0-100):**
- Count within brand preferences
- No banned hashtags
- Limited generic hashtags (#love, #instagood, #photooftheday)
- Mix of broad and niche hashtags
Score: 80+ to pass

**4. Format Validation (0-100):**
- Caption length under 2200 chars
- Hook under 125 chars
- Alt text present (max 100 chars)
- Creative brief has sufficient detail
Score: 80+ to pass

**5. Claims Verification (0-100):**
- CRITICAL: All factual claims sourced from references
- No unsupported statistics
- No unverifiable guarantees
- Score MUST be 100 to pass

List ALL issues found. Be thorough but fair."""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3072,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Strip markdown fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        scores = json.loads(text)
        
        # Calculate overall score
        dimension_scores = [
            scores.get("brand_voice", {}).get("score", 0),
            scores.get("compliance", {}).get("score", 0),
            scores.get("hashtags", {}).get("score", 0),
            scores.get("format", {}).get("score", 0),
            scores.get("claims", {}).get("score", 0)
        ]
        overall_score = sum(dimension_scores) / len(dimension_scores)
        
        # Determine pass/fail
        compliance_ok = scores.get("compliance", {}).get("score", 0) == 100
        claims_ok = scores.get("claims", {}).get("score", 0) == 100
        overall_ok = overall_score >= 80
        
        pass_fail = "PASS" if (overall_ok and compliance_ok and claims_ok) else "FAIL"
        
        # Compile result
        result = {
            "scores": scores,
            "overall_score": round(overall_score, 1),
            "pass_fail": pass_fail,
            "pass_criteria": {
                "overall_80": overall_ok,
                "compliance_100": compliance_ok,
                "claims_100": claims_ok
            }
        }
        
        return result
        
    except Exception as e:
        logging.error(f"Review failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Review Instagram content quality"
    )
    parser.add_argument(
        "--generated-content",
        required=True,
        help="Path to generated content JSON"
    )
    parser.add_argument(
        "--brand-profile",
        required=True,
        help="Path to brand profile JSON"
    )
    parser.add_argument(
        "--reference-content",
        required=True,
        help="Path to reference content JSON"
    )
    parser.add_argument(
        "--output",
        default="review_report.json",
        help="Output file path"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Number of retries on failure"
    )
    
    args = parser.parse_args()
    
    try:
        # Load inputs
        with open(args.generated_content) as f:
            generated = json.load(f)
        
        with open(args.brand_profile) as f:
            brand_profile = json.load(f)
        
        with open(args.reference_content) as f:
            references = json.load(f)
        
        # Review with retry
        for attempt in range(1, args.retries + 2):
            try:
                logging.info(f"Running quality review (attempt {attempt}/{args.retries + 1})")
                
                review = score_with_llm(generated, brand_profile, references)
                
                # Write output
                with open(args.output, 'w') as f:
                    json.dump(review, f, indent=2)
                
                logging.info(
                    f"Review complete: {review['overall_score']}/100 - {review['pass_fail']}"
                )
                print(json.dumps(review, indent=2))
                return 0
                
            except Exception as e:
                if attempt > args.retries:
                    logging.error(f"Review failed after {attempt} attempts")
                    # Return conservative FAIL default
                    fail_result = {
                        "scores": {
                            "brand_voice": {"score": 0, "issues": ["Review failed"]},
                            "compliance": {"score": 0, "issues": ["Review failed"]},
                            "hashtags": {"score": 0, "issues": ["Review failed"]},
                            "format": {"score": 0, "issues": ["Review failed"]},
                            "claims": {"score": 0, "issues": ["Review failed"]}
                        },
                        "overall_score": 0,
                        "pass_fail": "FAIL",
                        "pass_criteria": {
                            "overall_80": False,
                            "compliance_100": False,
                            "claims_100": False
                        },
                        "error": str(e)
                    }
                    with open(args.output, 'w') as f:
                        json.dump(fail_result, f, indent=2)
                    print(json.dumps(fail_result, indent=2))
                    return 1
                
                logging.warning(f"Attempt {attempt} failed: {e}. Retrying...")
                continue
        
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
