#!/usr/bin/env python3
"""
Generate professional PDF invoice with ReportLab.

Creates a formatted invoice PDF with company branding, itemized line items
table, tax calculations, and payment instructions.

Inputs:
    - --invoice-data: Path to validated invoice JSON
    - --invoice-number: Formatted invoice number
    - --config: Path to config JSON
    - --output: Path for output PDF (or stdout if omitted)

Outputs:
    - PDF bytes to stdout or file

Exit Codes:
    0: Success
    1: Error during PDF generation
"""

import sys
import json
import logging
import io
from pathlib import Path
from decimal import Decimal
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from reportlab.pdfgen import canvas
except ImportError:
    print("Error: reportlab not installed. Run: pip install reportlab", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Warning: pillow not installed. Logo rendering may fail.", file=sys.stderr)


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main(invoice_data_path: str, invoice_number: str, config_path: str,
         output_path: str = None) -> bytes:
    """Generate PDF invoice from validated data."""
    try:
        # Load inputs
        logger.info("Loading invoice data and config")
        invoice_data = json.loads(Path(invoice_data_path).read_text(encoding='utf-8'))
        config = json.loads(Path(config_path).read_text(encoding='utf-8'))

        # Create PDF in memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter  # 612 x 792 points

        # Current Y position (top-down)
        y = height - inch

        # HEADER: Company branding
        logger.info("Rendering company branding")
        logo_path = config.get("company_logo_path")
        if logo_path and Path(logo_path).exists():
            try:
                c.drawImage(
                    logo_path,
                    inch, y - 0.5 * inch,
                    width=2 * inch,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                y -= 0.7 * inch
            except Exception as e:
                logger.warning(f"Failed to render logo: {e}. Skipping.")

        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, y, config.get("company_name", "Your Company"))
        y -= 0.25 * inch

        c.setFont("Helvetica", 10)
        company_address = config.get("company_address", "")
        if company_address:
            c.drawString(inch, y, company_address)
            y -= 0.2 * inch

        company_email = config.get("company_email", "")
        company_phone = config.get("company_phone", "")
        if company_email or company_phone:
            contact_line = f"{company_email}  •  {company_phone}" if company_email and company_phone else (company_email or company_phone)
            c.drawString(inch, y, contact_line)
            y -= 0.4 * inch

        # INVOICE HEADER
        y -= 0.3 * inch
        c.setFont("Helvetica-Bold", 24)
        c.drawString(inch, y, "INVOICE")
        y -= 0.3 * inch

        c.setFont("Helvetica", 10)
        c.drawString(inch, y, f"Invoice Number: {invoice_number}")
        y -= 0.2 * inch
        c.drawString(inch, y, f"Invoice Date: {invoice_data.get('invoice_date', '')}")
        y -= 0.2 * inch
        c.drawString(inch, y, f"Due Date: {invoice_data.get('due_date', '')}")
        y -= 0.4 * inch

        # BILL TO
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, "Bill To:")
        y -= 0.2 * inch

        c.setFont("Helvetica", 10)
        c.drawString(inch, y, invoice_data.get("client_name", ""))
        y -= 0.2 * inch

        client_address = invoice_data.get("client_address", "")
        if client_address:
            # Handle multi-line addresses
            for line in client_address.split('\n'):
                c.drawString(inch, y, line.strip())
                y -= 0.2 * inch

        client_email = invoice_data.get("client_email", "")
        if client_email:
            c.drawString(inch, y, client_email)
            y -= 0.2 * inch

        # PROJECT DESCRIPTION
        y -= 0.2 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, "Project:")
        y -= 0.2 * inch
        c.setFont("Helvetica", 10)
        project_desc = invoice_data.get("project_description", "")
        c.drawString(inch, y, project_desc)
        y -= 0.4 * inch

        # LINE ITEMS TABLE
        logger.info("Rendering line items table")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, "Services:")
        y -= 0.3 * inch

        # Build table data
        currency_symbol = config.get("currency_symbol", "$")
        table_data = [["Description", "Quantity", "Rate", "Amount"]]

        subtotal = Decimal(0)
        for item in invoice_data["line_items"]:
            qty = Decimal(str(item["quantity"]))
            rate = Decimal(str(item["rate"]))
            amount = qty * rate
            subtotal += amount

            table_data.append([
                item["description"],
                f"{qty:.2f}",
                f"{currency_symbol}{rate:.2f}",
                f"{currency_symbol}{amount:.2f}"
            ])

        # Create table
        table = Table(table_data, colWidths=[3.5 * inch, 0.8 * inch, 0.8 * inch, 1 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        table_width, table_height = table.wrap(0, 0)
        table.drawOn(c, inch, y - table_height)
        y -= (table_height + 0.4 * inch)

        # TOTALS
        tax_rate = Decimal(str(config.get("tax_rate", 0)))
        tax = subtotal * tax_rate
        total = subtotal + tax

        totals_x = width - 2.5 * inch
        line_spacing = 0.25 * inch

        c.setFont("Helvetica", 10)
        c.drawString(totals_x, y, "Subtotal:")
        c.drawRightString(width - inch, y, f"{currency_symbol}{subtotal:.2f}")
        y -= line_spacing

        if tax_rate > 0:
            tax_label = config.get("tax_label", f"Tax ({tax_rate * 100:.2f}%)")
            c.drawString(totals_x, y, tax_label)
            c.drawRightString(width - inch, y, f"{currency_symbol}{tax:.2f}")
            y -= line_spacing

        c.setFont("Helvetica-Bold", 12)
        c.drawString(totals_x, y, "Total:")
        c.drawRightString(width - inch, y, f"{currency_symbol}{total:.2f}")
        y -= 0.5 * inch

        # PAYMENT TERMS
        payment_terms = invoice_data.get("payment_terms", "")
        if payment_terms:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(inch, y, "Payment Terms:")
            y -= 0.2 * inch
            c.setFont("Helvetica", 9)
            c.drawString(inch, y, payment_terms)
            y -= 0.3 * inch

        # PAYMENT METHODS
        payment_methods = invoice_data.get("payment_methods", [])
        if payment_methods:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(inch, y, "Payment Methods:")
            y -= 0.2 * inch
            c.setFont("Helvetica", 9)
            for method in payment_methods:
                c.drawString(inch + 0.2 * inch, y, f"• {method}")
                y -= 0.18 * inch
            y -= 0.2 * inch

        # NOTES
        notes = invoice_data.get("notes", "")
        if notes:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(inch, y, "Notes:")
            y -= 0.2 * inch
            c.setFont("Helvetica", 9)
            c.drawString(inch, y, notes)

        # Save PDF
        c.save()
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()

        logger.info(f"✓ PDF generated ({len(pdf_bytes)} bytes)")

        # Output
        if output_path:
            Path(output_path).write_bytes(pdf_bytes)
            logger.info(f"✓ PDF saved to {output_path}")
        else:
            sys.stdout.buffer.write(pdf_bytes)

        return pdf_bytes

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate invoice PDF")
    parser.add_argument(
        "--invoice-data",
        required=True,
        help="Path to validated invoice JSON"
    )
    parser.add_argument(
        "--invoice-number",
        required=True,
        help="Formatted invoice number"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to config JSON"
    )
    parser.add_argument(
        "--output",
        help="Path for output PDF (omit for stdout)"
    )
    args = parser.parse_args()

    main(
        args.invoice_data,
        args.invoice_number,
        args.config,
        args.output
    )
