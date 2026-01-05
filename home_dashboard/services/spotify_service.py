"""Spotify Web API service."""

from typing import TYPE_CHECKING

import httpx

from home_dashboard.cache import cached, get_cache
from home_dashboard.config import Settings, get_settings
from home_dashboard.exceptions import (
    SpotifyAPIException,
    SpotifyAuthException,
    SpotifyException,
    SpotifyNotAuthenticatedException,
)
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.models import SpotifyPlaybackState
from home_dashboard.protocols import TVServiceProtocol
from home_dashboard.state_managers import SpotifyAuthManager

if TYPE_CHECKING:
    from home_dashboard.state_managers import TVStateManager

logger = get_logger(__name__)

# Cache configuration
SPOTIFY_STATUS_CACHE_TTL = 5  # 5 seconds - status changes frequently


def is_authenticated(settings: Settings | None = None) -> bool:
    """Check if we have a refresh token available in settings.

    Args:
        settings: Settings instance (defaults to singleton)

    Returns:
        True if refresh token is configured in .env file
    """
    if settings is None:
        settings = get_settings()
    return bool(settings.spotify_refresh_token)


async def _get_access_token(
    client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None
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

    # Get refresh token from settings (.env file)
    refresh_token = settings.spotify_refresh_token
    if not refresh_token:
        log_with_context(
            logger,
            "error",
            "No Spotify refresh token available",
            event_type="spotify_auth_error",
        )
        raise SpotifyNotAuthenticatedException(
            "No refresh token available. Please authenticate first.",
            details={"auth_url": "/api/spotify/auth/login"},
        )

    log_with_context(
        logger,
        "debug",
        "Refreshing Spotify access token",
        event_type="spotify_token_refresh",
    )

    try:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify token refresh response",
            event_type="spotify_token_response",
            status_code=response.status_code,
            response_text=response.text if response.status_code != 200 else None,
        )

        response.raise_for_status()
        data = response.json()

        access_token: str = data["access_token"]
        expires_in = data.get("expires_in", 3600)

        # Store in manager
        await auth_manager.set_token(access_token, expires_in)

        log_with_context(
            logger,
            "info",
            "Spotify access token refreshed successfully",
            event_type="spotify_token_success",
            expires_in=expires_in,
        )

        # Note: Spotify may return a new refresh token (rare, on first auth or security events)
        # Access token: expires in ~1 hour, cached in memory by auth_manager
        # Refresh token: no expiry, stored in .env (SPOTIFY_REFRESH_TOKEN)
        # If a new refresh token is returned, user must manually update .env
        if "refresh_token" in data:
            log_with_context(
                logger,
                "warning",
                "Spotify returned new refresh token - update SPOTIFY_REFRESH_TOKEN in .env",
                event_type="spotify_new_refresh_token",
            )

        return access_token
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else None
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Spotify token refresh failed",
            event_type="spotify_token_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAuthException(
            f"Spotify token refresh failed: {str(e)}",
            details={"error_type": "token_refresh", "status_code": status_code},
        ) from e
    except (KeyError, ValueError) as e:
        log_with_context(
            logger,
            "error",
            "Invalid Spotify auth response",
            event_type="spotify_auth_parse_error",
            error=str(e),
        )
        raise SpotifyAuthException(
            f"Invalid Spotify auth response: {str(e)}",
            details={"error_type": "invalid_response"},
        ) from e


