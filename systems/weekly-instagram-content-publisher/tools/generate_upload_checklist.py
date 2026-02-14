#!/usr/bin/env python3
"""
Generate manual upload checklist with copy-paste ready content.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Generate upload checklist")
    parser.add_argument("--generated-content", required=True)
    parser.add_argument("--output-dir", required=True)
    
    args = parser.parse_args()
    
    try:
        with open(args.generated_content) as f:
            content = json.load(f)
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        checklist = f"""# Instagram Upload Checklist - {date_str}

Use this checklist to manually upload posts to Instagram.

"""
        
        for post in content.get("posts", []):
            if post.get("status") == "failed":
                continue
            
            caption = f"{post.get('hook', '')}\n\n{post.get('caption', '')}\n\n{post.get('cta', '')}\n\n{' '.join(post.get('hashtags', []))}"
            
            checklist += f"""---

## [ ] Post {post['post_id']}: {post.get('type', 'unknown').upper()}

**Caption (copy-paste):**
```
{caption}
```

**Alt Text (copy-paste):**
```
{post.get('alt_text', '')}
```

**Creative Brief:**
{post.get('creative_brief', '')}

**Image Prompt:**
{post.get('image_prompt', '')}

"""
        
        path = output_dir / f"upload_checklist_{date_str}.md"
        path.write_text(checklist)
        
        logging.info(f"Upload checklist generated: {path}")
        print(json.dumps({"path": str(path)}, indent=2))
        return 0
        
    except Exception as e:
        logging.error(f"Failed to generate checklist: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
