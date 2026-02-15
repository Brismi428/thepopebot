"""Pydantic model for instagram_publish_container tool."""

from typing import Optional
from pydantic import BaseModel, Field


class InstagramPublishContainerRequest(BaseModel):
    """Publish container to make Instagram post live."""
    creation_id: str = Field(..., description="Container creation ID from create container step")
    business_account_id: str = Field(..., description="Instagram Business Account ID (numeric)")
    access_token: Optional[str] = Field(None, description="Graph API access token (optional, falls back to env var)")
