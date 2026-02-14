#!/usr/bin/env python3
"""
Instagram Media Container Creator

Creates an Instagram media container via the Graph API.
This is step 1 of the two-step Instagram publishing process.

Usage:
    python instagram_create_container.py \
        --image-url "https://example.com/image.jpg" \
        --caption "My post caption #hashtag" \
        --business-account-id "17841405309211844" \
        --access-token "$INSTAGRAM_ACCESS_TOKEN"

Returns:
    JSON: {"status": "success", "creation_id": "..."} or
          {"status": "failed", "error_code": "...", "error_message": "..."}
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any

try:
    import httpx
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install httpx tenacity", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Graph API configuration
GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Retry configuration
MAX_RETRIES = 3
RETRY_MIN_WAIT = 2
RETRY_MAX_WAIT = 30


class RetryableError(Exception):
    """Error that should trigger a retry."""
    pass


class NonRetryableError(Exception):
    """Error that should not be retried."""
    pass


def is_retryable_error(exc: Exception) -> bool:
    """Determine if an error should trigger a retry."""
    if isinstance(exc, RetryableError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        # Retry on rate limit and server errors
        return exc.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout)):
        return True
    return False


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type(RetryableError),
    reraise=True,
)
def create_container_with_retry(
    image_url: str,
    caption: str,
    business_account_id: str,
    access_token: str,
) -> dict[str, Any]:
    """
    Create Instagram media container with automatic retry logic.
    
    Args:
        image_url: Publicly accessible image URL
        caption: Post caption with hashtags
        business_account_id: Instagram Business Account ID
        access_token: Instagram Graph API access token
        
    Returns:
        Container creation response
        
    Raises:
        RetryableError: Transient error, should retry
        NonRetryableError: Permanent error, should not retry
    """
    url = f"{GRAPH_API_BASE}/{business_account_id}/media"
    
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }
    
    try:
        logger.info(f"Creating container for account {business_account_id}...")
        logger.debug(f"API URL: {url}")
        logger.debug(f"Image URL: {image_url}")
        logger.debug(f"Caption length: {len(caption)} chars")
        
        resp = httpx.post(url, json=payload, timeout=30.0)
        
        # Check for rate limiting
        if resp.status_code == 429:
            logger.warning("Rate limit exceeded (429), will retry with backoff")
            raise RetryableError(f"Rate limit exceeded: {resp.text}")
        
        # Check for auth/validation errors (do not retry)
        if resp.status_code in (190, 400, 401, 403):
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_message = error_data.get("error", {}).get("message", resp.text)
            error_code = error_data.get("error", {}).get("code", resp.status_code)
            logger.error(f"Non-retryable error {error_code}: {error_message}")
            raise NonRetryableError(f"Auth/validation error {error_code}: {error_message}")
        
        # Raise for other HTTP errors (will retry on 5xx)
        resp.raise_for_status()
        
        # Parse response
        data = resp.json()
        creation_id = data.get("id")
        
        if not creation_id:
            raise NonRetryableError(f"API response missing 'id' field: {data}")
        
        logger.info(f"✓ Container created successfully: {creation_id}")
        return {"creation_id": creation_id}
        
    except (RetryableError, NonRetryableError):
        raise
    except httpx.HTTPStatusError as e:
        # Server errors should retry
        if 500 <= e.response.status_code < 600:
            logger.warning(f"Server error {e.response.status_code}, will retry")
            raise RetryableError(f"Server error: {e}") from e
        raise NonRetryableError(f"HTTP error: {e}") from e
    except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
        logger.warning(f"Timeout error, will retry: {e}")
        raise RetryableError(f"Timeout: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise NonRetryableError(f"Unexpected error: {e}") from e


def create_container(
    image_url: str,
    caption: str,
    business_account_id: str,
    access_token: str,
) -> dict[str, Any]:
    """
    Create Instagram media container (wrapper with error handling).
    
    Returns:
        Success: {"status": "success", "creation_id": "..."}
        Failure: {"status": "failed", "error_code": "...", "error_message": "..."}
    """
    try:
        result = create_container_with_retry(
            image_url=image_url,
            caption=caption,
            business_account_id=business_account_id,
            access_token=access_token,
        )
        return {
            "status": "success",
            "creation_id": result["creation_id"],
        }
    except NonRetryableError as e:
        error_msg = str(e)
        # Extract error code if present
        error_code = "unknown"
        if "error" in error_msg.lower():
            if "190" in error_msg or "auth" in error_msg.lower():
                error_code = "190"
            elif "400" in error_msg or "validation" in error_msg.lower():
                error_code = "400"
        
        return {
            "status": "failed",
            "error_code": error_code,
            "error_message": error_msg,
            "retryable": False,
        }
    except RetryableError as e:
        return {
            "status": "failed",
            "error_code": "429",
            "error_message": f"Rate limit exceeded after {MAX_RETRIES} retries",
            "retryable": True,
        }
    except Exception as e:
        logger.exception(f"Container creation failed: {e}")
        return {
            "status": "failed",
            "error_code": "unknown",
            "error_message": str(e),
            "retryable": False,
        }


def main(
    image_url: str,
    caption: str,
    business_account_id: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    """
    Main entry point.
    
    Args:
        image_url: URL of image to post
        caption: Post caption
        business_account_id: Instagram Business Account ID
        access_token: Access token (defaults to INSTAGRAM_ACCESS_TOKEN env var)
        
    Returns:
        Result dictionary
    """
    # Get access token from environment if not provided
    if not access_token:
        access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    
    if not access_token:
        return {
            "status": "failed",
            "error_code": "config",
            "error_message": "INSTAGRAM_ACCESS_TOKEN not provided",
            "retryable": False,
        }
    
    # Validate inputs
    if not image_url or not caption or not business_account_id:
        return {
            "status": "failed",
            "error_code": "validation",
            "error_message": "Missing required fields: image_url, caption, or business_account_id",
            "retryable": False,
        }
    
    return create_container(
        image_url=image_url,
        caption=caption,
        business_account_id=business_account_id,
        access_token=access_token,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Instagram media container")
    parser.add_argument("--image-url", required=True, help="Image URL")
    parser.add_argument("--caption", required=True, help="Post caption")
    parser.add_argument("--business-account-id", required=True, help="Business Account ID")
    parser.add_argument("--access-token", help="Access token (default: env var)")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    result = main(
        image_url=args.image_url,
        caption=args.caption,
        business_account_id=args.business_account_id,
        access_token=args.access_token,
    )
    
    # Output result
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
    else:
        print(output_json)
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)
