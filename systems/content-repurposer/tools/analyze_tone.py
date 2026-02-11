#!/usr/bin/env python3
"""
analyze_tone.py

Analyzes the tone and writing style of content using Claude.
Returns structured tone profile with confidence score.

Usage:
    python analyze_tone.py --content "Blog post content here..."
    echo '{"markdown_content": "..."}' | python analyze_tone.py --stdin

Output:
    JSON with formality, technical_level, humor_level, primary_emotion, confidence, rationale
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tone analysis JSON schema
TONE_SCHEMA = {
    "type": "object",
    "properties": {
        "formality": {
            "type": "string",
            "enum": ["formal", "semi-formal", "casual"],
            "description": "Overall formality level of the writing"
        },
        "technical_level": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced", "expert"],
            "description": "Technical complexity and assumed audience knowledge"
        },
        "humor_level": {
            "type": "string",
            "enum": ["none", "low", "medium", "high"],
            "description": "Presence and intensity of humor or playfulness"
        },
        "primary_emotion": {
            "type": "string",
            "description": "The dominant emotional tone (e.g., informative, inspiring, urgent, playful, serious)"
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence score for this analysis (0.0 = low, 1.0 = high)"
        },
        "rationale": {
            "type": "string",
            "description": "Brief explanation of the tone assessment"
        }
    },
    "required": ["formality", "technical_level", "humor_level", "primary_emotion", "confidence", "rationale"]
}


def get_default_tone() -> Dict[str, Any]:
    """Return default/fallback tone profile."""
    return {
        "formality": "neutral",
        "technical_level": "general",
        "humor_level": "low",
        "primary_emotion": "informative",
        "confidence": 0.5,
        "rationale": "Using default tone profile due to analysis failure or insufficient content"
    }


def analyze_tone_with_claude(content: str, retries: int = 2) -> Dict[str, Any]:
    """
    Analyze content tone using Claude API with structured output.
    
    Args:
        content: Markdown content to analyze
        retries: Number of retry attempts on failure
    
    Returns:
        Dict with tone analysis results
    
    Raises:
        Exception: If analysis fails after all retries
    """
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("anthropic package not installed")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    client = Anthropic(api_key=api_key)
    
    system_prompt = """You are a writing style analyst. Analyze the tone, style, and characteristics of the provided content.

Return your analysis as valid JSON matching this exact structure:
{
  "formality": "formal" | "semi-formal" | "casual",
  "technical_level": "beginner" | "intermediate" | "advanced" | "expert",
  "humor_level": "none" | "low" | "medium" | "high",
  "primary_emotion": "brief description (e.g., informative, inspiring, urgent)",
  "confidence": 0.0 to 1.0,
  "rationale": "brief explanation of your assessment"
}

CRITICAL: Return ONLY valid JSON. No markdown fences, no commentary, no additional text."""
    
    for attempt in range(1, retries + 2):
        try:
            logger.info(f"Tone analysis attempt {attempt}/{retries + 1}")
            
            # Truncate content if too long (keep first 8000 chars)
            analysis_content = content[:8000] if len(content) > 8000 else content
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                temperature=0.2,  # Lower temperature for more consistent analysis
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Analyze the tone of this content:\n\n{analysis_content}"
                }]
            )
            
            response_text = message.content[0].text.strip()
            
            # Strip markdown fences if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]).strip()
            
            # Parse JSON
            tone_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["formality", "technical_level", "humor_level", "primary_emotion", "confidence", "rationale"]
            missing = [f for f in required_fields if f not in tone_data]
            if missing:
                raise ValueError(f"Missing required fields in response: {missing}")
            
            # Validate confidence is a number between 0 and 1
            conf = tone_data["confidence"]
            if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
                logger.warning(f"Invalid confidence value {conf}, defaulting to 0.7")
                tone_data["confidence"] = 0.7
            
            logger.info(f"Tone analysis successful: formality={tone_data['formality']}, confidence={tone_data['confidence']}")
            return tone_data
        
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing failed: {str(e)}"
            logger.warning(f"Attempt {attempt} failed: {error_msg}")
            if attempt > retries:
                raise ValueError(error_msg)
        
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt > retries:
                raise
    
    raise RuntimeError("Unreachable code reached")


def main(content: str) -> Dict[str, Any]:
    """
    Main tone analysis function.
    
    Args:
        content: Markdown content to analyze
    
    Returns:
        Dict with tone analysis or default profile on failure
    """
    # Validate content length
    if not content or len(content.strip()) < 50:
        logger.warning("Content too short for meaningful analysis")
        default = get_default_tone()
        default["rationale"] = "Content too short for analysis (< 50 characters)"
        return default
    
    try:
        return analyze_tone_with_claude(content, retries=1)
    
    except Exception as e:
        logger.error(f"Tone analysis failed: {str(e)}")
        logger.warning("Returning default tone profile")
        default = get_default_tone()
        default["rationale"] = f"Analysis failed ({str(e)[:100]}), using defaults"
        return default


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze tone and writing style of content"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--content",
        help="Content to analyze (direct string)"
    )
    group.add_argument(
        "--stdin",
        action="store_true",
        help="Read JSON from stdin with 'markdown_content' key"
    )
    args = parser.parse_args()
    
    try:
        if args.stdin:
            input_data = json.load(sys.stdin)
            content = input_data.get("markdown_content", "")
        else:
            content = args.content
        
        if not content:
            logger.error("No content provided for analysis")
            print(json.dumps(get_default_tone(), indent=2))
            sys.exit(1)
        
        result = main(content)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    
    except Exception as e:
        logger.exception("Unexpected error during tone analysis")
        error_result = get_default_tone()
        error_result["rationale"] = f"Fatal error: {str(e)}"
        error_result["confidence"] = 0.0
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)
