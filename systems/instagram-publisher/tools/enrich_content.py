#!/usr/bin/env python3
"""
Instagram Content Enricher

Optionally enhances Instagram content with AI-generated insights:
- Hashtag suggestions based on caption analysis
- Alt text generation for accessibility
- Caption improvements for engagement

This is an OPTIONAL step that gracefully degrades if LLM APIs are unavailable.

Usage:
    python enrich_content.py \
        --content '{"caption": "...", "image_url": "..."}' \
        --enhancement-type hashtags

    python enrich_content.py --file input/queue/post.json --enhancement-type alt_text

Returns:
    JSON: {"enhanced_content": {...}} (original content with enriched fields)
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Valid enhancement types
ENHANCEMENT_TYPES = ["hashtags", "alt_text", "caption", "all"]


def enrich_with_anthropic(
    content: dict[str, Any],
    enhancement_type: str,
) -> dict[str, Any]:
    """
    Enrich content using Anthropic Claude API.
    
    Args:
        content: Content payload
        enhancement_type: Type of enhancement to perform
        
    Returns:
        Enriched content dictionary
    """
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed, skipping enrichment")
        return content
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping enrichment")
        return content
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build prompt based on enhancement type
        caption = content.get("caption", "")
        image_url = content.get("image_url", "")
        
        if enhancement_type == "hashtags":
            prompt = f"""Analyze this Instagram caption and suggest 3-5 additional relevant hashtags that would increase reach and engagement. Return ONLY a JSON array of hashtag strings (with # prefix).

Caption: {caption}

Return format: ["#hashtag1", "#hashtag2", "#hashtag3"]"""
        
        elif enhancement_type == "alt_text":
            prompt = f"""Generate descriptive alt text for this Instagram post for accessibility. Keep it concise (1-2 sentences). Return ONLY the alt text string, no JSON.

Caption: {caption}
Image URL: {image_url}"""
        
        elif enhancement_type == "caption":
            prompt = f"""Improve this Instagram caption for better engagement while maintaining the original voice and message. Add emojis if appropriate. Keep under 2000 characters. Return ONLY the improved caption text, no JSON.

Original caption: {caption}"""
        
        else:
            logger.warning(f"Unknown enhancement type: {enhancement_type}")
            return content
        
        # Call Claude
        logger.info(f"Calling Claude for {enhancement_type} enhancement...")
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Parse response and merge into content
        enriched = dict(content)
        
        if enhancement_type == "hashtags":
            try:
                suggested_hashtags = json.loads(response_text)
                if isinstance(suggested_hashtags, list):
                    existing = enriched.get("hashtags", [])
                    # Deduplicate and combine
                    all_hashtags = list(set(existing + suggested_hashtags))
                    enriched["hashtags"] = all_hashtags[:30]  # Max 30 hashtags
                    logger.info(f"✓ Added {len(suggested_hashtags)} hashtag suggestions")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse hashtag response: {response_text}")
        
        elif enhancement_type == "alt_text":
            enriched["alt_text"] = response_text
            logger.info(f"✓ Generated alt text: {response_text[:50]}...")
        
        elif enhancement_type == "caption":
            enriched["caption"] = response_text
            logger.info(f"✓ Improved caption (length: {len(response_text)})")
        
        return enriched
        
    except Exception as e:
        logger.exception(f"Claude API error: {e}")
        return content


def enrich_with_openai(
    content: dict[str, Any],
    enhancement_type: str,
) -> dict[str, Any]:
    """
    Enrich content using OpenAI API (fallback).
    
    Args:
        content: Content payload
        enhancement_type: Type of enhancement to perform
        
    Returns:
        Enriched content dictionary
    """
    try:
        import openai
    except ImportError:
        logger.warning("openai package not installed, skipping enrichment")
        return content
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping enrichment")
        return content
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Build prompt based on enhancement type
        caption = content.get("caption", "")
        image_url = content.get("image_url", "")
        
        if enhancement_type == "hashtags":
            prompt = f"""Analyze this Instagram caption and suggest 3-5 additional relevant hashtags. Return ONLY a JSON array.

Caption: {caption}

Format: ["#hashtag1", "#hashtag2"]"""
        
        elif enhancement_type == "alt_text":
            prompt = f"""Generate alt text for this Instagram post. Keep it concise (1-2 sentences).

Caption: {caption}
Image URL: {image_url}"""
        
        elif enhancement_type == "caption":
            prompt = f"""Improve this Instagram caption for engagement. Keep under 2000 characters.

Original: {caption}"""
        
        else:
            logger.warning(f"Unknown enhancement type: {enhancement_type}")
            return content
        
        # Call OpenAI
        logger.info(f"Calling OpenAI for {enhancement_type} enhancement...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.7,
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse and merge (same logic as Anthropic)
        enriched = dict(content)
        
        if enhancement_type == "hashtags":
            try:
                suggested_hashtags = json.loads(response_text)
                if isinstance(suggested_hashtags, list):
                    existing = enriched.get("hashtags", [])
                    all_hashtags = list(set(existing + suggested_hashtags))
                    enriched["hashtags"] = all_hashtags[:30]
                    logger.info(f"✓ Added {len(suggested_hashtags)} hashtag suggestions")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse hashtag response: {response_text}")
        
        elif enhancement_type == "alt_text":
            enriched["alt_text"] = response_text
            logger.info(f"✓ Generated alt text: {response_text[:50]}...")
        
        elif enhancement_type == "caption":
            enriched["caption"] = response_text
            logger.info(f"✓ Improved caption (length: {len(response_text)})")
        
        return enriched
        
    except Exception as e:
        logger.exception(f"OpenAI API error: {e}")
        return content


def enrich_content(
    content: dict[str, Any],
    enhancement_type: str,
) -> dict[str, Any]:
    """
    Enrich content with AI-generated insights.
    
    Falls back gracefully if APIs are unavailable.
    
    Args:
        content: Content payload
        enhancement_type: Type of enhancement
        
    Returns:
        Enriched content (or original if enrichment fails)
    """
    # Try Anthropic first (primary)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return enrich_with_anthropic(content, enhancement_type)
    
    # Fall back to OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        return enrich_with_openai(content, enhancement_type)
    
    # No API keys available
    logger.warning("No LLM API keys available, skipping enrichment")
    return content


def main(
    content: dict[str, Any] | None = None,
    file_path: str | None = None,
    enhancement_type: str = "hashtags",
) -> dict[str, Any]:
    """
    Main entry point.
    
    Args:
        content: Content payload (if provided directly)
        file_path: Path to JSON file
        enhancement_type: Type of enhancement to perform
        
    Returns:
        Result with enhanced_content key
    """
    try:
        # Load content from file if provided
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        
        if not content:
            raise ValueError("No content provided (use --content or --file)")
        
        if enhancement_type not in ENHANCEMENT_TYPES:
            raise ValueError(f"Invalid enhancement type. Must be one of: {', '.join(ENHANCEMENT_TYPES)}")
        
        # Enrich
        if enhancement_type == "all":
            # Apply all enhancement types sequentially
            enriched = content
            for enh_type in ["hashtags", "alt_text"]:  # Skip caption to preserve original
                enriched = enrich_content(enriched, enh_type)
        else:
            enriched = enrich_content(content, enhancement_type)
        
        return {"enhanced_content": enriched}
        
    except Exception as e:
        logger.exception(f"Enrichment failed: {e}")
        # Graceful degradation: return original content
        return {"enhanced_content": content or {}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Instagram content with AI")
    parser.add_argument("--content", type=str, help="JSON content payload string")
    parser.add_argument("--file", type=str, help="Path to JSON file")
    parser.add_argument(
        "--enhancement-type",
        type=str,
        default="hashtags",
        choices=ENHANCEMENT_TYPES,
        help="Type of enhancement to perform",
    )
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    content_dict = None
    if args.content:
        content_dict = json.loads(args.content)
    
    result = main(
        content=content_dict,
        file_path=args.file,
        enhancement_type=args.enhancement_type,
    )
    
    # Output result
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
    else:
        print(output_json)
    
    sys.exit(0)
