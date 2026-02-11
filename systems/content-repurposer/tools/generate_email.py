"""
Generate Email — Generate email newsletter section from content matching source tone

Creates an email newsletter section with subject line, HTML body, plain text fallback,
and call-to-action. Target 500-800 words for optimal engagement.

Inputs:
    - markdown_content (str): Source content
    - tone_analysis (dict): Tone profile from analyze_tone.py
    - source_url (str): Link back to original blog post

Outputs:
    - JSON: {subject_line, section_html, section_text, word_count, cta}

Usage:
    python generate_email.py --content "..." --tone '{"formality": "casual", ...}' --url "https://..."

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


def generate_email_section(
    content: str, tone: dict[str, Any], source_url: str = ""
) -> dict[str, Any]:
    """
    Generate email newsletter section using Claude API.

    Args:
        content: Source markdown content
        tone: Tone analysis dict
        source_url: Link back to original blog post

    Returns:
        dict with subject_line, section_html, section_text, word_count, cta

    Raises:
        Exception: If Claude API call fails
    """
    try:
        from anthropic import Anthropic
        import markdown
    except ImportError:
        raise ImportError(
            "Required packages not installed. Install with: pip install anthropic markdown"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Build system prompt with tone matching instructions
    system_prompt = f"""You are an email newsletter writer. Generate an email newsletter section from the provided content.

**Source Tone Profile**:
- Formality: {tone.get('formality', 'neutral')}
- Technical Level: {tone.get('technical_level', 'general')}
- Humor Level: {tone.get('humor_level', 'low')}
- Primary Emotion: {tone.get('primary_emotion', 'informative')}

**CRITICAL: Match this tone exactly**. Email should feel like it came from the same author as the source content.

**Email Newsletter Constraints**:
- Subject line: 40-60 characters, compelling and clear
- Body: 500-800 words (target for newsletter section, not full article)
- Structure: Clear sections with headings (H2, H3)
- Scannable: Short paragraphs (2-3 sentences), bullet points where appropriate
- Call-to-action: Link back to full article with compelling CTA
- Tone: Match source but optimize for email (conversational, direct)

**Original Article URL**: {source_url or 'Not provided'}

Return the body in MARKDOWN format (we'll convert to HTML). Return ONLY valid JSON (no markdown fences):
{{
  "subject_line": "Compelling subject line here",
  "section_markdown": "## Heading\\n\\nParagraph...\\n\\n- Bullet point\\n- Another point\\n\\n[Read the full article]({source_url})",
  "word_count": 672,
  "cta": "Read the full article: [link]"
}}"""

    logger.info("Generating email section (content length: %d chars)", len(content))

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

    # Convert markdown to HTML
    section_markdown = result.get("section_markdown", "")
    section_html = markdown.markdown(
        section_markdown,
        extensions=["nl2br", "sane_lists"],
    )

    # Generate plain text version (strip HTML, clean up)
    import re
    section_text = re.sub(r"<[^>]+>", "", section_html)
    section_text = re.sub(r"\n{3,}", "\n\n", section_text)  # Collapse multiple newlines

    # Update word count (count actual words in markdown)
    words = len(section_markdown.split())
    result["word_count"] = words

    # Add HTML and text versions to result
    result["section_html"] = section_html
    result["section_text"] = section_text.strip()

    logger.info("Email section generated (%d words)", words)

    return result


def main() -> dict[str, Any]:
    """
    Main entry point for the email generator tool.

    Returns:
        dict: Email section result.
    """
    parser = argparse.ArgumentParser(description="Generate email newsletter section from content")
    parser.add_argument("--content", help="Markdown content (alternative to stdin)")
    parser.add_argument("--tone", help="Tone analysis JSON string")
    parser.add_argument("--url", default="", help="Source URL to link back to")
    args = parser.parse_args()

    # Get inputs
    if args.content and args.tone:
        content = args.content
        tone = json.loads(args.tone)
    else:
        # Read from stdin (JSON with markdown_content, tone_analysis, source_url fields)
        try:
            stdin_data = json.load(sys.stdin)
            content = stdin_data.get("markdown_content", "")
            tone = stdin_data.get("tone_analysis", {})
            if not args.url:
                args.url = stdin_data.get("source_url", "")
        except json.JSONDecodeError as e:
            logger.error("Failed to parse stdin as JSON: %s", e)
            sys.exit(1)

    logger.info("Starting email generation")

    try:
        result = generate_email_section(content, tone, args.url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except Exception as e:
        logger.error("Email generation failed: %s", str(e))
        error_result = {
            "status": "generation_failed",
            "message": str(e),
            "subject_line": "",
            "section_html": "",
            "section_text": "",
            "word_count": 0,
            "cta": "",
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
