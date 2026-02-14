#!/usr/bin/env python3
"""
Generate human-readable Markdown and machine-readable JSON content packs.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def generate_markdown(content: dict, review: dict, theme: str) -> str:
    """Generate Markdown content pack."""
    md = f"""# Instagram Content Pack
    
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
**Weekly Theme:** {theme}
**Total Posts:** {len(content.get('posts', []))}
**Quality Score:** {review.get('overall_score', 0)}/100 - {review.get('pass_fail', 'UNKNOWN')}

---

"""
    
    for post in content.get("posts", []):
        if post.get("status") == "failed":
            md += f"## Post {post['post_id']} - FAILED\n\nError: {post.get('error', 'Unknown')}\n\n---\n\n"
            continue
        
        md += f"""## Post {post['post_id']}: {post.get('type', 'unknown').upper()}

**Hook:** {post.get('hook', '')}

**Caption:**
{post.get('caption', '')}

**CTA:** {post.get('cta', '')}

**Hashtags:**
{' '.join(post.get('hashtags', []))}

**Alt Text:** {post.get('alt_text', '')}

**Creative Brief:**
{post.get('creative_brief', '')}

**Image Prompt:**
{post.get('image_prompt', '')}

---

"""
    
    return md


def main():
    parser = argparse.ArgumentParser(description="Generate content pack")
    parser.add_argument("--generated-content", required=True)
    parser.add_argument("--review-report", required=True)
    parser.add_argument("--weekly-theme", required=True)
    parser.add_argument("--output-dir", required=True)
    
    args = parser.parse_args()
    
    try:
        with open(args.generated_content) as f:
            content = json.load(f)
        
        with open(args.review_report) as f:
            review = json.load(f)
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Generate Markdown
        md = generate_markdown(content, review, args.weekly_theme)
        md_path = output_dir / f"content_pack_{date_str}.md"
        md_path.write_text(md)
        
        # Write JSON
        json_path = output_dir / f"content_pack_{date_str}.json"
        json_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "theme": args.weekly_theme,
                "total_posts": len(content.get("posts", [])),
                "quality_score": review.get("overall_score", 0)
            },
            "posts": content.get("posts", [])
        }
        json_path.write_text(json.dumps(json_data, indent=2))
        
        logging.info(f"Content pack generated: {md_path}")
        print(json.dumps({"md": str(md_path), "json": str(json_path)}, indent=2))
        return 0
        
    except Exception as e:
        logging.error(f"Failed to generate content pack: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
