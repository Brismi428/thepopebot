"""Pydantic model for log_results tool."""

from pydantic import BaseModel, Field


class LogResultsRequest(BaseModel):
    """CSV logging tool for uptime check results."""
    results: str = Field(..., description="JSON file or string with check results")
    log_file: str = Field(default="logs/uptime_log.csv", description="CSV log file path")
