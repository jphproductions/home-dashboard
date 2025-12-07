"""Pydantic models for request/response validation."""

from pydantic import BaseModel
from typing import Optional


class PhoneRingRequest(BaseModel):
    """Request to ring phone."""

    message: Optional[str] = None
