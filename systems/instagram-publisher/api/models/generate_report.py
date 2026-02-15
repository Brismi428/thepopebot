"""Pydantic model for generate_report tool."""

from typing import Optional
from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    """Generate markdown summary report."""
    published_dir: Optional[str] = Field(None, description="Path to published result files directory")
    failed_dir: Optional[str] = Field(None, description="Path to failed result files directory")
