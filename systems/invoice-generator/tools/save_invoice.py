#!/usr/bin/env python3
"""
Save PDF to output directory with standardized filename and append audit log.

Handles file output with directory creation and audit logging.

Inputs:
    - --pdf-path: Path to source PDF file
    - --client-name: Client name for filename
    - --invoice-date: Invoice date (YYYY-MM-DD)
    - --invoice-number: Invoice number
    - --total: Total amount

Outputs:
    - JSON with {'pdf_path': 'output/...'} to stdout

Exit Codes:
    0: Success
    1: Error during save
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from decimal import Decimal

try:
    from slugify import slugify
except ImportError:
    print("Error: python-slugify not installed. Run: pip install python-slugify", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main(pdf_path: str, client_name: str, invoice_date: str,
         invoice_number: str, total: str) -> dict:
    """Save PDF with standardized filename and append audit log."""
    try:
        # Read PDF bytes
        pdf_bytes = Path(pdf_path).read_bytes()
        logger.info(f"Loaded PDF from {pdf_path} ({len(pdf_bytes)} bytes)")

        # Generate filename: {client-slug}-{YYYY-MM-DD}-{invoice-number}.pdf
        client_slug = slugify(client_name, lowercase=True)
        filename = f"{client_slug}-{invoice_date}-{invoice_number}.pdf"

        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write PDF
        output_path = output_dir / filename
        output_path.write_bytes(pdf_bytes)
        logger.info(f"✓ Saved PDF to {output_path}")

        # Append audit log (best-effort)
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "invoice_number": invoice_number,
                "client": client_name,
                "total": float(Decimal(total)),
                "pdf_path": str(output_path)
            }

            log_file = logs_dir / "invoice_log.jsonl"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

            logger.info(f"✓ Appended audit log entry")

        except Exception as log_error:
            logger.warning(f"Audit log write failed: {log_error}")
            # Continue -- audit log is best-effort

        return {"pdf_path": str(output_path)}

    except FileNotFoundError as e:
        logger.error(f"PDF file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Save failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Save invoice PDF and log")
    parser.add_argument(
        "--pdf-path",
        required=True,
        help="Path to source PDF file"
    )
    parser.add_argument(
        "--client-name",
        required=True,
        help="Client name for filename"
    )
    parser.add_argument(
        "--invoice-date",
        required=True,
        help="Invoice date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--invoice-number",
        required=True,
        help="Invoice number"
    )
    parser.add_argument(
        "--total",
        required=True,
        help="Total invoice amount"
    )
    args = parser.parse_args()

    result = main(
        args.pdf_path,
        args.client_name,
        args.invoice_date,
        args.invoice_number,
        args.total
    )
    print(json.dumps(result, indent=2))
