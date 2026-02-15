"""Pydantic model for validate_content tool."""

from pydantic import BaseModel, Field


class ValidateContentRequest(BaseModel):
    """Validate content against Instagram requirements."""
    content: str = Field(..., description="JSON string with caption, image_url, and business_account_id")
