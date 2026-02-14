"""Pydantic model for load_config tool."""

from pydantic import BaseModel, Field


class LoadConfigRequest(BaseModel):
    """Load company branding and tax configuration with sensible defaults."""
    config_path: str = Field(..., description="Path to config JSON file")
