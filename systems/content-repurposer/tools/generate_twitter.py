"""
Generate Twitter — Generate Twitter thread from content matching source tone

Creates a threaded tweet sequence with proper character limits (280/tweet),
numbering, hashtags, and mention suggestions. Matches source content tone.

Inputs:
    - markdown_content (str): Source content
    - tone_analysis (dict): Tone profile from analyze_tone.py
    - author_handle (str, optional): Author handle for mentions
    - brand_hashtags (list[str], optional): Brand hashtags to include

Outputs:
    - JSON: {thread: [{tweet_number, text, char_count}, ...], total_tweets, hashtags, suggested_mentions}

Usage:
    python generate_twitter.py --content "..." --tone '{"formality": "casual", ...}'

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


def generate_twitter_thread(
    content: str, tone: dict[str, Any], author_handle: str = "", brand_hashtags: list[str] | None = None
) -> dict[str, Any]:
    """
    Generate Twitter thread using Claude API.

    Args:
        content: Source markdown content
        tone: Tone analysis dict
        author_handle: Optional author handle
        brand_hashtags: Optional list of brand hashtags

    Returns:
        dict with thread, total_tweets, hashtags, suggested_mentions

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
    system_prompt = f"""You are a Twitter content strategist. Generate a Twitter thread from the provided content.

**Source Tone Profile**:
- Formality: {tone.get('formality', 'neutral')}
- Technical Level: {tone.get('technical_level', 'general')}
- Humor Level: {tone.get('humor_level', 'low')}
- Primary Emotion: {tone.get('primary_emotion', 'informative')}

**CRITICAL: Match this tone exactly** in your Twitter thread. If the source is formal, be formal. If casual, be casual.

**Twitter Thread Constraints**:
- Maximum 280 characters per tweet (STRICT LIMIT)
- Number tweets in X/N format (e.g., "1/5", "2/5")
- First tweet MUST have a hook that grabs attention
- Last tweet MUST have a clear call-to-action (CTA)
- Use line breaks for readability
- Include 2-3 relevant hashtags total (distributed across thread, not all in one tweet)
- Suggest @mentions for industry leaders or relevant accounts (without the @ in JSON)

**Brand Hashtags to Include**: {', '.join(brand_hashtags) if brand_hashtags else 'None'}
{"**Author Handle**: " + author_handle if author_handle else ""}

Return ONLY valid JSON in this exact structure (no markdown fences):
{{
  "thread": [
    {{"tweet_number": 1, "text": "First tweet with hook...", "char_count": 125}},
    {{"tweet_number": 2, "text": "Second tweet...", "char_count": 267}}
  ],
  "total_tweets": 5,
  "hashtags": ["#ContentMarketing", "#SEO"],
  "suggested_mentions": ["Industry_Leader", "Relevant_Account"]
}}"""

    logger.info("Generating Twitter thread (content length: %d chars)", len(content))

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

    # Validate character counts
    for tweet in result.get("thread", []):
        tweet_text = tweet.get("text", "")
        actual_length = len(tweet_text)
        tweet["char_count"] = actual_length  # Ensure accurate count

        if actual_length > 280:
            logger.error("Tweet %d exceeds 280 chars: %d", tweet.get("tweet_number", 0), actual_length)
            # Truncate with ellipsis
            tweet["text"] = tweet_text[:277] + "..."
            tweet["char_count"] = 280
            logger.warning("Tweet %d truncated to 280 chars", tweet.get("tweet_number", 0))

    logger.info("Twitter thread generated (%d tweets)", len(result.get("thread", [])))

    return result


def main() -> dict[str, Any]:
    """
    Main entry point for the Twitter generator tool.

    Returns:
        dict: Twitter thread result.
    """
    parser = argparse.ArgumentParser(description="Generate Twitter thread from content")
    parser.add_argument("--content", help="Markdown content (alternative to stdin)")
    parser.add_argument("--tone", help="Tone analysis JSON string")
    parser.add_argument("--author-handle", default="", help="Author social media handle")
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

    logger.info("Starting Twitter generation")

    try:
        result = generate_twitter_thread(content, tone, args.author_handle, brand_hashtags)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except Exception as e:
        logger.error("Twitter generation failed: %s", str(e))
        error_result = {
            "status": "generation_failed",
            "message": str(e),
            "thread": [],
            "total_tweets": 0,
            "hashtags": [],
            "suggested_mentions": [],
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
