"""Pydantic model for enrich_content tool."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class EnrichContentRequest(BaseModel):
    """AI-powered content enrichment."""
    content: str = Field(..., description="JSON string with content to enrich")
    enhancement_type: Optional[Literal["hashtags", "alt_text", "caption", "all"]] = Field(
        "hashtags", description="Type of AI enrichment to apply"
    )
