"""Spotify Web API service."""

import httpx
import time
import threading
from pathlib import Path
from home_dashboard.config import Settings, get_settings
from home_dashboard.models import SpotifyStatus
from home_dashboard.services import tv_tizen_service
from home_dashboard.state_managers import SpotifyAuthManager


# NOTE: Global variables are deprecated and will be removed in future
# Use SpotifyAuthManager via dependency injection instead
# Path to store refresh token persistently
TOKEN_FILE = Path.home() / ".spotify_refresh_token"


def _load_refresh_token() -> str | None:
    """Load refresh token from file."""
    if TOKEN_FILE.exists():
        try:
            return TOKEN_FILE.read_text().strip()
        except Exception:
            return None
    return None


def _save_refresh_token(refresh_token: str) -> None:
    """Save refresh token to file."""
    try:
        TOKEN_FILE.write_text(refresh_token)
        TOKEN_FILE.chmod(0o600)  # Secure file permissions
    except Exception as e:
        raise Exception(f"Failed to save refresh token: {str(e)}") from e


def is_authenticated(settings: Settings | None = None) -> bool:
    """Check if we have a refresh token available.
    
    Args:
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()
    return _load_refresh_token() is not None or bool(settings.spotify_refresh_token)


async def _get_access_token(
    client: httpx.AsyncClient, 
    auth_manager: SpotifyAuthManager,
    settings: Settings | None = None
) -> str:
    """
    Get Spotify access token using refresh token flow.

    Automatically refreshes the token when expired.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)

    Returns:
        Access token string.

    Raises:
        Exception if token fetch/refresh fails.
    """
    if settings is None:
        settings = get_settings()
    
    # Check if we have a valid cached token
    cached_token = await auth_manager.get_token()
    if cached_token:
        return cached_token

    # Get refresh token from file or settings
    refresh_token = _load_refresh_token() or settings.spotify_refresh_token
    if not refresh_token:
        raise Exception("No refresh token available. Please authenticate first.")

    try:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        
        # Store in manager
        await auth_manager.set_token(access_token, expires_in)

        # If a new refresh token is provided, save it
        if "refresh_token" in data:
            _save_refresh_token(data["refresh_token"])

        return access_token
    except httpx.HTTPError as e:
        raise Exception(f"Spotify auth error: {str(e)}") from e
    except (KeyError, ValueError) as e:
        raise Exception(f"Invalid Spotify auth response: {str(e)}") from e


async def get_current_track(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> SpotifyStatus:
    """
    Get current playback state on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)

    Returns:
        SpotifyStatus with current track and playback info.

    Raises:
        Exception if API call fails.
    """
    if settings is None:
        settings = get_settings()
    
    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.get(
            "https://api.spotify.com/v1/me/player",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json() if response.status_code != 204 else {}

        is_playing = data.get("is_playing", False)
        item = data.get("item") or {}
        device = data.get("device") or {}

        return SpotifyStatus(
            is_playing=is_playing,
            track_name=item.get("name"),
            artist_name=item.get("artists", [{}])[0].get("name") if item.get("artists") else None,
            device_name=device.get("name"),
            progress_ms=data.get("progress_ms"),
            duration_ms=item.get("duration_ms") if item else None,
        )
    except httpx.HTTPError as e:
        raise Exception(f"Spotify playback state error: {str(e)}") from e


async def play(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """Resume playback on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()
    
    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify play error: {str(e)}") from e


async def pause(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """Pause playback on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()
    
    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/pause",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify pause error: {str(e)}") from e


async def next_track(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """Skip to next track.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()
    
    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.post(
            "https://api.spotify.com/v1/me/player/next",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify next error: {str(e)}") from e


async def previous_track(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """Go to previous track.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()
    
    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.post(
            "https://api.spotify.com/v1/me/player/previous",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Spotify previous error: {str(e)}") from e


async def wake_tv_and_play(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, tv_manager: 'TVStateManager', settings: Settings | None = None) -> str:
    """
    Wake TV and transfer current playback to TV device.

    This combines:
    1. Wake TV via Tizen (KEY_POWER).
    2. Transfer Spotify playback to TV device.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        tv_manager: TV state manager (for failure tracking)
        settings: Settings instance (defaults to singleton)

    Returns:
        Status message.

    Raises:
        Exception if operation fails.
    """
    if settings is None:
        settings = get_settings()
    
    try:
        # Wake TV first
        await tv_tizen_service.wake(settings, tv_manager)

        # Transfer playback to TV device
        token = await _get_access_token(client, auth_manager, settings)
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


async def play_playlist(client: httpx.AsyncClient, playlist_uri: str, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """
    Start playing a playlist.

    Args:
        client: Shared HTTP client from dependency injection.
        playlist_uri: Spotify URI of the playlist (spotify:playlist:xxx).
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)

    Raises:
        Exception if API call fails.
    """
    if settings is None:
        settings = get_settings()
    
    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": f"Bearer {token}"},
            json={"context_uri": playlist_uri},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise Exception(f"Play playlist error: {str(e)}") from e
