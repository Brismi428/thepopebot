"""Pydantic model for parse_invoice_input tool."""

from pydantic import BaseModel, Field


class ParseInvoiceInputRequest(BaseModel):
    """Parse and validate invoice JSON input with business rule checks."""
    input_path: str = Field(..., description="Path to JSON file or '-' for stdin")
