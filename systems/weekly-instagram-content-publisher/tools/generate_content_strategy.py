#!/usr/bin/env python3
"""
Generate content strategy using LLM analysis of brand voice, theme, and references.

Produces per-post content briefs, posting schedule, and content themes.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def generate_strategy_with_llm(
    brand_profile: Dict[str, Any],
    weekly_theme: str,
    post_plan: Dict[str, Any],
    reference_content: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate content strategy using Claude."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        
        # Build context
        ref_text = "\n\n".join(
            f"Source: {r['url']}\n{r['content'][:1000]}"
            for r in reference_content.get("reference_content", [])
            if r.get("success")
        ) or "No reference material provided."
        
        total_posts = sum(
            post_plan.get(t, 0) for t in ["reels", "carousels", "single_images", "stories"]
        )
        
        prompt = f"""You are a social media strategist creating an Instagram content strategy.

**Brand:** {brand_profile['brand_name']}
**Tone:** {brand_profile['tone']}
**Target Audience:** {brand_profile['target_audience']}
**Products/Services:** {', '.join(brand_profile['products'])}

**Weekly Theme:** {weekly_theme}

**Post Plan:**
- Reels: {post_plan.get('reels', 0)}
- Carousels: {post_plan.get('carousels', 0)}
- Single Images: {post_plan.get('single_images', 0)}
- Stories: {post_plan.get('stories', 0)}
Total: {total_posts} posts

**Reference Material:**
{ref_text}

**Task:** Generate a complete content strategy with:
1. A content brief for EACH post (one brief per reel, carousel, single image)
2. A posting schedule (spread posts across 7 days, optimal times)
3. Content themes/pillars for the week

Return ONLY valid JSON matching this schema:
{{
  "post_briefs": [
    {{
      "post_number": 1,
      "post_type": "reel",
      "theme": "Product announcement",
      "objective": "Generate awareness and excitement",
      "key_messages": ["message 1", "message 2"],
      "target_emotion": "excitement",
      "content_angle": "Behind-the-scenes reveal"
    }}
  ],
  "posting_schedule": [
    {{
      "post_number": 1,
      "posting_day": "Monday",
      "posting_time": "10:00 AM local time",
      "rationale": "Start of week, high engagement"
    }}
  ],
  "content_themes": ["theme1", "theme2", "theme3"]
}}

Generate {total_posts} post briefs, one for each post in the plan."""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        strategy = json.loads(text)
        
        # Validate structure
        if "post_briefs" not in strategy or "posting_schedule" not in strategy:
            raise ValueError("Invalid strategy structure: missing required fields")
        
        if len(strategy["post_briefs"]) != total_posts:
            logging.warning(
                f"Expected {total_posts} post briefs, got {len(strategy['post_briefs'])}"
            )
        
        return strategy
        
    except json.JSONDecodeError as e:
        logging.error(f"LLM returned invalid JSON: {e}")
        raise
    except Exception as e:
        logging.error(f"Strategy generation failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Generate Instagram content strategy"
    )
    parser.add_argument(
        "--validated-inputs",
        required=True,
        help="Path to validated inputs JSON"
    )
    parser.add_argument(
        "--reference-content",
        required=True,
        help="Path to reference content JSON"
    )
    parser.add_argument(
        "--output",
        default="content_strategy.json",
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
        with open(args.validated_inputs) as f:
            inputs = json.load(f)
        
        with open(args.reference_content) as f:
            references = json.load(f)
        
        # Generate strategy with retry
        for attempt in range(1, args.retries + 2):
            try:
                logging.info(f"Generating strategy (attempt {attempt}/{args.retries + 1})")
                
                strategy = generate_strategy_with_llm(
                    inputs["brand_profile"],
                    inputs["weekly_theme"],
                    inputs["post_plan"],
                    references
                )
                
                # Write output
                with open(args.output, 'w') as f:
                    json.dump(strategy, f, indent=2)
                
                logging.info(f"Strategy generated: {len(strategy['post_briefs'])} post briefs")
                print(json.dumps(strategy, indent=2))
                return 0
                
            except Exception as e:
                if attempt > args.retries:
                    logging.error(f"Strategy generation failed after {attempt} attempts")
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
