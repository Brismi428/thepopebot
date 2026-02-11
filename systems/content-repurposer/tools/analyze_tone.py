"""
Analyze Tone — Analyze writing style and tone of content using Claude

Uses Claude API with structured JSON output to extract tone characteristics
across multiple dimensions (formality, technical level, humor, emotion).

Inputs:
    - markdown_content (str): Content to analyze (via stdin or --content arg)

Outputs:
    - JSON: {formality, technical_level, humor_level, primary_emotion, confidence, rationale}

Usage:
    python analyze_tone.py --content "Your content here"
    echo '{"markdown_content": "..."}' | python analyze_tone.py

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

# Default tone profile for failures
DEFAULT_TONE = {
    "formality": "neutral",
    "technical_level": "general",
    "humor_level": "low",
    "primary_emotion": "informative",
    "confidence": 0.5,
    "rationale": "Default tone profile due to analysis failure",
}


def analyze_tone_with_claude(content: str) -> dict[str, Any]:
    """
    Analyze content tone using Claude API with structured extraction.

    Args:
        content: Markdown content to analyze

    Returns:
        dict with tone dimensions and confidence score

    Raises:
        Exception: If Claude API call fails
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Define JSON schema for structured extraction
    schema = {
        "type": "object",
        "properties": {
            "formality": {
                "type": "string",
                "enum": ["formal", "semi-formal", "casual"],
                "description": "Overall formality level of the writing",
            },
            "technical_level": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced", "expert"],
                "description": "Technical complexity and assumed audience knowledge",
            },
            "humor_level": {
                "type": "string",
                "enum": ["none", "low", "medium", "high"],
                "description": "Presence and intensity of humor in the writing",
            },
            "primary_emotion": {
                "type": "string",
                "description": "Dominant emotional tone (e.g., informative, persuasive, inspiring, critical)",
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence in this analysis (0.0 to 1.0)",
            },
            "rationale": {
                "type": "string",
                "description": "Brief explanation of the tone analysis",
            },
        },
        "required": [
            "formality",
            "technical_level",
            "humor_level",
            "primary_emotion",
            "confidence",
            "rationale",
        ],
    }

    system_prompt = f"""You are a writing style analyst. Analyze the tone and style of the provided content.

Return your analysis as valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Be precise and consider:
- Formality: word choice, sentence structure, use of jargon
- Technical level: assumed background knowledge, complexity of concepts
- Humor: presence of jokes, wordplay, lighthearted tone
- Primary emotion: what the author wants the reader to feel

Return ONLY the JSON object, no markdown fences or commentary."""

    logger.info("Sending tone analysis request to Claude (content length: %d chars)", len(content))

    # Truncate content if too long (max ~100k chars for context)
    if len(content) > 100000:
        logger.warning("Content exceeds 100k chars, truncating for analysis")
        content = content[:100000] + "\n\n[Content truncated for analysis]"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        temperature=0.0,
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

    logger.info("Tone analysis complete (confidence: %.2f)", result.get("confidence", 0.0))

    return result


def main() -> dict[str, Any]:
    """
    Main entry point for the tone analysis tool.

    Returns:
        dict: Tone analysis result or default tone profile on failure.
    """
    parser = argparse.ArgumentParser(description="Analyze content tone using Claude")
    parser.add_argument("--content", help="Content to analyze (alternative to stdin)")
    args = parser.parse_args()

    # Get content from arg or stdin
    if args.content:
        content = args.content
    else:
        # Read from stdin (JSON with markdown_content field)
        try:
            stdin_data = json.load(sys.stdin)
            content = stdin_data.get("markdown_content", "")
        except json.JSONDecodeError:
            logger.error("Failed to parse stdin as JSON")
            return DEFAULT_TONE
        except Exception as e:
            logger.error("Error reading stdin: %s", e)
            return DEFAULT_TONE

    if not content or len(content.strip()) < 50:
        logger.warning("Content is too short for meaningful analysis (< 50 chars)")
        return DEFAULT_TONE

    logger.info("Starting tone analysis (content length: %d chars)", len(content))

    # Try tone analysis with retry
    max_retries = 2
    for attempt in range(1, max_retries + 1):
        try:
            result = analyze_tone_with_claude(content)
            return result
        except Exception as e:
            logger.warning("Tone analysis attempt %d/%d failed: %s", attempt, max_retries, str(e))
            if attempt == max_retries:
                logger.error("All tone analysis attempts failed. Returning default profile.")
                return DEFAULT_TONE


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, ensure_ascii=False))
