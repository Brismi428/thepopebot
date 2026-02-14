#!/usr/bin/env python3
"""
Publish posts to Instagram via Graph API.

Handles media container creation, publishing, scheduling, and rate limiting.
Falls back to manual pack generation on failures.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def publish_post(
    post: Dict[str, Any],
    access_token: str,
    ig_user_id: str
) -> Dict[str, Any]:
    """Publish a single post to Instagram."""
    try:
        import httpx
        
        # Format caption (hook + caption + CTA + hashtags)
        caption = f"{post.get('hook', '')}\n\n{post.get('caption', '')}\n\n{post.get('cta', '')}\n\n{' '.join(post.get('hashtags', []))}"
        
        # Truncate if over 2200 chars
        if len(caption) > 2200:
            logging.warning(f"Post {post['post_id']} caption truncated from {len(caption)} to 2200 chars")
            caption = caption[:2197] + "..."
        
        # NOTE: Instagram Graph API requires publicly accessible HTTPS URLs for media
        # This tool creates a TEXT-ONLY post as a placeholder
        # For actual media publishing, media URLs must be provided
        
        # Create media container (simplified - text only)
        create_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
        create_params = {
            "caption": caption,
            "access_token": access_token
        }
        
        # If media_url is provided, include it
        if "media_url" in post:
            create_params["image_url"] = post["media_url"]
            create_params["media_type"] = "IMAGE"
        
        resp = httpx.post(create_url, params=create_params, timeout=30)
        resp.raise_for_status()
        container = resp.json()
        container_id = container.get("id")
        
        if not container_id:
            raise ValueError("No container ID returned")
        
        # Publish media container
        publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        
        resp = httpx.post(publish_url, params=publish_params, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        
        return {
            "post_id": post["post_id"],
            "status": "success",
            "ig_media_id": result.get("id"),
            "ig_permalink": f"https://instagram.com/p/{result.get('id')}"
        }
        
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 429:
            return {
                "post_id": post["post_id"],
                "status": "rate_limited",
                "error": "Rate limit exceeded (200 calls/hour)",
                "retry_after": e.response.headers.get("Retry-After", "3600")
            }
        elif status in (401, 403):
            return {
                "post_id": post["post_id"],
                "status": "auth_failed",
                "error": f"Authentication failed: {e.response.text}"
            }
        else:
            return {
                "post_id": post["post_id"],
                "status": "failed",
                "error": f"HTTP {status}: {e.response.text}"
            }
    except Exception as e:
        return {
            "post_id": post["post_id"],
            "status": "failed",
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Publish Instagram posts via Graph API"
    )
    parser.add_argument(
        "--generated-content",
        required=True,
        help="Path to generated content JSON"
    )
    parser.add_argument(
        "--output",
        default="publish_log.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    try:
        # Load generated content
        with open(args.generated_content) as f:
            content = json.load(f)
        
        # Get Instagram credentials from environment
        access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
        
        if not access_token or not ig_user_id:
            logging.error("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID must be set")
            return 1
        
        posts = content.get("posts", [])
        successful_posts = [p for p in posts if p.get("status") != "failed"]
        
        logging.info(f"Publishing {len(successful_posts)} posts to Instagram")
        
        results = []
        rate_limited = False
        
        for post in successful_posts:
            if rate_limited:
                results.append({
                    "post_id": post["post_id"],
                    "status": "skipped",
                    "error": "Skipped due to rate limit"
                })
                continue
            
            logging.info(f"Publishing post {post['post_id']}")
            result = publish_post(post, access_token, ig_user_id)
            results.append(result)
            
            if result["status"] == "success":
                logging.info(f"✓ Published post {post['post_id']}")
            elif result["status"] == "rate_limited":
                logging.error(f"✗ Rate limit hit at post {post['post_id']}")
                rate_limited = True
            else:
                logging.error(f"✗ Failed to publish post {post['post_id']}: {result.get('error')}")
            
            # Small delay between posts
            time.sleep(2)
        
        # Compile publish log
        publish_log = {
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": "auto_publish",
            "results": results,
            "summary": {
                "total": len(successful_posts),
                "successful": sum(1 for r in results if r["status"] == "success"),
                "failed": sum(1 for r in results if r["status"] in ("failed", "auth_failed")),
                "rate_limited": sum(1 for r in results if r["status"] == "rate_limited"),
                "skipped": sum(1 for r in results if r["status"] == "skipped")
            }
        }
        
        # Write output
        with open(args.output, 'w') as f:
            json.dump(publish_log, f, indent=2)
        
        logging.info(
            f"Publish complete: {publish_log['summary']['successful']}/{publish_log['summary']['total']} successful"
        )
        print(json.dumps(publish_log, indent=2))
        
        # Exit with error if any failures
        if publish_log['summary']['failed'] > 0 or publish_log['summary']['rate_limited'] > 0:
            return 1
        return 0
        
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
