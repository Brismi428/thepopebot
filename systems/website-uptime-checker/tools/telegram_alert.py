"""
Telegram alert tool for website downtime notifications.

Sends Telegram messages when monitored sites go down.
Optional: only runs if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_alert(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Send a Telegram message.
    
    Args:
        bot_token: Telegram bot token from @BotFather
        chat_id: Telegram chat ID for the recipient
        message: Message text to send
    
    Returns:
        True on success, False on failure.
    """
    url = TELEGRAM_API.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logging.info("Telegram alert sent successfully")
        return True
    except requests.RequestException as exc:
        logging.error(f"Failed to send Telegram alert: {exc}")
        return False


def main():
    """Main entry point for the Telegram alert tool."""
    parser = argparse.ArgumentParser(description="Send Telegram alerts for down sites")
    parser.add_argument("--results", required=True, help="JSON file or string with check results")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Get credentials from environment
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        logging.info("Telegram credentials not configured, skipping alerts")
        sys.exit(0)
    
    # Parse results
    try:
        results_path = Path(args.results)
        if results_path.exists():
            results = json.loads(results_path.read_text())
        else:
            results = json.loads(args.results)
    except Exception as exc:
        logging.error(f"Failed to parse results: {exc}")
        sys.exit(1)
    
    # Filter down sites
    down_sites = [r for r in results if not r["is_up"]]
    
    if not down_sites:
        logging.info("All sites are up, no alerts needed")
        sys.exit(0)
    
    # Send alert for each down site
    for site in down_sites:
        status_msg = f"status code {site['status_code']}" if site["status_code"] > 0 else "connection failed"
        message = (
            f"⚠️ <b>WEBSITE DOWN ALERT</b>\n\n"
            f"<b>URL:</b> {site['url']}\n"
            f"<b>Status:</b> {status_msg}\n"
            f"<b>Timestamp:</b> {site['timestamp']}\n"
        )
        send_alert(bot_token, chat_id, message)
    
    logging.info(f"Sent {len(down_sites)} alert(s)")


if __name__ == "__main__":
    main()
