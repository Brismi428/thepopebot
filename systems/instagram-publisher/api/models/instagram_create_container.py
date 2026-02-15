"""Pydantic model for instagram_create_container tool."""

from typing import Optional
from pydantic import BaseModel, Field


class InstagramCreateContainerRequest(BaseModel):
    """Create Instagram media container via Graph API."""
    image_url: str = Field(..., description="Public URL to JPEG or PNG image")
    caption: str = Field(..., description="Post caption (max 2,200 characters)")
    business_account_id: str = Field(..., description="Instagram Business Account ID (numeric)")
    access_token: Optional[str] = Field(None, description="Graph API access token (optional, falls back to env var)")
