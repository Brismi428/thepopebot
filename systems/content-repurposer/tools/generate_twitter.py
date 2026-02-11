#!/usr/bin/env python3
"""
generate_twitter.py

Generates an optimized Twitter thread from blog content and tone analysis.

Usage:
    python generate_twitter.py --content-file content.json --tone-file tone.json

Output:
    JSON with thread array, total_tweets, hashtags, suggested_mentions
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


def generate_twitter_thread(
    content: str,
    tone_analysis: Dict[str, Any],
    author_handle: str = "",
    brand_hashtags: List[str] = None
) -> Dict[str, Any]:
    """Generate Twitter thread matching source tone."""
    
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("anthropic package required")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    brand_tags = brand_hashtags or []
    
    system_prompt = f"""You are a social media expert specializing in Twitter content.

Generate a Twitter thread from the provided blog content.

TONE REQUIREMENTS:
- Formality: {tone_analysis.get('formality', 'neutral')}
- Technical level: {tone_analysis.get('technical_level', 'general')}
- Humor: {tone_analysis.get('humor_level', 'low')}
- Emotion: {tone_analysis.get('primary_emotion', 'informative')}

MATCH THE SOURCE TONE PRECISELY. If the source is formal, be formal. If casual, be casual.

TWITTER CONSTRAINTS:
- Each tweet max 280 characters (STRICT limit)
- Number tweets: 1/N, 2/N, etc.
- First tweet: strong hook, grab attention in first 140 chars
- Middle tweets: one key insight per tweet
- Final tweet: clear CTA (call-to-action)
- Include 2-3 relevant hashtags for the ENTIRE thread (not per tweet)
- Use line breaks for readability where appropriate

Return ONLY valid JSON:
{{
  "thread": [
    {{"tweet_number": 1, "text": "...", "char_count": 125}},
    {{"tweet_number": 2, "text": "...", "char_count": 267}}
  ],
  "total_tweets": 5,
  "hashtags": ["#Hashtag1", "#Hashtag2"],
  "suggested_mentions": ["@handle1", "@handle2"]
}}"""
    
    user_prompt = f"Blog content to convert into Twitter thread:\n\n{content[:6000]}"
    if author_handle:
        user_prompt += f"\n\nAuthor handle to potentially mention: @{author_handle}"
    if brand_tags:
        user_prompt += f"\n\nBrand hashtags to include: {', '.join(brand_tags)}"
    
    logger.info("Generating Twitter thread...")
    
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
        
        # Validate thread
        if "thread" not in result or not isinstance(result["thread"], list):
            raise ValueError("Invalid response: missing or invalid 'thread' field")
        
        # Validate and fix character counts
        for tweet in result["thread"]:
            text = tweet.get("text", "")
            actual_count = len(text)
            tweet["char_count"] = actual_count
            
            if actual_count > 280:
                logger.warning(f"Tweet {tweet['tweet_number']} exceeds 280 chars ({actual_count}). Truncating.")
                tweet["text"] = text[:277] + "..."
                tweet["char_count"] = 280
        
        logger.info(f"Generated {len(result['thread'])} tweet thread")
        return result
    
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise


def main(
    content: str,
    tone_analysis: Dict[str, Any],
    author_handle: str = "",
    brand_hashtags: List[str] = None
) -> Dict[str, Any]:
    """Main generation function with error handling."""
    
    try:
        return generate_twitter_thread(content, tone_analysis, author_handle, brand_hashtags)
    except Exception as e:
        logger.error(f"Twitter generation failed: {str(e)}")
        return {
            "status": "generation_failed",
            "error": str(e),
            "thread": [],
            "total_tweets": 0,
            "hashtags": [],
            "suggested_mentions": []
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Twitter thread")
    parser.add_argument("--content-file", required=True, help="JSON file with markdown_content")
    parser.add_argument("--tone-file", required=True, help="JSON file with tone analysis")
    parser.add_argument("--author-handle", default="", help="Author social handle")
    parser.add_argument("--brand-hashtags", default="", help="Comma-separated brand hashtags")
    
    args = parser.parse_args()
    
    try:
        with open(args.content_file) as f:
            content_data = json.load(f)
        with open(args.tone_file) as f:
            tone_data = json.load(f)
        
        content = content_data.get("markdown_content", "")
        brand_tags = [t.strip() for t in args.brand_hashtags.split(",") if t.strip()] if args.brand_hashtags else []
        
        result = main(content, tone_data, args.author_handle, brand_tags)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        sys.exit(0 if result.get("status") != "generation_failed" else 1)
    
    except Exception as e:
        logger.exception("Fatal error")
        print(json.dumps({"status": "generation_failed", "error": str(e)}, indent=2))
        sys.exit(1)
