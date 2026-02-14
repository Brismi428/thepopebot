"""Pydantic model for manage_counter tool."""

from pydantic import BaseModel, Field
from typing import Literal


class ManageCounterRequest(BaseModel):
    """Atomically increment invoice counter with file locking."""
    counter_path: str = Field(..., description="Path to counter JSON file")
    action: Literal["get_next", "get_current"] = Field(default="get_next", description="Action to perform (default: get_next)")
