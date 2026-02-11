#!/usr/bin/env python3
"""
generate_instagram.py

Generates an optimized Instagram caption from blog content and tone analysis.

Usage:
    python generate_instagram.py --content-file content.json --tone-file tone.json

Output:
    JSON with caption, char_count, hashtags, line_break_count, emoji_count
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Dict, Any, List

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def count_emojis(text: str) -> int:
    """Count emoji characters in text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return len(emoji_pattern.findall(text))


def generate_instagram_caption(
    content: str,
    tone_analysis: Dict[str, Any],
    brand_hashtags: List[str] = None
) -> Dict[str, Any]:
    """Generate Instagram caption matching source tone."""
    
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("anthropic package required")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    brand_tags = brand_hashtags or []
    
    system_prompt = f"""You are an Instagram content creator.

Generate an Instagram caption from the provided blog content.

TONE REQUIREMENTS:
- Formality: {tone_analysis.get('formality', 'casual')} (Instagram defaults more casual)
- Technical level: {tone_analysis.get('technical_level', 'general')}
- Humor: {tone_analysis.get('humor_level', 'medium')}
- Emotion: {tone_analysis.get('primary_emotion', 'inspiring')}

INSTAGRAM BEST PRACTICES:
- Hook in first 1-2 lines (before "more" button)
- Line breaks every 2-3 sentences for readability
- Use 3-5 emojis strategically (not excessive)
- Visual storytelling (caption must work standalone)
- Conversational, engaging tone
- Lists or numbered points work well
- Strong call-to-action (comment, tag, save, share)
- Target 1500-2000 characters (sweet spot)
- Maximum 2200 characters (hard limit)
- 10-15 hashtags (mix of broad, niche, branded)
- Hashtag format: lowercase, alphanumeric + underscores only

Return ONLY valid JSON:
{{
  "caption": "Caption text with\\n\\nline breaks and emojis 💡",
  "hashtags": ["#marketing", "#contentcreator", "#tips"]
}}"""
    
    user_prompt = f"Blog content to convert into Instagram caption:\n\n{content[:6000]}"
    if brand_tags:
        user_prompt += f"\n\nBrand hashtags to include: {', '.join(brand_tags)}"
    
    logger.info("Generating Instagram caption...")
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.8,  # Slightly higher for creative Instagram content
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Strip markdown fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]).strip()
        
        result = json.loads(response_text)
        
        # Validate required fields
        if "caption" not in result:
            raise ValueError("Missing 'caption' field in response")
        
        caption = result["caption"]
        
        # Calculate metrics
        char_count = len(caption)
        line_break_count = caption.count("\n")
        emoji_count = count_emojis(caption)
        
        # Validate caption length
        if char_count > 2200:
            logger.warning(f"Caption exceeds 2200 chars ({char_count}). Truncating.")
            caption = caption[:2197] + "..."
            char_count = 2200
        
        # Validate hashtag format
        hashtags = result.get("hashtags", [])
        clean_hashtags = []
        for tag in hashtags:
            # Remove # if present, lowercase, keep only alphanumeric and underscores
            clean_tag = re.sub(r'[^a-z0-9_]', '', tag.lower().lstrip('#'))
            if clean_tag:
                clean_hashtags.append(f"#{clean_tag}")
        
        # Limit to 15 hashtags
        clean_hashtags = clean_hashtags[:15]
        
        logger.info(f"Generated Instagram caption: {char_count} chars, {emoji_count} emojis, {len(clean_hashtags)} hashtags")
        
        return {
            "caption": caption,
            "char_count": char_count,
            "hashtags": clean_hashtags,
            "line_break_count": line_break_count,
            "emoji_count": emoji_count
        }
    
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise


def main(
    content: str,
    tone_analysis: Dict[str, Any],
    brand_hashtags: List[str] = None
) -> Dict[str, Any]:
    """Main generation function with error handling."""
    
    try:
        return generate_instagram_caption(content, tone_analysis, brand_hashtags)
    except Exception as e:
        logger.error(f"Instagram generation failed: {str(e)}")
        return {
            "status": "generation_failed",
            "error": str(e),
            "caption": "",
            "char_count": 0,
            "hashtags": [],
            "line_break_count": 0,
            "emoji_count": 0
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Instagram caption")
    parser.add_argument("--content-file", required=True, help="JSON file with markdown_content")
    parser.add_argument("--tone-file", required=True, help="JSON file with tone analysis")
    parser.add_argument("--brand-hashtags", default="", help="Comma-separated brand hashtags")
    
    args = parser.parse_args()
    
    try:
        with open(args.content_file) as f:
            content_data = json.load(f)
        with open(args.tone_file) as f:
            tone_data = json.load(f)
        
        content = content_data.get("markdown_content", "")
        brand_tags = [t.strip() for t in args.brand_hashtags.split(",") if t.strip()] if args.brand_hashtags else []
        
        result = main(content, tone_data, brand_tags)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        sys.exit(0 if result.get("status") != "generation_failed" else 1)
    
    except Exception as e:
        logger.exception("Fatal error")
        print(json.dumps({"status": "generation_failed", "error": str(e)}, indent=2))
        sys.exit(1)
