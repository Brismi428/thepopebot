"""
Generate LinkedIn — Generate LinkedIn post from content matching source tone

Creates a professional LinkedIn post with hook, body, CTA, and hashtags.
Targets 1300 chars for optimal visibility (under "see more" fold).

Inputs:
    - markdown_content (str): Source content
    - tone_analysis (dict): Tone profile from analyze_tone.py
    - brand_hashtags (list[str], optional): Brand hashtags to include

Outputs:
    - JSON: {text, char_count, hashtags, hook, cta}

Usage:
    python generate_linkedin.py --content "..." --tone '{"formality": "professional", ...}'

Environment Variables:
    - ANTHROPIC_API_KEY: Claude API key (required)
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_linkedin_post(
    content: str, tone: dict[str, Any], brand_hashtags: list[str] | None = None
) -> dict[str, Any]:
    """
    Generate LinkedIn post using Claude API.

    Args:
        content: Source markdown content
        tone: Tone analysis dict
        brand_hashtags: Optional list of brand hashtags

    Returns:
        dict with text, char_count, hashtags, hook, cta

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
    system_prompt = f"""You are a LinkedIn content strategist. Generate a LinkedIn post from the provided content.

**Source Tone Profile**:
- Formality: {tone.get('formality', 'neutral')}
- Technical Level: {tone.get('technical_level', 'general')}
- Humor Level: {tone.get('humor_level', 'low')}
- Primary Emotion: {tone.get('primary_emotion', 'informative')}

**CRITICAL: Match this tone exactly**. If the source is formal, maintain professionalism. If casual, be conversational but still LinkedIn-appropriate.

**LinkedIn Post Constraints**:
- Target 1300 characters for optimal visibility (before "see more" button)
- Maximum 3000 characters (hard limit)
- Start with a STRONG hook (first 1-2 sentences grab attention)
- Use line breaks for readability (short paragraphs)
- End with a clear call-to-action (question, invitation to comment, etc.)
- Include 3-5 relevant industry hashtags at the end
- Professional but engaging tone

**Brand Hashtags to Include**: {', '.join(brand_hashtags) if brand_hashtags else 'None'}

Return ONLY valid JSON in this exact structure (no markdown fences):
{{
  "text": "Full LinkedIn post text with line breaks...",
  "char_count": 1285,
  "hashtags": ["#Marketing", "#ContentStrategy", "#SocialMedia"],
  "hook": "First 1-2 sentences that grab attention",
  "cta": "What's your take on this? Share in the comments."
}}"""

    logger.info("Generating LinkedIn post (content length: %d chars)", len(content))

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
    post_text = result.get("text", "")
    actual_length = len(post_text)
    result["char_count"] = actual_length

    if actual_length > 3000:
        logger.warning("LinkedIn post exceeds 3000 chars (%d), truncating", actual_length)
        result["text"] = post_text[:2997] + "..."
        result["char_count"] = 3000

    logger.info("LinkedIn post generated (%d chars)", result["char_count"])

    return result


def main() -> dict[str, Any]:
    """
    Main entry point for the LinkedIn generator tool.

    Returns:
        dict: LinkedIn post result.
    """
    parser = argparse.ArgumentParser(description="Generate LinkedIn post from content")
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

    logger.info("Starting LinkedIn generation")

    try:
        result = generate_linkedin_post(content, tone, brand_hashtags)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except Exception as e:
        logger.error("LinkedIn generation failed: %s", str(e))
        error_result = {
            "status": "generation_failed",
            "message": str(e),
            "text": "",
            "char_count": 0,
            "hashtags": [],
            "hook": "",
            "cta": "",
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
