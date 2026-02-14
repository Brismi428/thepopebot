#!/usr/bin/env python3
"""
Instagram Content Validator

Validates Instagram content payloads against API requirements:
- Caption length (max 2,200 characters)
- Hashtag count (max 30)
- Image URL accessibility (HTTP HEAD request)
- Required fields presence and format
- Image format validation (JPEG/PNG only)

Usage:
    python validate_content.py --content '{"caption": "...", "image_url": "...", ...}'
    python validate_content.py --file input/queue/post.json

Returns:
    JSON: {"is_valid": bool, "errors": list[str], "warnings": list[str]}
"""

import argparse
import json
import logging
import re
import sys
from typing import Any
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
MAX_CAPTION_LENGTH = 2200
MAX_HASHTAGS = 30
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]
REQUIRED_FIELDS = ["caption", "image_url", "business_account_id"]


def extract_hashtags(text: str) -> list[str]:
    """Extract all hashtags from text."""
    return re.findall(r"#\w+", text)


def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL format."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme in ("http", "https"):
            return False, "URL must use http or https scheme"
        if not parsed.netloc:
            return False, "URL must have a domain"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL format: {e}"


def check_image_accessibility(url: str, timeout: int = 5) -> tuple[bool, str, str]:
    """
    Send HEAD request to check if image URL is accessible.
    
    Returns:
        (is_accessible, error_message, content_type)
    """
    try:
        resp = httpx.head(url, timeout=timeout, follow_redirects=True)
        
        if resp.status_code != 200:
            return False, f"Image URL returned status {resp.status_code}", ""
        
        content_type = resp.headers.get("content-type", "").lower()
        
        # Check if it's an image
        if not content_type.startswith("image/"):
            return False, f"URL does not point to an image (Content-Type: {content_type})", content_type
        
        return True, "", content_type
        
    except httpx.TimeoutException:
        return False, f"Image URL timed out after {timeout} seconds", ""
    except httpx.RequestError as e:
        return False, f"Image URL fetch failed: {str(e)}", ""
    except Exception as e:
        return False, f"Unexpected error checking image URL: {str(e)}", ""


def validate_content(content: dict[str, Any]) -> dict[str, Any]:
    """
    Validate Instagram content payload.
    
    Args:
        content: Content payload dictionary
        
    Returns:
        Validation report: {is_valid: bool, errors: list, warnings: list}
    """
    errors = []
    warnings = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in content or not content[field]:
            errors.append(f"Missing required field: {field}")
    
    # If missing required fields, return early
    if errors:
        return {"is_valid": False, "errors": errors, "warnings": warnings}
    
    # Validate caption length
    caption = content.get("caption", "")
    if len(caption) > MAX_CAPTION_LENGTH:
        errors.append(f"Caption exceeds {MAX_CAPTION_LENGTH} character limit (current: {len(caption)})")
    
    if len(caption) == 0:
        errors.append("Caption cannot be empty")
    
    # Extract and count hashtags
    hashtags_in_caption = extract_hashtags(caption)
    hashtags_array = content.get("hashtags", [])
    
    # Combine hashtags from both sources and deduplicate
    all_hashtags = list(set(hashtags_in_caption + hashtags_array))
    
    if len(all_hashtags) > MAX_HASHTAGS:
        errors.append(f"Too many hashtags: {len(all_hashtags)} (max {MAX_HASHTAGS})")
    
    if len(all_hashtags) == 0:
        warnings.append("No hashtags found - consider adding some for better reach")
    
    # Validate image URL format
    image_url = content.get("image_url", "")
    url_valid, url_error = validate_url(image_url)
    
    if not url_valid:
        errors.append(f"Invalid image URL: {url_error}")
        # Don't check accessibility if URL format is invalid
        return {"is_valid": False, "errors": errors, "warnings": warnings}
    
    # Check image accessibility
    logger.info(f"Checking image URL accessibility: {image_url}")
    accessible, access_error, content_type = check_image_accessibility(image_url)
    
    if not accessible:
        errors.append(f"Image URL not accessible: {access_error}")
    elif content_type and not any(ct in content_type for ct in ALLOWED_IMAGE_TYPES):
        errors.append(f"Unsupported image format: {content_type} (must be JPEG or PNG)")
    
    # Validate business_account_id format (should be numeric)
    account_id = str(content.get("business_account_id", ""))
    if not account_id.isdigit():
        errors.append(f"Invalid business_account_id format: must be numeric (got: {account_id})")
    
    # Optional field warnings
    if not content.get("alt_text"):
        warnings.append("No alt_text provided - consider adding for accessibility")
    
    # Determine overall validity
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
    }


def main(content: dict[str, Any] | None = None, file_path: str | None = None) -> dict[str, Any]:
    """
    Main entry point for content validation.
    
    Args:
        content: Content payload dictionary (if provided directly)
        file_path: Path to JSON file containing content payload
        
    Returns:
        Validation report dictionary
    """
    try:
        # Load content from file if provided
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        
        if not content:
            raise ValueError("No content provided (use --content or --file)")
        
        # Validate
        result = validate_content(content)
        
        # Log results
        if result["is_valid"]:
            logger.info("✓ Content validation PASSED")
        else:
            logger.error("✗ Content validation FAILED")
            for error in result["errors"]:
                logger.error(f"  - {error}")
        
        for warning in result["warnings"]:
            logger.warning(f"  - {warning}")
        
        return result
        
    except Exception as e:
        logger.exception(f"Validation failed with exception: {e}")
        return {
            "is_valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": [],
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Instagram content payload")
    parser.add_argument("--content", type=str, help="JSON content payload string")
    parser.add_argument("--file", type=str, help="Path to JSON file")
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    content_dict = None
    if args.content:
        content_dict = json.loads(args.content)
    
    result = main(content=content_dict, file_path=args.file)
    
    # Output result
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
    else:
        print(output_json)
    
    # Exit with appropriate code
    sys.exit(0 if result["is_valid"] else 1)
