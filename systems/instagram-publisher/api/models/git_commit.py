"""Pydantic model for git_commit tool."""

from typing import Optional
from pydantic import BaseModel, Field


class GitCommitRequest(BaseModel):
    """Stage files, commit, and push to remote."""
    files: str = Field(..., description="Files to stage (supports glob patterns, comma-separated)")
    message: Optional[str] = Field(None, description="Custom commit message")
    push: bool = Field(False, description="Push to remote after committing")
    auto_message: bool = Field(False, description="Generate a timestamp-based commit message")
