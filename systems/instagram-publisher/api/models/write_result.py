"""Pydantic model for write_result tool."""

from typing import Optional
from pydantic import BaseModel, Field


class WriteResultRequest(BaseModel):
    """Write publish results to output directories."""
    result_json: str = Field(..., description="JSON string with publish result data")
    output_dir: Optional[str] = Field(None, description="Output directory path (default: output)")
