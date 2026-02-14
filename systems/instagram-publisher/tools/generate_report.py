#!/usr/bin/env python3
"""
Instagram Publish Report Generator

Aggregates publish results and generates markdown summary reports.

Reads all JSON files from output/published/ and output/failed/ directories,
produces a daily summary report with:
- Success/failure counts
- Error breakdown
- Failed post details
- Recommendations

Usage:
    python generate_report.py \
        --published-dir output/published \
        --failed-dir output/failed \
        --output logs/2026-02-14_publish_report.md

Returns:
    Markdown report string (printed to stdout or written to file)
"""

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_json_files(directory: Path) -> list[dict[str, Any]]:
    """
    Load all JSON files from a directory.
    
    Args:
        directory: Directory path
        
    Returns:
        List of parsed JSON objects
    """
    results = []
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return results
    
    for json_file in directory.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {json_file}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Failed to read {json_file}: {e}")
            continue
    
    return results


def generate_report(
    published_dir: str | Path,
    failed_dir: str | Path,
) -> str:
    """
    Generate markdown publish report.
    
    Args:
        published_dir: Path to published results directory
        failed_dir: Path to failed results directory
        
    Returns:
        Markdown report string
    """
    published_path = Path(published_dir)
    failed_path = Path(failed_dir)
    
    # Load results
    logger.info(f"Loading published results from {published_path}...")
    published = load_json_files(published_path)
    
    logger.info(f"Loading failed results from {failed_path}...")
    failed = load_json_files(failed_path)
    
    total_attempts = len(published) + len(failed)
    success_count = len(published)
    failure_count = len(failed)
    
    # Calculate success rate
    success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 0
    
    # Analyze failure reasons
    error_codes = Counter()
    error_messages = []
    
    for failure in failed:
        error_code = failure.get("error_code", "unknown")
        error_codes[error_code] += 1
        
        error_messages.append({
            "timestamp": failure.get("timestamp", "unknown"),
            "error_code": error_code,
            "error_message": failure.get("error_message", "No message"),
            "caption": failure.get("caption", "")[:50] + "..." if len(failure.get("caption", "")) > 50 else failure.get("caption", ""),
        })
    
    # Build markdown report
    today = date.today().isoformat()
    
    report_lines = [
        f"# Instagram Publish Report - {today}",
        "",
        "## Summary",
        "",
        f"- **Total attempts:** {total_attempts}",
        f"- **Successful:** {success_count} ({success_rate:.1f}%)",
        f"- **Failed:** {failure_count}",
        "",
    ]
    
    # Success details
    if published:
        report_lines.extend([
            "## Published Posts",
            "",
            "| Time | Post ID | Caption |",
            "|------|---------|---------|",
        ])
        
        for post in published:
            timestamp = post.get("timestamp", "unknown")
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = timestamp
            
            post_id = post.get("post_id", "unknown")
            caption = post.get("caption", "")[:40] + "..." if len(post.get("caption", "")) > 40 else post.get("caption", "")
            permalink = post.get("permalink", "")
            
            if permalink:
                post_id_link = f"[{post_id}]({permalink})"
            else:
                post_id_link = post_id
            
            report_lines.append(f"| {time_str} | {post_id_link} | {caption} |")
        
        report_lines.append("")
    
    # Failure details
    if failed:
        report_lines.extend([
            "## Failed Posts",
            "",
        ])
        
        # Error breakdown
        if error_codes:
            report_lines.extend([
                "### Error Breakdown",
                "",
            ])
            
            for error_code, count in error_codes.most_common():
                report_lines.append(f"- **{error_code}:** {count} occurrence(s)")
            
            report_lines.append("")
        
        # Detailed failures
        report_lines.extend([
            "### Details",
            "",
            "| Time | Error Code | Message | Caption |",
            "|------|------------|---------|---------|",
        ])
        
        for failure in error_messages:
            timestamp = failure["timestamp"]
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = timestamp
            
            error_code = failure["error_code"]
            error_msg = failure["error_message"][:50] + "..." if len(failure["error_message"]) > 50 else failure["error_message"]
            caption = failure["caption"]
            
            report_lines.append(f"| {time_str} | {error_code} | {error_msg} | {caption} |")
        
        report_lines.append("")
    
    # Recommendations
    report_lines.extend([
        "## Recommendations",
        "",
    ])
    
    if failure_count == 0:
        report_lines.append("✅ All posts published successfully! No action needed.")
    else:
        # Specific recommendations based on error patterns
        if error_codes.get("429", 0) >= 3:
            report_lines.append(
                f"⚠️ **{error_codes['429']} rate limit errors** detected. Consider reducing "
                "publishing frequency or spreading posts across multiple time windows."
            )
        
        if error_codes.get("190", 0) > 0:
            report_lines.append(
                "🚨 **Authentication errors** detected. Check that `INSTAGRAM_ACCESS_TOKEN` "
                "is valid and has `instagram_content_publish` permission."
            )
        
        if error_codes.get("400", 0) > 0:
            report_lines.append(
                f"⚠️ **{error_codes['400']} validation errors** detected. Review failed posts "
                "for invalid image URLs, caption length issues, or unsupported image formats."
            )
        
        if error_codes.get("100", 0) > 0:
            report_lines.append(
                f"⚠️ **{error_codes['100']} container errors** detected. Container creation "
                "succeeded but publishing failed. Check image format and accessibility."
            )
        
        # Generic recommendation
        report_lines.append("")
        report_lines.append(
            f"💡 **Next steps:** Review failed posts in `{failed_dir}`, fix issues, "
            f"and move corrected JSON files back to `input/queue/` for retry."
        )
    
    report_lines.extend(["", "---", f"*Report generated: {datetime.now().isoformat()}*"])
    
    return "\n".join(report_lines)


def main(
    published_dir: str = "output/published",
    failed_dir: str = "output/failed",
    output_file: str | None = None,
) -> str:
    """
    Main entry point.
    
    Args:
        published_dir: Path to published results
        failed_dir: Path to failed results
        output_file: Output file path (default: stdout)
        
    Returns:
        Report markdown string
    """
    try:
        report = generate_report(published_dir, failed_dir)
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info(f"✓ Report written to {output_path}")
        
        return report
        
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        return f"# Report Generation Failed\n\nError: {str(e)}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Instagram publish report")
    parser.add_argument(
        "--published-dir",
        type=str,
        default="output/published",
        help="Published results directory",
    )
    parser.add_argument(
        "--failed-dir",
        type=str,
        default="output/failed",
        help="Failed results directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)",
    )
    
    args = parser.parse_args()
    
    report_text = main(
        published_dir=args.published_dir,
        failed_dir=args.failed_dir,
        output_file=args.output,
    )
    
    if not args.output:
        print(report_text)
