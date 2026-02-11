#!/usr/bin/env python
"""
Send Email via SMTP

Sends an email digest via SMTP with TLS authentication. Supports retry logic
for transient failures.

Usage:
    python send_email_smtp.py email.eml

Inputs:
    - email_path: Path to email message file (from generate_html_digest.py)
    - Environment variables:
        SMTP_HOST: SMTP server hostname
        SMTP_PORT: SMTP server port
        SMTP_USER: SMTP authentication username
        SMTP_PASS: SMTP authentication password
        SMTP_FROM: From address
        SMTP_TO: Comma-separated recipient addresses

Outputs:
    JSON object with sent status, message_id, and error (if any)
"""

import json
import logging
import os
import sys
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.parser import Parser
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(email_path: str) -> Dict[str, Any]:
    """
    Send email via SMTP with TLS authentication and retry logic.
    
    Args:
        email_path: Path to email message file
        
    Returns:
        Dictionary with sent status, message_id, and error
    """
    try:
        # Load SMTP configuration from environment
        smtp_config = {
            "host": os.environ.get("SMTP_HOST"),
            "port": int(os.environ.get("SMTP_PORT", "587")),
            "user": os.environ.get("SMTP_USER"),
            "password": os.environ.get("SMTP_PASS"),
            "from_addr": os.environ.get("SMTP_FROM"),
            "to_addrs": os.environ.get("SMTP_TO", "").split(","),
        }
        
        # Validate required configuration
        missing = []
        for key in ["host", "user", "password", "from_addr"]:
            if not smtp_config.get(key):
                missing.append(key.upper())
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        if not smtp_config["to_addrs"] or not smtp_config["to_addrs"][0]:
            raise ValueError("SMTP_TO must contain at least one recipient address")
        
        # Strip whitespace from recipient addresses
        smtp_config["to_addrs"] = [addr.strip() for addr in smtp_config["to_addrs"]]
        
        logger.info(f"SMTP config loaded: {smtp_config['host']}:{smtp_config['port']}")
        logger.info(f"Recipients: {', '.join(smtp_config['to_addrs'])}")
        
        # Load email message
        logger.info(f"Loading email from {email_path}")
        with open(email_path, 'r', encoding='utf-8') as f:
            email_text = f.read()
        
        # Parse email message
        parser = Parser()
        msg = parser.parsestr(email_text)
        
        # Set From and To headers
        msg["From"] = smtp_config["from_addr"]
        msg["To"] = ", ".join(smtp_config["to_addrs"])
        
        # Attempt to send with retry logic
        max_attempts = 2
        retry_delay = 30
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Connecting to SMTP server (attempt {attempt}/{max_attempts})...")
                
                with smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=30) as server:
                    server.set_debuglevel(0)
                    
                    # Start TLS encryption
                    logger.info("Starting TLS...")
                    server.starttls()
                    
                    # Authenticate
                    logger.info(f"Authenticating as {smtp_config['user']}...")
                    server.login(smtp_config["user"], smtp_config["password"])
                    
                    # Send message
                    logger.info("Sending email...")
                    server.send_message(msg)
                    
                    message_id = msg.get("Message-ID", "")
                    logger.info(f"✓ Email sent successfully (Message-ID: {message_id})")
                    
                    return {
                        "sent": True,
                        "message_id": message_id,
                        "error": None
                    }
                    
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"✗ SMTP authentication failed: {e}")
                logger.error("Check SMTP_USER and SMTP_PASS. For Gmail, use an App Password.")
                
                if attempt < max_attempts:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return {
                        "sent": False,
                        "message_id": "",
                        "error": f"Authentication failed: {e}"
                    }
            
            except smtplib.SMTPException as e:
                logger.error(f"✗ SMTP error: {e}")
                
                if attempt < max_attempts:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return {
                        "sent": False,
                        "message_id": "",
                        "error": f"SMTP error: {e}"
                    }
            
            except Exception as e:
                logger.error(f"✗ Unexpected error: {e}")
                
                if attempt < max_attempts:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return {
                        "sent": False,
                        "message_id": "",
                        "error": f"Send failed: {e}"
                    }
        
        # Should never reach here
        return {
            "sent": False,
            "message_id": "",
            "error": "Maximum retry attempts exceeded"
        }
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return {
            "sent": False,
            "message_id": "",
            "error": str(e)
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_email_smtp.py <email.eml>")
        sys.exit(1)
    
    email_path = sys.argv[1]
    result = main(email_path)
    
    print(json.dumps(result, indent=2))
    
    # Exit with non-zero if send failed
    sys.exit(0 if result["sent"] else 1)
