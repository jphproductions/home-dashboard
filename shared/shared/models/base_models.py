"""Pydantic models for request/response validation."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    error_code: str
