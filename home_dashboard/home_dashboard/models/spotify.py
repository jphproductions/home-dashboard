"""Pydantic models for request/response validation."""

from pydantic import BaseModel
from typing import Optional


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
