"""Spotify Web API service."""

import httpx
from api_app.config import settings
from api_app.models import SpotifyStatus
from api_app.services import tv_tizen_service


# In-memory token cache (for demo; use proper token refresh in production)
_access_token = None


async def _get_access_token(client: httpx.AsyncClient) -> str:
    """
    Get Spotify access token using Client Credentials flow.

    In production, implement proper token refresh logic.
    For now, assumes SPOTIFY_REFRESH_TOKEN is set in .env.

    Args:
        client: Shared HTTP client from dependency injection.

    Returns:
        Access token string.

    Raises:
        Exception if token fetch fails.
    """
    global _access_token

    if _access_token:
        return _access_token

    try:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
            data={"grant_type": "client_credentials"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        _access_token = data["access_token"]
        return _access_token
    except httpx.HTTPError as e:
        raise Exception(f"Spotify auth error: {str(e)}") from e
    except (KeyError, ValueError) as e:
        raise Exception(f"Invalid Spotify auth response: {str(e)}") from e


async def get_current_track(client: httpx.AsyncClient) -> SpotifyStatus:
    """
    Get currently playing track on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.

    Returns:
        SpotifyStatus with current track and playback info.

    Raises:
        Exception if API call fails.
    """
    try:
        token = await _get_access_token(client)
        response = await client.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json() or {}

        is_playing = data.get("is_playing", False)
        item = data.get("item") or {}
        device = data.get("device") or {}

        return SpotifyStatus(
            is_playing=is_playing,
            track_name=item.get("name"),
            artist_name=item.get("artists", [{}])[0].get("name") if item else None,
            device_name=device.get("name"),
            progress_ms=data.get("progress_ms"),
            duration_ms=item.get("duration_ms") if item else None,
        )
    except httpx.HTTPError as e:
        raise Exception(f"Spotify current track error: {str(e)}") from e


async def play(client: httpx.AsyncClient) -> None:
    """Resume playback on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
    """
    try:
        token = await _get_access_token(client)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify play error: {str(e)}") from e


async def pause(client: httpx.AsyncClient) -> None:
    """Pause playback on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
    """
    try:
        token = await _get_access_token(client)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/pause",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify pause error: {str(e)}") from e


async def next_track(client: httpx.AsyncClient) -> None:
    """Skip to next track.

    Args:
        client: Shared HTTP client from dependency injection.
    """
    try:
        token = await _get_access_token(client)
        response = await client.post(
            "https://api.spotify.com/v1/me/player/next",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify next error: {str(e)}") from e


async def previous_track(client: httpx.AsyncClient) -> None:
    """Go to previous track.

    Args:
        client: Shared HTTP client from dependency injection.
    """
    try:
        token = await _get_access_token(client)
        response = await client.post(
            "https://api.spotify.com/v1/me/player/previous",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify previous error: {str(e)}") from e


async def wake_tv_and_play(client: httpx.AsyncClient) -> str:
    """
    Wake TV and transfer current playback to TV device.

    This combines:
    1. Wake TV via Tizen (KEY_POWER).
    2. Transfer Spotify playback to TV device.

    Args:
        client: Shared HTTP client from dependency injection.

    Returns:
        Status message.

    Raises:
        Exception if operation fails.
    """
    try:
        # Wake TV first
        await tv_tizen_service.wake()

        # Transfer playback to TV device
        token = await _get_access_token(client)
        response = await client.put(
            "https://api.spotify.com/v1/me/player",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_ids": [settings.tv_spotify_device_id], "play": True},
            timeout=10.0,
        )
        response.raise_for_status()

        return "TV woken and playback transferred"
    except Exception as e:
        raise Exception(f"Wake and play error: {str(e)}") from e
