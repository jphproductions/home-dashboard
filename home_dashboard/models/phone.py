"""Pydantic models for request/response validation."""

from pydantic import BaseModel


class PhoneRingRequest(BaseModel):
    """Request to ring phone."""

    message: str | None = None
