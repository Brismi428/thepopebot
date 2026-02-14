"""Pydantic model for monitor tool."""

from pydantic import BaseModel, Field


class MonitorRequest(BaseModel):
    """Website uptime monitor tool."""
    urls: list[str] = Field(..., description="URLs to check")
    timeout: int = Field(default=30, description="Request timeout (seconds)")
