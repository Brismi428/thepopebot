#!/usr/bin/env python3
"""
assemble_output.py

Merges all generated content into a single JSON output file.

Usage:
    python assemble_output.py --source source.json --tone tone.json --twitter twitter.json --linkedin linkedin.json --email email.json --instagram instagram.json

Output:
    JSON file written to output/{timestamp}-{slug}.json
    Prints summary to stdout
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to URL-safe slug.
    
    Args:
        text: Text to slugify
        max_length: Maximum slug length
    
    Returns:
        Slugified string
    """
    # Lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Strip leading/trailing hyphens
    text = text.strip('-')
    # Limit length
    return text[:max_length]


def assemble_output(
    source_metadata: Dict[str, Any],
    tone_analysis: Dict[str, Any],
    platform_content: Dict[str, Any],
    output_dir: str = "output"
) -> Dict[str, Any]:
    """
    Assemble all content into final JSON structure.
    
    Args:
        source_metadata: Scraped blog post metadata
        tone_analysis: Tone analysis results
        platform_content: Dict with twitter, linkedin, email, instagram keys
        output_dir: Output directory path
    
    Returns:
        Dict with output_path, total_chars, platform_count
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    title = source_metadata.get("title", "untitled")
    slug = slugify(title)
    filename = f"{timestamp}-{slug}.json"
    output_file = output_path / filename
    
    # Build unified structure
    output_data = {
        "source_url": source_metadata.get("url", ""),
        "source_title": source_metadata.get("title", ""),
        "source_author": source_metadata.get("author", ""),
        "source_publish_date": source_metadata.get("publish_date", ""),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tone_analysis": tone_analysis,
        "twitter": platform_content.get("twitter", {}),
        "linkedin": platform_content.get("linkedin", {}),
        "email": platform_content.get("email", {}),
        "instagram": platform_content.get("instagram", {})
    }
    
    # Calculate total characters across all platforms
    total_chars = 0
    platform_count = 0
    
    for platform_name in ["twitter", "linkedin", "email", "instagram"]:
        platform_data = output_data.get(platform_name, {})
        
        # Skip failed platforms
        if platform_data.get("status") == "generation_failed":
            logger.warning(f"Platform {platform_name} generation failed, including error in output")
            continue
        
        platform_count += 1
        
        # Count characters based on platform structure
        if platform_name == "twitter":
            for tweet in platform_data.get("thread", []):
                total_chars += tweet.get("char_count", 0)
        elif platform_name == "linkedin":
            total_chars += platform_data.get("char_count", 0)
        elif platform_name == "email":
            total_chars += len(platform_data.get("section_text", ""))
        elif platform_name == "instagram":
            total_chars += platform_data.get("char_count", 0)
    
    # Write JSON file
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Output written to {output_file}")
    logger.info(f"Total characters: {total_chars}, Successful platforms: {platform_count}/4")
    
    return {
        "output_path": str(output_file),
        "total_chars": total_chars,
        "platform_count": platform_count,
        "status": "success"
    }


def main(
    source_file: str,
    tone_file: str,
    twitter_file: str,
    linkedin_file: str,
    email_file: str,
    instagram_file: str,
    output_dir: str = "output"
) -> Dict[str, Any]:
    """Main assembly function with error handling."""
    
    try:
        # Load all input files
        with open(source_file) as f:
            source_data = json.load(f)
        with open(tone_file) as f:
            tone_data = json.load(f)
        with open(twitter_file) as f:
            twitter_data = json.load(f)
        with open(linkedin_file) as f:
            linkedin_data = json.load(f)
        with open(email_file) as f:
            email_data = json.load(f)
        with open(instagram_file) as f:
            instagram_data = json.load(f)
        
        # Assemble
        platform_content = {
            "twitter": twitter_data,
            "linkedin": linkedin_data,
            "email": email_data,
            "instagram": instagram_data
        }
        
        return assemble_output(source_data, tone_data, platform_content, output_dir)
    
    except Exception as e:
        logger.exception("Assembly failed")
        return {
            "status": "error",
            "error": str(e),
            "output_path": "",
            "total_chars": 0,
            "platform_count": 0
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble final output JSON")
    parser.add_argument("--source", required=True, help="Source metadata JSON file")
    parser.add_argument("--tone", required=True, help="Tone analysis JSON file")
    parser.add_argument("--twitter", required=True, help="Twitter content JSON file")
    parser.add_argument("--linkedin", required=True, help="LinkedIn content JSON file")
    parser.add_argument("--email", required=True, help="Email content JSON file")
    parser.add_argument("--instagram", required=True, help="Instagram content JSON file")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        result = main(
            args.source,
            args.tone,
            args.twitter,
            args.linkedin,
            args.email,
            args.instagram,
            args.output_dir
        )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get("status") == "success" else 1)
    
    except Exception as e:
        logger.exception("Fatal error")
        print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        sys.exit(1)
