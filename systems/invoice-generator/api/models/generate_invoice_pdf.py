"""Pydantic model for generate_invoice_pdf tool."""

from pydantic import BaseModel, Field


class GenerateInvoicePdfRequest(BaseModel):
    """Generate professional PDF invoice with ReportLab."""
    invoice_data: str = Field(..., description="Path to validated invoice JSON")
    invoice_number: str = Field(..., description="Formatted invoice number")
    config: str = Field(..., description="Path to config JSON")
