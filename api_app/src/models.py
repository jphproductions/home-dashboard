"""Pydantic models for request/response validation."""

from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class WeatherResponse(BaseModel):
    """Current weather response."""

    temp: float
    feels_like: float
    condition: str
    icon: str
    location: str
    recommendation: str


class SpotifyStatus(BaseModel):
    """Current Spotify playback status."""

    is_playing: bool
    track_name: Optional[str] = None
    artist_name: Optional[str] = None
    device_name: Optional[str] = None
    progress_ms: Optional[int] = None
    duration_ms: Optional[int] = None


class SpotifyPlayRequest(BaseModel):
    """Request to play a track or context."""

    context_uri: Optional[str] = None
    device_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    error_code: str


class PhoneRingRequest(BaseModel):
    """Request to ring phone."""

    message: Optional[str] = None