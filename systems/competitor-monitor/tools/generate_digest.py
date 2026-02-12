#!/usr/bin/env python3
"""
Digest Report Generator

Generates a markdown report from detected changes across all competitors.
Includes summary statistics and detailed per-competitor sections.

Inputs:
    --changes: Paths to changes JSON files (one per competitor)
    --date: Report date in YYYY-MM-DD format
    --output: Output directory for report (default: reports/)

Outputs:
    - Markdown report at {output}/YYYY-MM-DD.md
    - Plain-text email body to stdout (JSON with email_body key)

Exit codes:
    0: Success (report generated, even if no changes)
    1: Fatal error
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_summary(all_changes: List[Dict[str, Any]]) -> str:
    """
    Generate summary section of the report.
    
    Args:
        all_changes: List of changes dicts (one per competitor)
        
    Returns:
        Markdown summary text
    """
    total_competitors = len(all_changes)
    total_new_posts = sum(c["summary"]["new_posts_count"] for c in all_changes)
    total_pricing_changes = sum(c["summary"]["pricing_changes_count"] for c in all_changes)
    total_new_features = sum(c["summary"]["new_features_count"] for c in all_changes)
    
    total_changes = total_new_posts + total_pricing_changes + total_new_features
    
    summary = "## Summary\n\n"
    summary += f"- **Competitors monitored:** {total_competitors}\n"
    summary += f"- **Total changes detected:** {total_changes}\n"
    summary += f"  - New blog posts: {total_new_posts}\n"
    summary += f"  - Pricing changes: {total_pricing_changes}\n"
    summary += f"  - New features: {total_new_features}\n"
    summary += "\n"
    
    if total_changes == 0:
        summary += "_No changes detected this week across all competitors._\n\n"
    
    return summary


def generate_competitor_section(changes: Dict[str, Any]) -> str:
    """
    Generate detailed section for a single competitor.
    
    Args:
        changes: Changes dict for one competitor
        
    Returns:
        Markdown section text
    """
    competitor = changes.get("competitor", "Unknown")
    section = f"## {competitor.replace('-', ' ').title()}\n\n"
    
    # Check if any changes exist
    has_changes = (
        changes["summary"]["new_posts_count"] > 0 or
        changes["summary"]["pricing_changes_count"] > 0 or
        changes["summary"]["new_features_count"] > 0
    )
    
    if not has_changes:
        section += "_No changes detected for this competitor._\n\n"
        return section
    
    # New blog posts
    if changes["new_posts"]:
        section += f"### 📝 New Blog Posts ({len(changes['new_posts'])})\n\n"
        for post in changes["new_posts"]:
            title = post.get("title", "Untitled")
            url = post.get("url", "")
            published = post.get("published", "")
            excerpt = post.get("excerpt", "")
            
            section += f"**{title}**\n\n"
            if url:
                section += f"- URL: {url}\n"
            if published:
                section += f"- Published: {published}\n"
            if excerpt:
                section += f"- Summary: {excerpt}\n"
            section += "\n"
    
    # Pricing changes
    if changes["pricing_changes"]:
        section += f"### 💰 Pricing Changes ({len(changes['pricing_changes'])})\n\n"
        for change in changes["pricing_changes"]:
            plan = change.get("plan", "Unknown Plan")
            old_price = change.get("old_price", "")
            new_price = change.get("new_price", "")
            delta = change.get("delta", "")
            delta_pct = change.get("delta_pct", "")
            
            section += f"**{plan}**\n\n"
            section += f"- Old Price: {old_price}\n"
            section += f"- New Price: {new_price}\n"
            if delta != "unknown":
                section += f"- Change: {delta} ({delta_pct})\n"
            section += "\n"
    
    # New features
    if changes["new_features"]:
        section += f"### ✨ New Features ({len(changes['new_features'])})\n\n"
        for feature in changes["new_features"]:
            title = feature.get("title", "Untitled Feature")
            description = feature.get("description", "")
            url = feature.get("url", "")
            
            section += f"**{title}**\n\n"
            if description:
                section += f"{description}\n\n"
            if url:
                section += f"[Learn more]({url})\n\n"
    
    return section


def generate_markdown_report(all_changes: List[Dict[str, Any]], report_date: str) -> str:
    """
    Generate complete markdown report.
    
    Args:
        all_changes: List of changes dicts (one per competitor)
        report_date: Report date in YYYY-MM-DD format
        
    Returns:
        Complete markdown report text
    """
    report = f"# Competitor Monitor Report - {report_date}\n\n"
    
    report += f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_\n\n"
    report += "---\n\n"
    
    # Add summary
    report += generate_summary(all_changes)
    
    # Add per-competitor sections
    if all_changes:
        report += "---\n\n"
        for changes in sorted(all_changes, key=lambda c: c.get("competitor", "")):
            report += generate_competitor_section(changes)
            report += "---\n\n"
    
    # Add footer
    report += "_This report was generated automatically by the Competitor Monitor system._\n"
    
    return report


def generate_plain_text(markdown_report: str) -> str:
    """
    Generate plain-text version of the report for email body.
    
    Args:
        markdown_report: Markdown report text
        
    Returns:
        Plain-text version
    """
    import re
    
    # Strip markdown formatting
    text = markdown_report
    
    # Remove markdown links [text](url) -> text (url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
    
    # Remove bold **text** -> text
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    
    # Remove italic _text_ -> text
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove headers ### -> plain text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    
    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate digest report from changes")
    parser.add_argument("--changes", nargs="+", required=True, help="Paths to changes JSON files")
    parser.add_argument("--date", required=True, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--output", default="reports", help="Output directory (default: reports/)")
    args = parser.parse_args()
    
    try:
        # Validate date format
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date} (expected YYYY-MM-DD)")
            return 1
        
        # Load all changes files
        all_changes = []
        for changes_path in args.changes:
            path = Path(changes_path)
            if not path.exists():
                logger.warning(f"Changes file not found: {changes_path} (skipping)")
                continue
            
            changes = json.loads(path.read_text(encoding="utf-8"))
            all_changes.append(changes)
            logger.info(f"Loaded changes for: {changes.get('competitor', 'unknown')}")
        
        if not all_changes:
            logger.error("No valid changes files found")
            return 1
        
        # Generate markdown report
        logger.info("Generating markdown report")
        markdown_report = generate_markdown_report(all_changes, args.date)
        
        # Write report to file
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / f"{args.date}.md"
        report_path.write_text(markdown_report, encoding="utf-8")
        logger.info(f"Report written to: {report_path}")
        
        # Generate plain-text version for email
        plain_text = generate_plain_text(markdown_report)
        
        # Output JSON with paths and email body
        result = {
            "report_path": str(report_path.resolve()),
            "email_body": plain_text
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        logger.info("Digest generation complete")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