async def get_current_track(
    client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None
) -> SpotifyPlaybackState:
    """
    Get current playback state on Spotify with caching.

    Results are cached for 5 seconds to reduce API calls while maintaining responsiveness.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)

    Returns:
        SpotifyPlaybackState with current track and playback info (may be cached).

    Raises:
        SpotifyAPIException: If API call fails.
    """
    if settings is None:
        settings = get_settings()

    cache_key = "spotify:current_track"

    async def fetch_current_track() -> SpotifyPlaybackState:
        """Fetch fresh playback status from Spotify API."""
        log_with_context(
            logger,
            "debug",
            "Fetching Spotify playback status",
            event_type="spotify_status_fetch",
        )
        try:
            token = await _get_access_token(client, auth_manager, settings)
            response = await client.get(
                "https://api.spotify.com/v1/me/player",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )

            log_with_context(
                logger,
                "debug",
                "Spotify playback status response",
                event_type="spotify_status_response",
                status_code=response.status_code,
            )

            response.raise_for_status()
            data = response.json() if response.status_code != 204 else {}

            is_playing = data.get("is_playing", False)
            item = data.get("item") or {}
            device = data.get("device") or {}

            status = SpotifyPlaybackState(
                is_playing=is_playing,
                track_name=item.get("name"),
                artist_name=item.get("artists", [{}])[0].get("name") if item.get("artists") else None,
                device_name=device.get("name"),
                progress_ms=data.get("progress_ms"),
                duration_ms=item.get("duration_ms") if item else None,
            )

            log_with_context(
                logger,
                "info",
                "Spotify playback status retrieved",
                event_type="spotify_status_success",
                is_playing=is_playing,
                track=item.get("name"),
                artist=item.get("artists", [{}])[0].get("name") if item.get("artists") else None,
                device=device.get("name"),
            )

            return status
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 502
            response_text = e.response.text if hasattr(e, "response") else None
            log_with_context(
                logger,
                "error",
                "Failed to get Spotify playback state",
                event_type="spotify_status_error",
                status_code=status_code,
                error=str(e),
                response_body=response_text,
            )
            raise SpotifyAPIException(
                f"Failed to get playback state: {str(e)}",
                status_code=status_code,
                details={"operation": "get_current_track"},
            ) from e

    # Use cached wrapper
    return await cached(get_cache(), cache_key, SPOTIFY_STATUS_CACHE_TTL, fetch_current_track)


async def play(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """Resume playback on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()

    log_with_context(logger, "info", "Starting Spotify playback", event_type="spotify_play")

    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify play response",
            event_type="spotify_play_response",
            status_code=response.status_code,
        )

        response.raise_for_status()
        log_with_context(logger, "info", "Spotify playback started", event_type="spotify_play_success")

        # Invalidate cache to force fresh status on next request
        cache_key = "spotify:current_track"
        cache = get_cache()
        await cache.clear(cache_key)
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Failed to start Spotify playback",
            event_type="spotify_play_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAPIException(
            f"Failed to start playback: {str(e)}",
            status_code=status_code,
            details={"operation": "play"},
        ) from e


async def pause(client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None) -> None:
    """Pause playback on Spotify.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()

    log_with_context(logger, "info", "Pausing Spotify playback", event_type="spotify_pause")

    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/pause",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify pause response",
            event_type="spotify_pause_response",
            status_code=response.status_code,
        )

        response.raise_for_status()
        log_with_context(logger, "info", "Spotify playback paused", event_type="spotify_pause_success")

        # Invalidate cache to force fresh status on next request
        cache_key = "spotify:current_track"
        cache = get_cache()
        await cache.clear(cache_key)
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Failed to pause Spotify playback",
            event_type="spotify_pause_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAPIException(
            f"Failed to pause playback: {str(e)}",
            status_code=status_code,
            details={"operation": "pause"},
        ) from e


async def next_track(
    client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None
) -> None:
    """Skip to next track.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()

    log_with_context(logger, "info", "Skipping to next track", event_type="spotify_next")

    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.post(
            "https://api.spotify.com/v1/me/player/next",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify next track response",
            event_type="spotify_next_response",
            status_code=response.status_code,
        )

        response.raise_for_status()
        log_with_context(logger, "info", "Skipped to next track", event_type="spotify_next_success")

        # Invalidate cache to force fresh status on next request
        cache_key = "spotify:current_track"
        cache = get_cache()
        await cache.clear(cache_key)
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Failed to skip to next track",
            event_type="spotify_next_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAPIException(
            f"Failed to skip to next track: {str(e)}",
            status_code=status_code,
            details={"operation": "next_track"},
        ) from e


async def previous_track(
    client: httpx.AsyncClient, auth_manager: SpotifyAuthManager, settings: Settings | None = None
) -> None:
    """Go to previous track.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()

    log_with_context(logger, "info", "Going to previous track", event_type="spotify_previous")

    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.post(
            "https://api.spotify.com/v1/me/player/previous",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify previous track response",
            event_type="spotify_previous_response",
            status_code=response.status_code,
        )

        response.raise_for_status()
        log_with_context(logger, "info", "Went to previous track", event_type="spotify_previous_success")

        # Invalidate cache to force fresh status on next request
        cache_key = "spotify:current_track"
        cache = get_cache()
        await cache.clear(cache_key)
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Failed to go to previous track",
            event_type="spotify_previous_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAPIException(
            f"Failed to skip to previous track: {str(e)}",
            status_code=status_code,
            details={"operation": "previous_track"},
        ) from e


