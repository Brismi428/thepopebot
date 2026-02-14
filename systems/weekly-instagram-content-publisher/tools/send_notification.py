#!/usr/bin/env python3
"""
Send notification to GitHub Issue or Slack.
"""

import argparse
import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def send_github_comment(issue_number: str, summary: str) -> bool:
    """Post comment on GitHub Issue."""
    try:
        import httpx
        
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY", "owner/repo")
        
        if not token:
            logging.error("GITHUB_TOKEN not set")
            return False
        
        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        resp = httpx.post(url, headers=headers, json={"body": summary}, timeout=15)
        resp.raise_for_status()
        
        logging.info(f"GitHub comment posted on issue #{issue_number}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to post GitHub comment: {e}")
        return False


def send_slack_message(channel: str, summary: str) -> bool:
    """Send Slack message."""
    try:
        import httpx
        
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        
        if not webhook_url:
            logging.error("SLACK_WEBHOOK_URL not set")
            return False
        
        resp = httpx.post(webhook_url, json={"text": summary}, timeout=10)
        resp.raise_for_status()
        
        logging.info("Slack notification sent")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send Slack message: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Send notification")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--target", choices=["github", "slack", "stdout"], default="stdout")
    parser.add_argument("--issue-number", help="GitHub issue number (for github target)")
    parser.add_argument("--channel", help="Slack channel (for slack target)")
    
    args = parser.parse_args()
    
    try:
        if args.target == "github":
            if not args.issue_number:
                logging.error("--issue-number required for github target")
                return 1
            success = send_github_comment(args.issue_number, args.summary)
            return 0 if success else 1
        
        elif args.target == "slack":
            success = send_slack_message(args.channel or "general", args.summary)
            return 0 if success else 1
        
        else:  # stdout
            print(args.summary)
            return 0
        
    except Exception as e:
        logging.error(f"Notification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
