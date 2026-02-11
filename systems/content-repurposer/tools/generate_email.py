#!/usr/bin/env python3
"""
generate_email.py

Generates an email newsletter section from blog content and tone analysis.

Usage:
    python generate_email.py --content-file content.json --tone-file tone.json --source-url URL

Output:
    JSON with subject_line, section_html, section_text, word_count, cta
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any

try:
    from anthropic import Anthropic
    import markdown
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_email_section(
    content: str,
    tone_analysis: Dict[str, Any],
    source_url: str = ""
) -> Dict[str, Any]:
    """Generate email newsletter section matching source tone."""
    
    if not DEPS_AVAILABLE:
        raise ImportError("anthropic and markdown packages required")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    
    system_prompt = f"""You are an email newsletter writer.

Generate an email newsletter section from the provided blog content.

TONE REQUIREMENTS:
- Formality: {tone_analysis.get('formality', 'neutral')}
- Technical level: {tone_analysis.get('technical_level', 'general')}
- Humor: {tone_analysis.get('humor_level', 'low')}
- Emotion: {tone_analysis.get('primary_emotion', 'informative')}

EMAIL BEST PRACTICES:
- Subject line: 40-60 chars, curiosity gap or clear benefit
- Scannable format: clear subheadings, short paragraphs
- Bullet points for lists
- Bold key phrases for emphasis (use **bold** in markdown)
- Direct, conversational tone (slightly more personal than blog)
- Clear call-to-action with link to original post
- Target 500-800 words (3-5 minute read)
- Include brief intro that hooks the reader

Return your response as MARKDOWN format. I will convert it to HTML.

Return ONLY valid JSON:
{{
  "subject_line": "Compelling subject line",
  "content_markdown": "## Subheading\\n\\nContent with **bold** and bullet points:\\n- Point 1\\n- Point 2",
  "cta": "Read the full article here: [link]"
}}"""
    
    user_prompt = f"Blog content to convert into email newsletter section:\n\n{content[:7000]}"
    if source_url:
        user_prompt += f"\n\nOriginal blog post URL (for CTA link): {source_url}"
    
    logger.info("Generating email newsletter section...")
    
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
        if "content_markdown" not in result:
            raise ValueError("Missing 'content_markdown' field in response")
        
        md_content = result["content_markdown"]
        
        # Convert markdown to HTML
        section_html = markdown.markdown(md_content, extensions=['extra', 'nl2br'])
        
        # Plain text version (strip HTML tags roughly)
        import re
        section_text = re.sub(r'<[^>]+>', '', section_html)
        section_text = re.sub(r'\n\n+', '\n\n', section_text).strip()
        
        # Count words
        word_count = len(section_text.split())
        
        logger.info(f"Generated email section: {word_count} words")
        
        return {
            "subject_line": result.get("subject_line", "New Article"),
            "section_html": section_html,
            "section_text": section_text,
            "word_count": word_count,
            "cta": result.get("cta", f"Read more: {source_url}")
        }
    
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise


def main(
    content: str,
    tone_analysis: Dict[str, Any],
    source_url: str = ""
) -> Dict[str, Any]:
    """Main generation function with error handling."""
    
    try:
        return generate_email_section(content, tone_analysis, source_url)
    except Exception as e:
        logger.error(f"Email generation failed: {str(e)}")
        return {
            "status": "generation_failed",
            "error": str(e),
            "subject_line": "",
            "section_html": "",
            "section_text": "",
            "word_count": 0,
            "cta": ""
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate email newsletter section")
    parser.add_argument("--content-file", required=True, help="JSON file with markdown_content")
    parser.add_argument("--tone-file", required=True, help="JSON file with tone analysis")
    parser.add_argument("--source-url", default="", help="Original blog post URL")
    
    args = parser.parse_args()
    
    try:
        with open(args.content_file) as f:
            content_data = json.load(f)
        with open(args.tone_file) as f:
            tone_data = json.load(f)
        
        content = content_data.get("markdown_content", "")
        
        result = main(content, tone_data, args.source_url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        sys.exit(0 if result.get("status") != "generation_failed" else 1)
    
    except Exception as e:
        logger.exception("Fatal error")
        print(json.dumps({"status": "generation_failed", "error": str(e)}, indent=2))
        sys.exit(1)
