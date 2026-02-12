#!/usr/bin/env python3
"""
Email Sender

Sends digest report via SMTP. Supports HTML and plain-text multipart emails.
Optional - only runs if email is enabled in config.

Inputs:
    --subject: Email subject line
    --body-html: HTML email body (optional)
    --body-text: Plain text email body (required)
    --recipients: Comma-separated list of email addresses
    --from-addr: From email address (optional, uses EMAIL_FROM env var)

Outputs:
    JSON to stdout with success status and error message (if failed)

Exit codes:
    0: Success (email sent)
    1: Failed (email not sent)
"""

import argparse
import json
import logging
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_smtp_config() -> bool:
    """
    Check that all required SMTP environment variables are set.
    
    Returns:
        True if all required vars present, False otherwise
    """
    required_vars = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "EMAIL_FROM"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        logger.error(f"Missing required SMTP environment variables: {', '.join(missing)}")
        return False
    
    logger.debug("SMTP configuration validated")
    return True


def send_email_smtp(
    subject: str,
    body_html: str,
    body_text: str,
    recipients: List[str],
    from_addr: str,
    retry: bool = True
) -> dict:
    """
    Send email via SMTP with retry logic.
    
    Args:
        subject: Email subject line
        body_html: HTML email body
        body_text: Plain text email body
        recipients: List of recipient email addresses
        from_addr: From email address
        retry: Whether to retry on transient failures
        
    Returns:
        Dict with success status and error message (if failed)
    """
    # Build MIME multipart message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    
    # Attach plain text and HTML parts
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    
    # SMTP configuration
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    
    # Send email with retry
    max_attempts = 2 if retry else 1
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Connecting to SMTP server: {smtp_host}:{smtp_port} (attempt {attempt}/{max_attempts})")
            
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.set_debuglevel(0)
                
                # Use TLS if port is 587 (common for STARTTLS)
                if smtp_port in (587, 25):
                    logger.debug("Starting TLS")
                    server.starttls()
                
                # Login
                logger.debug(f"Authenticating as: {smtp_user}")
                server.login(smtp_user, smtp_pass)
                
                # Send message
                logger.info(f"Sending email to {len(recipients)} recipient(s)")
                server.send_message(msg)
                
                logger.info("Email sent successfully")
                return {
                    "success": True,
                    "error": None,
                    "attempts": attempt
                }
        
        except (smtplib.SMTPException, OSError, TimeoutError) as e:
            last_error = str(e)
            logger.warning(f"Email send failed (attempt {attempt}/{max_attempts}): {e}")
            
            if attempt < max_attempts:
                logger.info("Retrying in 30 seconds...")
                time.sleep(30)
    
    # All attempts failed
    logger.error(f"Email send failed after {max_attempts} attempts")
    return {
        "success": False,
        "error": last_error,
        "attempts": max_attempts
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Send email via SMTP")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--body-html", default="", help="HTML email body")
    parser.add_argument("--body-text", required=True, help="Plain text email body")
    parser.add_argument("--recipients", required=True, help="Comma-separated email addresses")
    parser.add_argument("--from-addr", default="", help="From email address (uses EMAIL_FROM if not provided)")
    args = parser.parse_args()
    
    try:
        # Validate SMTP configuration
        if not validate_smtp_config():
            result = {
                "success": False,
                "error": "Missing SMTP configuration (check environment variables)"
            }
            print(json.dumps(result, indent=2))
            return 1
        
        # Parse recipients
        recipients = [r.strip() for r in args.recipients.split(",") if r.strip()]
        if not recipients:
            logger.error("No valid recipients provided")
            result = {
                "success": False,
                "error": "No valid recipients"
            }
            print(json.dumps(result, indent=2))
            return 1
        
        # Determine from address
        from_addr = args.from_addr or os.environ.get("EMAIL_FROM", "")
        if not from_addr:
            logger.error("No from address specified (use --from-addr or set EMAIL_FROM)")
            result = {
                "success": False,
                "error": "No from address"
            }
            print(json.dumps(result, indent=2))
            return 1
        
        # Send email
        logger.info(f"Sending email: '{args.subject}' to {len(recipients)} recipient(s)")
        result = send_email_smtp(
            subject=args.subject,
            body_html=args.body_html,
            body_text=args.body_text,
            recipients=recipients,
            from_addr=from_addr,
            retry=True
        )
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
        return 0 if result["success"] else 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
