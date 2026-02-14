"""Pydantic model for save_invoice tool."""

from pydantic import BaseModel, Field


class SaveInvoiceRequest(BaseModel):
    """Save PDF to output directory with standardized filename and append audit log."""
    pdf_path: str = Field(..., description="Path to source PDF file")
    client_name: str = Field(..., description="Client name for filename")
    invoice_date: str = Field(..., description="Invoice date (YYYY-MM-DD)")
    invoice_number: str = Field(..., description="Invoice number")
    total: str = Field(..., description="Total invoice amount")
