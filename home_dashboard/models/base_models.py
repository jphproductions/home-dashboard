"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic health check response."""

    status: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with dependency status."""

    status: str = Field(..., description="Overall health status: healthy or unhealthy")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current server timestamp")
    checks: dict[str, str] = Field(..., description="Individual health check results")


class DebugInfo(BaseModel):
    """Debug information about application state."""

    system: dict[str, Any] = Field(..., description="System information")
    state: dict[str, Any] = Field(..., description="Application state")
    config: dict[str, Any] = Field(..., description="Configuration (sanitized)")
    requests: dict[str, int] = Field(..., description="Request statistics")


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    error_code: str
