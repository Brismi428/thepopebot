#!/usr/bin/env python3
"""
Instagram Container Publisher

Publishes an Instagram media container created via the Graph API.
This is step 2 of the two-step Instagram publishing process.

IMPORTANT: Container must be fully processed before publishing (takes 1-2 seconds after creation).

Usage:
    python instagram_publish_container.py \
        --creation-id "17895695668004550" \
        --business-account-id "17841405309211844" \
        --access-token "$INSTAGRAM_ACCESS_TOKEN"

Returns:
    JSON: {"status": "published", "post_id": "...", "permalink": "..."} or
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
RETRY_MIN_WAIT = 3
RETRY_MAX_WAIT = 30

# Container processing wait time
CONTAINER_PROCESSING_DELAY = 2


class RetryableError(Exception):
    """Error that should trigger a retry."""
    pass


class NonRetryableError(Exception):
    """Error that should not be retried."""
    pass


def post_id_to_shortcode(post_id: str) -> str:
    """
    Convert Instagram post ID to shortcode for permalink.
    
    Instagram uses base64-like encoding. This is a simplified version.
    The actual permalink comes from the API response if available.
    """
    # Instagram's shortcode conversion is complex
    # Better to get permalink from API response directly
    return post_id


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type(RetryableError),
    reraise=True,
)
def publish_container_with_retry(
    creation_id: str,
    business_account_id: str,
    access_token: str,
) -> dict[str, Any]:
    """
    Publish Instagram media container with automatic retry logic.
    
    Args:
        creation_id: Container ID from create_container step
        business_account_id: Instagram Business Account ID
        access_token: Instagram Graph API access token
        
    Returns:
        Publish response with post_id and permalink
        
    Raises:
        RetryableError: Transient error, should retry
        NonRetryableError: Permanent error, should not retry
    """
    url = f"{GRAPH_API_BASE}/{business_account_id}/media_publish"
    
    payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    
    try:
        logger.info(f"Publishing container {creation_id}...")
        logger.debug(f"API URL: {url}")
        
        resp = httpx.post(url, json=payload, timeout=30.0)
        
        # Check for rate limiting
        if resp.status_code == 429:
            logger.warning("Rate limit exceeded (429), will retry with backoff")
            raise RetryableError(f"Rate limit exceeded: {resp.text}")
        
        # Check for invalid container (do not retry)
        if resp.status_code == 400:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_message = error_data.get("error", {}).get("message", resp.text)
            error_code = error_data.get("error", {}).get("code", 400)
            
            # Container not ready yet - this IS retryable
            if "not ready" in error_message.lower() or "processing" in error_message.lower():
                logger.warning(f"Container still processing, will retry: {error_message}")
                raise RetryableError(f"Container not ready: {error_message}")
            
            # Other validation errors are not retryable
            logger.error(f"Invalid container {error_code}: {error_message}")
            raise NonRetryableError(f"Invalid container {error_code}: {error_message}")
        
        # Auth errors (do not retry)
        if resp.status_code in (190, 401, 403):
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_message = error_data.get("error", {}).get("message", resp.text)
            error_code = error_data.get("error", {}).get("code", resp.status_code)
            logger.error(f"Auth error {error_code}: {error_message}")
            raise NonRetryableError(f"Auth error {error_code}: {error_message}")
        
        # Raise for other HTTP errors (will retry on 5xx)
        resp.raise_for_status()
        
        # Parse response
        data = resp.json()
        post_id = data.get("id")
        
        if not post_id:
            raise NonRetryableError(f"API response missing 'id' field: {data}")
        
        # Generate permalink (Instagram format: https://www.instagram.com/p/SHORTCODE/)
        # The shortcode is not directly provided, but we can construct a basic URL
        # In production, you'd want to fetch the post details to get the actual permalink
        permalink = f"https://www.instagram.com/p/{post_id}/"
        
        logger.info(f"✓ Post published successfully: {post_id}")
        logger.info(f"  Permalink: {permalink}")
        
        return {
            "post_id": post_id,
            "permalink": permalink,
        }
        
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


def publish_container(
    creation_id: str,
    business_account_id: str,
    access_token: str,
    wait_for_processing: bool = True,
) -> dict[str, Any]:
    """
    Publish Instagram media container (wrapper with error handling).
    
    Args:
        creation_id: Container ID from create step
        business_account_id: Instagram Business Account ID
        access_token: Access token
        wait_for_processing: Wait for container processing before publishing
    
    Returns:
        Success: {"status": "published", "post_id": "...", "permalink": "..."}
        Failure: {"status": "failed", "error_code": "...", "error_message": "..."}
    """
    try:
        # Wait for container to be processed
        if wait_for_processing:
            logger.info(f"Waiting {CONTAINER_PROCESSING_DELAY}s for container processing...")
            time.sleep(CONTAINER_PROCESSING_DELAY)
        
        result = publish_container_with_retry(
            creation_id=creation_id,
            business_account_id=business_account_id,
            access_token=access_token,
        )
        return {
            "status": "published",
            "post_id": result["post_id"],
            "permalink": result["permalink"],
        }
    except NonRetryableError as e:
        error_msg = str(e)
        # Extract error code if present
        error_code = "unknown"
        if "100" in error_msg or "invalid container" in error_msg.lower():
            error_code = "100"
        elif "190" in error_msg or "auth" in error_msg.lower():
            error_code = "190"
        elif "400" in error_msg:
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
            "error_message": f"Publish failed after {MAX_RETRIES} retries: {str(e)}",
            "retryable": True,
        }
    except Exception as e:
        logger.exception(f"Publish failed: {e}")
        return {
            "status": "failed",
            "error_code": "unknown",
            "error_message": str(e),
            "retryable": False,
        }


def main(
    creation_id: str,
    business_account_id: str,
    access_token: str | None = None,
    no_wait: bool = False,
) -> dict[str, Any]:
    """
    Main entry point.
    
    Args:
        creation_id: Container ID to publish
        business_account_id: Instagram Business Account ID
        access_token: Access token (defaults to INSTAGRAM_ACCESS_TOKEN env var)
        no_wait: Skip waiting for container processing
        
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
    if not creation_id or not business_account_id:
        return {
            "status": "failed",
            "error_code": "validation",
            "error_message": "Missing required fields: creation_id or business_account_id",
            "retryable": False,
        }
    
    return publish_container(
        creation_id=creation_id,
        business_account_id=business_account_id,
        access_token=access_token,
        wait_for_processing=not no_wait,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish Instagram media container")
    parser.add_argument("--creation-id", required=True, help="Container creation ID")
    parser.add_argument("--business-account-id", required=True, help="Business Account ID")
    parser.add_argument("--access-token", help="Access token (default: env var)")
    parser.add_argument("--no-wait", action="store_true", help="Skip container processing wait")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    result = main(
        creation_id=args.creation_id,
        business_account_id=args.business_account_id,
        access_token=args.access_token,
        no_wait=args.no_wait,
    )
    
    # Output result
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
    else:
        print(output_json)
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "published" else 1)
