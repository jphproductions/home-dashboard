"""Pydantic models for request/response validation."""

from pydantic import BaseModel


class SpotifyPlaybackState(BaseModel):
    """Current Spotify playback status."""

    is_playing: bool
    track_name: str | None = None
    artist_name: str | None = None
    device_name: str | None = None
    progress_ms: int | None = None
    duration_ms: int | None = None
