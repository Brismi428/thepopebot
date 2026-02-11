#!/usr/bin/env python3
"""
generate_linkedin.py

Generates an optimized LinkedIn post from blog content and tone analysis.

Usage:
    python generate_linkedin.py --content-file content.json --tone-file tone.json

Output:
    JSON with text, char_count, hashtags, hook, cta
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, List

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_linkedin_post(
    content: str,
    tone_analysis: Dict[str, Any],
    brand_hashtags: List[str] = None
) -> Dict[str, Any]:
    """Generate LinkedIn post matching source tone."""
    
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("anthropic package required")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    brand_tags = brand_hashtags or []
    
    system_prompt = f"""You are a LinkedIn content strategist.

Generate a LinkedIn post from the provided blog content.

TONE REQUIREMENTS:
- Formality: {tone_analysis.get('formality', 'professional')} (LinkedIn defaults to professional)
- Technical level: {tone_analysis.get('technical_level', 'intermediate')}
- Humor: {tone_analysis.get('humor_level', 'low')}
- Emotion: {tone_analysis.get('primary_emotion', 'informative')}

LINKEDIN BEST PRACTICES:
- Hook in first 1-2 sentences (before "see more" fold)
- Short paragraphs (2-3 sentences each)
- Line breaks for readability
- Bullet points or numbered lists where appropriate
- Professional yet conversational tone
- Clear value proposition and takeaways
- Strong call-to-action at end
- Target 1200-1400 characters (optimal visibility)
- Maximum 3000 characters (hard limit)
- 3-5 relevant hashtags (mix of popular and niche)

Return ONLY valid JSON:
{{
  "text": "Full LinkedIn post with line breaks...",
  "char_count": 1285,
  "hashtags": ["#Marketing", "#ContentStrategy"],
  "hook": "First sentence that grabs attention",
  "cta": "Call-to-action text"
}}"""
    
    user_prompt = f"Blog content to convert into LinkedIn post:\n\n{content[:7000]}"
    if brand_tags:
        user_prompt += f"\n\nBrand hashtags to include: {', '.join(brand_tags)}"
    
    logger.info("Generating LinkedIn post...")
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.7,
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
        if "text" not in result:
            raise ValueError("Missing 'text' field in response")
        
        # Update actual character count
        actual_count = len(result["text"])
        result["char_count"] = actual_count
        
        # Warn if too long
        if actual_count > 3000:
            logger.warning(f"Post exceeds 3000 chars ({actual_count}). Truncating.")
            result["text"] = result["text"][:2997] + "..."
            result["char_count"] = 3000
        
        logger.info(f"Generated LinkedIn post: {actual_count} chars")
        return result
    
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
        return generate_linkedin_post(content, tone_analysis, brand_hashtags)
    except Exception as e:
        logger.error(f"LinkedIn generation failed: {str(e)}")
        return {
            "status": "generation_failed",
            "error": str(e),
            "text": "",
            "char_count": 0,
            "hashtags": [],
            "hook": "",
            "cta": ""
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LinkedIn post")
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
