"""
Generate Instagram — Generate Instagram caption from content matching source tone

Creates an Instagram caption with emojis, line breaks, hashtags, and engaging hooks.
Target 1500-2000 chars with 10-15 hashtags for optimal reach.

Inputs:
    - markdown_content (str): Source content
    - tone_analysis (dict): Tone profile from analyze_tone.py
    - brand_hashtags (list[str], optional): Brand hashtags to include

Outputs:
    - JSON: {caption, char_count, hashtags, line_break_count, emoji_count}

Usage:
    python generate_instagram.py --content "..." --tone '{"formality": "casual", ...}'

Environment Variables:
    - ANTHROPIC_API_KEY: Claude API key (required)
"""

import argparse
import json
import logging
import os
import sys
import re
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def count_emojis(text: str) -> int:
    """
    Count emoji characters in text.

    Args:
        text: Text to analyze

    Returns:
        int: Number of emojis found
    """
    # Unicode ranges for emojis (simplified)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return len(emoji_pattern.findall(text))


def generate_instagram_caption(
    content: str, tone: dict[str, Any], brand_hashtags: list[str] | None = None
) -> dict[str, Any]:
    """
    Generate Instagram caption using Claude API.

    Args:
        content: Source markdown content
        tone: Tone analysis dict
        brand_hashtags: Optional list of brand hashtags

    Returns:
        dict with caption, char_count, hashtags, line_break_count, emoji_count

    Raises:
        Exception: If Claude API call fails or validation fails
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Build system prompt with tone matching instructions
    system_prompt = f"""You are an Instagram content strategist. Generate an Instagram caption from the provided content.

**Source Tone Profile**:
- Formality: {tone.get('formality', 'neutral')}
- Technical Level: {tone.get('technical_level', 'general')}
- Humor Level: {tone.get('humor_level', 'low')}
- Primary Emotion: {tone.get('primary_emotion', 'informative')}

**CRITICAL: Match this tone**. If the source is casual, be Instagram-friendly casual. If formal, maintain professionalism but adapt to Instagram's visual, conversational style.

**Instagram Caption Constraints**:
- Target 1500-2000 characters for optimal engagement
- Maximum 2200 characters (hard limit)
- Start with a HOOK (first line grabs attention, shows before "more" button)
- Use line breaks for readability (every 2-3 sentences)
- Include 3-5 relevant emojis (not excessive, strategic placement)
- End with 10-15 hashtags (lowercase, no spaces, alphanumeric + underscores only)
- Mix popular and niche hashtags for reach + engagement
- Conversational, engaging tone

**Brand Hashtags to Include**: {', '.join(brand_hashtags) if brand_hashtags else 'None'}

Return ONLY valid JSON in this exact structure (no markdown fences):
{{
  "caption": "Hook line here 🔥\\n\\nBody paragraph with insights...\\n\\nAnother paragraph...\\n\\n#hashtag1 #hashtag2 #hashtag3",
  "char_count": 1847,
  "hashtags": ["#marketing", "#contentcreation", "#socialmedia"],
  "line_break_count": 4,
  "emoji_count": 3
}}"""

    logger.info("Generating Instagram caption (content length: %d chars)", len(content))

    # Truncate content if too long
    if len(content) > 50000:
        logger.warning("Content exceeds 50k chars, truncating for generation")
        content = content[:50000] + "\n\n[Content truncated]"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

    # Parse JSON response
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Claude response as JSON: %s", e)
        logger.debug("Raw response: %s", response_text)
        raise ValueError(f"Claude returned invalid JSON: {e}") from e

    # Validate and update character count
    caption_text = result.get("caption", "")
    actual_length = len(caption_text)
    result["char_count"] = actual_length

    if actual_length > 2200:
        logger.warning("Instagram caption exceeds 2200 chars (%d), truncating", actual_length)
        result["caption"] = caption_text[:2197] + "..."
        result["char_count"] = 2200

    # Count line breaks and emojis
    line_breaks = caption_text.count("\n")
    emoji_count = count_emojis(caption_text)

    result["line_break_count"] = line_breaks
    result["emoji_count"] = emoji_count

    # Validate hashtags are lowercase alphanumeric + underscores
    hashtags = result.get("hashtags", [])
    validated_hashtags = []
    for tag in hashtags:
        # Remove # if present, lowercase, validate format
        clean_tag = tag.lstrip("#").lower()
        if re.match(r"^[a-z0-9_]+$", clean_tag):
            validated_hashtags.append(f"#{clean_tag}")
        else:
            logger.warning("Invalid hashtag format (skipping): %s", tag)

    result["hashtags"] = validated_hashtags

    logger.info(
        "Instagram caption generated (%d chars, %d line breaks, %d emojis, %d hashtags)",
        actual_length,
        line_breaks,
        emoji_count,
        len(validated_hashtags),
    )

    return result


def main() -> dict[str, Any]:
    """
    Main entry point for the Instagram generator tool.

    Returns:
        dict: Instagram caption result.
    """
    parser = argparse.ArgumentParser(description="Generate Instagram caption from content")
    parser.add_argument("--content", help="Markdown content (alternative to stdin)")
    parser.add_argument("--tone", help="Tone analysis JSON string")
    parser.add_argument("--brand-hashtags", help="Comma-separated brand hashtags")
    args = parser.parse_args()

    # Get inputs
    if args.content and args.tone:
        content = args.content
        tone = json.loads(args.tone)
    else:
        # Read from stdin (JSON with markdown_content and tone_analysis fields)
        try:
            stdin_data = json.load(sys.stdin)
            content = stdin_data.get("markdown_content", "")
            tone = stdin_data.get("tone_analysis", {})
        except json.JSONDecodeError as e:
            logger.error("Failed to parse stdin as JSON: %s", e)
            sys.exit(1)

    brand_hashtags = []
    if args.brand_hashtags:
        brand_hashtags = [tag.strip() for tag in args.brand_hashtags.split(",")]

    logger.info("Starting Instagram generation")

    try:
        result = generate_instagram_caption(content, tone, brand_hashtags)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except Exception as e:
        logger.error("Instagram generation failed: %s", str(e))
        error_result = {
            "status": "generation_failed",
            "message": str(e),
            "caption": "",
            "char_count": 0,
            "hashtags": [],
            "line_break_count": 0,
            "emoji_count": 0,
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
