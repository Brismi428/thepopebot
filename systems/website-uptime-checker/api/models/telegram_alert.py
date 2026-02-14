"""Pydantic model for telegram_alert tool."""

from pydantic import BaseModel, Field


class TelegramAlertRequest(BaseModel):
    """Telegram alert tool for website downtime notifications."""
    results: str = Field(..., description="JSON file or string with check results")
