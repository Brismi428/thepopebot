"""
Assemble Output — Merge all generated content into final JSON file

Combines source metadata, tone analysis, and all platform content into a single
unified JSON structure and writes to output/{timestamp}-{slug}.json.

Inputs:
    - source_metadata (dict): {url, title, author, publish_date}
    - tone_analysis (dict): Full tone profile
    - platform_content (dict): {twitter, linkedin, email, instagram}

Outputs:
    - JSON: {output_path, total_chars, platform_count}

Usage:
    python assemble_output.py --source '{}' --tone '{}' --platforms '{}'

Environment Variables:
    None required
"""

import argparse
import json
import logging
import pathlib
import sys
from datetime import datetime
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        str: Slugified text (lowercase, hyphens, alphanumeric only)
    """
    import re

    # Lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r"\s+", "-", slug)
    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    # Collapse multiple hyphens
    slug = re.sub(r"\-+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Truncate to reasonable length
    return slug[:50]


def assemble_output(
    source_metadata: dict[str, Any],
    tone_analysis: dict[str, Any],
    platform_content: dict[str, Any],
    output_dir: str = "output",
) -> dict[str, Any]:
    """
    Merge all content into final JSON file.

    Args:
        source_metadata: Source URL, title, author, publish date
        tone_analysis: Tone profile from analyze_tone.py
        platform_content: Generated content for all platforms
        output_dir: Directory to write output file (default: output/)

    Returns:
        dict with output_path, total_chars, platform_count

    Raises:
        Exception: If JSON serialization or file write fails
    """
    # Build unified structure
    output_data = {
        "source_url": source_metadata.get("url", ""),
        "source_title": source_metadata.get("title", "Untitled"),
        "source_author": source_metadata.get("author", ""),
        "source_publish_date": source_metadata.get("publish_date", ""),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tone_analysis": tone_analysis,
        "twitter": platform_content.get("twitter", {}),
        "linkedin": platform_content.get("linkedin", {}),
        "email": platform_content.get("email", {}),
        "instagram": platform_content.get("instagram", {}),
    }

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    slug = slugify(source_metadata.get("title", "untitled"))
    filename = f"{timestamp}-{slug}.json"

    # Create output directory if it doesn't exist
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    full_path = output_path / filename

    logger.info("Writing output to: %s", full_path)

    # Write JSON with pretty formatting
    try:
        with full_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to write output file: %s", str(e))
        # Print to stdout as fallback
        print("\n=== OUTPUT (file write failed, printing to stdout) ===")
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
        print("=== END OUTPUT ===\n")
        raise

    # Calculate summary stats
    total_chars = len(json.dumps(output_data))
    platform_count = sum(
        1
        for key in ["twitter", "linkedin", "email", "instagram"]
        if platform_content.get(key) and platform_content[key].get("status") != "generation_failed"
    )

    result = {
        "output_path": str(full_path.resolve()),
        "total_chars": total_chars,
        "platform_count": platform_count,
    }

    logger.info(
        "Output assembled: %s (%d chars, %d platforms)", full_path.name, total_chars, platform_count
    )

    return result


def main() -> dict[str, Any]:
    """
    Main entry point for the assembly tool.

    Returns:
        dict: Assembly result with output path and stats.
    """
    parser = argparse.ArgumentParser(description="Assemble final output JSON from all components")
    parser.add_argument("--source", help="Source metadata JSON string")
    parser.add_argument("--tone", help="Tone analysis JSON string")
    parser.add_argument("--platforms", help="Platform content JSON string")
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output/)")
    args = parser.parse_args()

    # Get inputs
    if args.source and args.tone and args.platforms:
        source_metadata = json.loads(args.source)
        tone_analysis = json.loads(args.tone)
        platform_content = json.loads(args.platforms)
    else:
        # Read from stdin (JSON with all fields)
        try:
            stdin_data = json.load(sys.stdin)
            source_metadata = stdin_data.get("source_metadata", {})
            tone_analysis = stdin_data.get("tone_analysis", {})
            platform_content = stdin_data.get("platform_content", {})
        except json.JSONDecodeError as e:
            logger.error("Failed to parse stdin as JSON: %s", e)
            sys.exit(1)

    logger.info("Starting output assembly")

    try:
        result = assemble_output(source_metadata, tone_analysis, platform_content, args.output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except Exception as e:
        logger.error("Output assembly failed: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