async def wake_tv_and_play(
    client: httpx.AsyncClient,
    auth_manager: SpotifyAuthManager,
    tv_service: TVServiceProtocol,
    tv_manager: "TVStateManager",
    settings: Settings | None = None,
) -> str:
    """
    Wake TV and transfer current playback to TV device.

    This combines:
    1. Wake TV via Tizen (KEY_POWER).
    2. Transfer Spotify playback to TV device.

    Args:
        client: Shared HTTP client from dependency injection.
        auth_manager: Spotify authentication state manager
        tv_service: TV service for waking the TV (injected)
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
        # Wake TV first using injected service
        await tv_service.wake(settings, tv_manager)

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
        raise SpotifyException(
            f"Failed to wake TV and play: {str(e)}",
            details={"operation": "wake_and_play"},
        ) from e


async def play_playlist(
    client: httpx.AsyncClient, playlist_uri: str, auth_manager: SpotifyAuthManager, settings: Settings | None = None
) -> None:
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
        status_code = e.response.status_code if hasattr(e, "response") else 502
        raise SpotifyAPIException(
            f"Failed to play playlist: {str(e)}",
            status_code=status_code,
            details={"operation": "play_playlist"},
        ) from e


async def transfer_playback_to_device(
    client: httpx.AsyncClient,
    device_id: str,
    auth_manager: SpotifyAuthManager,
    settings: Settings | None = None,
    play: bool = False,
) -> None:
    """
    Transfer Spotify playback to a specific device.

    Args:
        client: Shared HTTP client from dependency injection.
        device_id: Spotify device ID to transfer playback to.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)
        play: Whether to start playing after transfer (default: False, keeps current play state)

    Raises:
        SpotifyAPIException: If API call fails.
    """
    if settings is None:
        settings = get_settings()

    log_with_context(
        logger,
        "info",
        "Transferring playback to device",
        event_type="spotify_transfer_playback",
        device_id=device_id,
        auto_play=play,
    )

    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_ids": [device_id], "play": play},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify transfer playback response",
            event_type="spotify_transfer_response",
            status_code=response.status_code,
        )

        response.raise_for_status()

        log_with_context(
            logger,
            "info",
            "Playback transferred successfully",
            event_type="spotify_transfer_success",
            device_id=device_id,
        )

        # Invalidate cache to force fresh status on next request
        cache_key = "spotify:current_track"
        cache = get_cache()
        await cache.clear(cache_key)
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Failed to transfer playback",
            event_type="spotify_transfer_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAPIException(
            f"Failed to transfer playback: {str(e)}",
            status_code=status_code,
            details={"operation": "transfer_playback", "device_id": device_id},
        ) from e


async def play_playlist_on_device(
    client: httpx.AsyncClient,
    playlist_uri: str,
    device_id: str,
    auth_manager: SpotifyAuthManager,
    settings: Settings | None = None,
) -> None:
    """
    Start playing a specific playlist on a specific device.

    Args:
        client: Shared HTTP client from dependency injection.
        playlist_uri: Spotify URI of the playlist (spotify:playlist:xxx).
        device_id: Spotify device ID to play on.
        auth_manager: Spotify authentication state manager
        settings: Settings instance (defaults to singleton)

    Raises:
        SpotifyAPIException: If API call fails.
    """
    if settings is None:
        settings = get_settings()

    log_with_context(
        logger,
        "info",
        "Starting playlist on device",
        event_type="spotify_play_playlist_on_device",
        playlist_uri=playlist_uri,
        device_id=device_id,
    )

    try:
        token = await _get_access_token(client, auth_manager, settings)
        response = await client.put(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": f"Bearer {token}"},
            params={"device_id": device_id},
            json={"context_uri": playlist_uri},
            timeout=10.0,
        )

        log_with_context(
            logger,
            "debug",
            "Spotify play playlist response",
            event_type="spotify_play_playlist_response",
            status_code=response.status_code,
        )

        response.raise_for_status()

        log_with_context(
            logger,
            "info",
            "Playlist started successfully",
            event_type="spotify_play_playlist_success",
            playlist_uri=playlist_uri,
            device_id=device_id,
        )

        # Invalidate cache to force fresh status on next request
        cache_key = "spotify:current_track"
        cache = get_cache()
        await cache.clear(cache_key)
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        response_text = e.response.text if hasattr(e, "response") else None
        log_with_context(
            logger,
            "error",
            "Failed to play playlist on device",
            event_type="spotify_play_playlist_error",
            status_code=status_code,
            error=str(e),
            response_body=response_text,
        )
        raise SpotifyAPIException(
            f"Failed to play playlist on device: {str(e)}",
            status_code=status_code,
            details={
                "operation": "play_playlist_on_device",
                "playlist_uri": playlist_uri,
                "device_id": device_id,
            },
        ) from e


async def wake_tv_launch_spotify_and_play_playlist(
    client: httpx.AsyncClient,
    playlist_uri: str,
    auth_manager: SpotifyAuthManager,
    tv_service: TVServiceProtocol,
    tv_manager: "TVStateManager",
    settings: Settings | None = None,
) -> str:
    """
    Complete workflow: Wake TV, launch Spotify app, transfer playback, and play a playlist.

    This function orchestrates the full experience:
    1. Wake the TV if it's in standby
    2. Launch the Spotify app on the TV
    3. Transfer Spotify playback to the TV device
    4. Start playing the specified playlist

    Args:
        client: Shared HTTP client from dependency injection.
        playlist_uri: Spotify URI of the playlist (spotify:playlist:xxx).
        auth_manager: Spotify authentication state manager
        tv_service: TV service protocol implementation
        tv_manager: TV state manager for WebSocket token
        settings: Settings instance (defaults to singleton)

    Returns:
        Success message

    Raises:
        SpotifyAPIException: If Spotify API calls fail.
        Exception: If TV operations fail.
    """
    if settings is None:
        settings = get_settings()

    log_with_context(
        logger,
        "info",
        "Starting complete TV + Spotify workflow",
        event_type="spotify_complete_workflow",
        playlist_uri=playlist_uri,
    )

    try:
        # Step 1: Wake the TV
        log_with_context(logger, "info", "Step 1: Waking TV", event_type="spotify_workflow_wake_tv")
        await tv_service.wake(settings, tv_manager)
        await asyncio.sleep(2)  # Give TV time to wake up

        # Step 2: Launch Spotify app on TV
        log_with_context(logger, "info", "Step 2: Launching Spotify app", event_type="spotify_workflow_launch_app")
        await tv_service.launch_app(
            app_id="3201606009684",  # Spotify app ID
            settings=settings,
            tv_manager=tv_manager,
            app_type="DEEP_LINK",
        )
        await asyncio.sleep(3)  # Give app time to launch

        # Step 3: Transfer playback and play playlist
        log_with_context(
            logger,
            "info",
            "Step 3: Transferring playback and starting playlist",
            event_type="spotify_workflow_play",
        )
        await play_playlist_on_device(
            client=client,
            playlist_uri=playlist_uri,
            device_id=settings.tv_spotify_device_id,
            auth_manager=auth_manager,
            settings=settings,
        )

        log_with_context(
            logger,
            "info",
            "Complete workflow finished successfully",
            event_type="spotify_workflow_success",
            playlist_uri=playlist_uri,
        )

        return f"TV woken, Spotify launched, and playlist started: {playlist_uri}"

    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Complete workflow failed",
            event_type="spotify_workflow_error",
            error=str(e),
        )
        raise
