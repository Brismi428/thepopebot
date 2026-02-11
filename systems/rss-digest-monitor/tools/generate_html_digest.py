#!/usr/bin/env python
"""
Generate HTML Digest

Generates an HTML email digest grouped by feed source, with plain-text fallback.
Returns a MIME multipart email object ready for SMTP delivery.

Usage:
    python generate_html_digest.py new_posts.json current_date

Inputs:
    - new_posts_path: Path to JSON output from filter_new_posts.py
    - current_date: Date string for subject line (e.g., "February 11, 2026")

Outputs:
    MIME multipart email written to stdout (or null if no posts)
"""

import json
import logging
import sys
from typing import Dict, Any, List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import groupby

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(new_posts_path: str, current_date: str) -> Optional[MIMEMultipart]:
    """
    Generate HTML email digest from new posts.
    
    Args:
        new_posts_path: Path to new_posts JSON from filter_new_posts.py
        current_date: Date string for subject line
        
    Returns:
        MIMEMultipart email object, or None if no new posts
    """
    try:
        # Load new posts
        logger.info(f"Loading new posts from {new_posts_path}")
        with open(new_posts_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        new_posts = data.get("new_posts", [])
        
        if not new_posts:
            logger.info("No new posts - skipping email generation")
            return None
        
        logger.info(f"Generating digest for {len(new_posts)} new posts")
        
        # Group posts by feed name
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for post in sorted(new_posts, key=lambda p: p["feed_name"]):
            feed_name = post["feed_name"]
            if feed_name not in grouped:
                grouped[feed_name] = []
            grouped[feed_name].append(post)
        
        # Generate HTML body
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .post {{
            background: #f8f9fa;
            border-left: 3px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 3px;
        }}
        .post-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .post-title a {{
            color: #2980b9;
            text-decoration: none;
        }}
        .post-title a:hover {{
            text-decoration: underline;
        }}
        .post-summary {{
            color: #555;
            margin: 8px 0;
        }}
        .post-meta {{
            font-size: 0.9em;
            color: #777;
            margin-top: 8px;
        }}
        .feed-count {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>RSS Digest - {current_date}</h1>
    <p class="feed-count"><strong>{len(new_posts)} new posts</strong> from {len(grouped)} feeds</p>
"""
        
        # Generate plain-text body
        text_body = f"RSS Digest - {current_date}\n"
        text_body += "=" * 60 + "\n\n"
        text_body += f"{len(new_posts)} new posts from {len(grouped)} feeds\n\n"
        
        # Add sections for each feed
        for feed_name, posts in grouped.items():
            # HTML section
            html_body += f'    <h2>{feed_name} <span class="feed-count">({len(posts)} posts)</span></h2>\n'
            
            # Plain-text section
            text_body += f"\n{feed_name}\n"
            text_body += "-" * len(feed_name) + "\n"
            
            for post in posts:
                # HTML post card
                html_body += f"""    <div class="post">
        <div class="post-title">
            <a href="{post['link']}" target="_blank">{post['title']}</a>
        </div>
        <div class="post-summary">{post['summary']}</div>
        <div class="post-meta">Published: {post['published']}</div>
    </div>
"""
                
                # Plain-text post
                text_body += f"\n• {post['title']}\n"
                text_body += f"  {post['link']}\n"
                if post['summary']:
                    text_body += f"  {post['summary']}\n"
                text_body += f"  {post['published']}\n"
        
        # Close HTML
        html_body += """</body>
</html>
"""
        
        # Create MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"RSS Digest - {current_date} ({len(new_posts)} new posts)"
        
        # Attach both plain-text and HTML parts
        # Email clients will prefer HTML if they support it
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        logger.info(f"✓ Generated digest email: {len(grouped)} feeds, {len(new_posts)} posts")
        
        return msg
        
    except Exception as e:
        logger.error(f"Fatal error generating digest: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_html_digest.py <new_posts.json> <current_date>")
        sys.exit(1)
    
    posts_path = sys.argv[1]
    date_str = sys.argv[2]
    
    result = main(posts_path, date_str)
    
    if result is None:
        print("null")
        sys.exit(0)
    
    # Output the MIME message as a string
    print(result.as_string())
    sys.exit(0)
