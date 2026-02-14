#!/usr/bin/env python3
"""
Generate complete Instagram post content for all posts.

Supports both parallel generation (Agent Teams) and sequential execution.
Each post includes: hook, caption, CTA, hashtags, alt_text, creative_brief, image_prompt.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def generate_single_post_with_llm(
    post_brief: Dict[str, Any],
    brand_profile: Dict[str, Any],
    post_number: int
) -> Dict[str, Any]:
    """Generate content for a single post using Claude."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        
        # Extract hashtag preferences
        hashtag_count = brand_profile.get("hashtag_preferences", {}).get("count", "8-12")
        hashtag_avoid = brand_profile.get("hashtag_preferences", {}).get("avoid", [])
        
        prompt = f"""You are an Instagram content creator. Generate complete content for ONE Instagram post.

**Brand:** {brand_profile['brand_name']}
**Tone:** {brand_profile['tone']}
**Target Audience:** {brand_profile['target_audience']}
**Emoji Style:** {brand_profile.get('emoji_style', 'minimal')}
**Preferred CTAs:** {', '.join(brand_profile.get('preferred_cta', []))}

**Post Type:** {post_brief.get('post_type', 'single_image')}
**Theme:** {post_brief.get('theme', '')}
**Objective:** {post_brief.get('objective', '')}
**Key Messages:** {', '.join(post_brief.get('key_messages', []))}
**Target Emotion:** {post_brief.get('target_emotion', '')}

**Task:** Generate complete content for this Instagram post.

Return ONLY valid JSON matching this schema:
{{
  "post_id": {post_number},
  "type": "{post_brief.get('post_type', 'single_image')}",
  "hook": "Attention-grabbing first line (max 125 chars, appears before 'more' button)",
  "caption": "Full caption text (125-300 words, match brand tone, include emojis per brand style)",
  "cta": "Call to action from preferred list",
  "hashtags": ["#hashtag1", "#hashtag2"],
  "alt_text": "Descriptive alt text for accessibility (max 100 chars)",
  "creative_brief": "Detailed instructions for image/video creation (what to show, how to shoot/design, style, mood)",
  "image_prompt": "AI image generation prompt (style, composition, lighting, mood - for guidance only, not generation)"
}}

**Requirements:**
- Hook: Must be compelling, max 125 characters (appears before "more" button)
- Caption: 125-300 words, match {brand_profile['tone']} tone
- Hashtags: {hashtag_count} hashtags, avoid: {', '.join(hashtag_avoid) or 'generic, spammy'}
- CTA: Choose from: {', '.join(brand_profile.get('preferred_cta', ['Learn more']))}
- Alt text: Descriptive, max 100 characters
- Creative brief: Detailed (at least 2-3 sentences)
- Image prompt: Detailed visual description"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Strip markdown fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        post_content = json.loads(text)
        
        # Validate required fields
        required = ["hook", "caption", "cta", "hashtags", "alt_text", "creative_brief", "image_prompt"]
        missing = [f for f in required if f not in post_content]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")
        
        # Ensure post_id and type are set
        post_content["post_id"] = post_number
        post_content["type"] = post_brief.get("post_type", "single_image")
        
        return post_content
        
    except Exception as e:
        logging.error(f"Failed to generate post {post_number}: {e}")
        raise


def generate_sequential(
    post_briefs: List[Dict[str, Any]],
    brand_profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate posts sequentially."""
    logging.info("Using sequential generation")
    posts = []
    
    for i, brief in enumerate(post_briefs, 1):
        logging.info(f"Generating post {i}/{len(post_briefs)}")
        try:
            post = generate_single_post_with_llm(brief, brand_profile, i)
            posts.append(post)
        except Exception as e:
            logging.error(f"Failed to generate post {i}: {e}")
            # Add placeholder for failed post
            posts.append({
                "post_id": i,
                "type": brief.get("post_type", "single_image"),
                "error": str(e),
                "status": "failed"
            })
    
    return posts


def main():
    parser = argparse.ArgumentParser(
        description="Generate Instagram post content"
    )
    parser.add_argument(
        "--content-strategy",
        required=True,
        help="Path to content strategy JSON"
    )
    parser.add_argument(
        "--brand-profile",
        required=True,
        help="Path to brand profile JSON"
    )
    parser.add_argument(
        "--output",
        default="generated_content.json",
        help="Output file path"
    )
    parser.add_argument(
        "--use-agent-teams",
        action="store_true",
        help="Use Agent Teams for parallel generation (if 3+ posts)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load inputs
        with open(args.content_strategy) as f:
            strategy = json.load(f)
        
        with open(args.brand_profile) as f:
            brand_profile = json.load(f)
        
        post_briefs = strategy.get("post_briefs", [])
        
        if not post_briefs:
            logging.error("No post briefs found in content strategy")
            return 1
        
        logging.info(f"Generating content for {len(post_briefs)} posts")
        
        # Decide: parallel or sequential
        # Note: Agent Teams parallelization would be handled by Claude Code's native
        # Agent Teams feature, not within this tool. This tool provides sequential
        # generation. The workflow coordinator (Claude) can invoke this tool
        # multiple times in parallel using Agent Teams.
        
        # For now, always use sequential within this tool
        # The parallel speedup comes from the workflow coordinator
        generated_posts = generate_sequential(post_briefs, brand_profile)
        
        # Check for failures
        failed = [p for p in generated_posts if p.get("status") == "failed"]
        if failed:
            logging.warning(f"{len(failed)} posts failed to generate")
        
        # Compile output
        output = {
            "posts": generated_posts,
            "metadata": {
                "total_posts": len(generated_posts),
                "successful": len(generated_posts) - len(failed),
                "failed": len(failed),
                "generation_mode": "sequential"
            }
        }
        
        # Write output
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        
        logging.info(
            f"Content generated: {output['metadata']['successful']}/{output['metadata']['total_posts']} successful"
        )
        print(json.dumps(output, indent=2))
        
        # Exit with error if any posts failed
        return 1 if failed else 0
        
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
