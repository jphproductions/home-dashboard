"""Unit tests for Spotify service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from home_dashboard.exceptions import (
    SpotifyAPIException,
    SpotifyAuthException,
    SpotifyException,
    SpotifyNotAuthenticatedException,
)
from home_dashboard.services import spotify_service


@pytest.mark.asyncio
async def test_get_access_token_from_cache(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test getting access token from cache."""
    mock_spotify_auth_manager.get_token.return_value = "cached-token-123"

    token = await spotify_service._get_access_token(mock_http_client, mock_spotify_auth_manager, mock_settings)

    assert token == "cached-token-123"
    mock_spotify_auth_manager.get_token.assert_called_once()
    # Should not make API call if cached
    mock_http_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_get_access_token_refresh_flow(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test access token refresh flow."""
    # No cached token
    mock_spotify_auth_manager.get_token.return_value = None

    # Mock successful token refresh
    mock_response = MagicMock()
    mock_response.json = lambda: {
        "access_token": "new-access-token",
        "expires_in": 3600,
        "refresh_token": "new-refresh-token",
    }
    mock_response.raise_for_status = lambda: None
    mock_http_client.post.return_value = mock_response

    token = await spotify_service._get_access_token(mock_http_client, mock_spotify_auth_manager, mock_settings)

    assert token == "new-access-token"
    mock_http_client.post.assert_called_once()
    # Verify token was cached
    mock_spotify_auth_manager.set_token.assert_called_once()
    call_args = mock_spotify_auth_manager.set_token.call_args[0]
    assert call_args[0] == "new-access-token"
    assert call_args[1] > 0  # expires_at timestamp


@pytest.mark.asyncio
async def test_get_access_token_no_refresh_token(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test access token fails when no refresh token available."""
    mock_spotify_auth_manager.get_token.return_value = None
    mock_settings.spotify_refresh_token = None

    with patch("home_dashboard.services.spotify_service._load_refresh_token", return_value=None):
        with pytest.raises(SpotifyNotAuthenticatedException) as exc_info:
            await spotify_service._get_access_token(mock_http_client, mock_spotify_auth_manager, mock_settings)

        assert "No refresh token available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_access_token_auth_error(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test access token refresh fails with auth error."""
    mock_spotify_auth_manager.get_token.return_value = None

    # Mock 401 Unauthorized
    error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=MagicMock(status_code=401))
    mock_http_client.post.side_effect = error

    with pytest.raises(SpotifyAuthException) as exc_info:
        await spotify_service._get_access_token(mock_http_client, mock_spotify_auth_manager, mock_settings)

    assert "Spotify token refresh failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_track_success(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test successful current track retrieval."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    # Mock playback state response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "is_playing": True,
        "item": {
            "name": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album", "images": [{"url": "https://example.com/image.jpg"}]},
            "duration_ms": 240000,
        },
        "progress_ms": 60000,
        "device": {"name": "Living Room TV", "type": "TV", "volume_percent": 50},
    }
    mock_response.raise_for_status = lambda: None
    mock_http_client.get.return_value = mock_response

    status = await spotify_service.get_current_track(mock_http_client, mock_spotify_auth_manager, mock_settings)

    assert status.is_playing is True
    assert status.track_name == "Test Song"
    assert status.artist_name == "Test Artist"
    assert status.device_name == "Living Room TV"


@pytest.mark.asyncio
async def test_get_current_track_no_playback(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test get current track when no playback active."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    # Mock 204 No Content
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.raise_for_status = lambda: None
    mock_http_client.get.return_value = mock_response

    status = await spotify_service.get_current_track(mock_http_client, mock_spotify_auth_manager, mock_settings)

    assert status.is_playing is False
    assert status.track_name is None


@pytest.mark.asyncio
async def test_get_current_track_api_error(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test get current track with API error."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    error = httpx.HTTPStatusError("Server Error", request=MagicMock(), response=MagicMock(status_code=500))
    mock_http_client.get.side_effect = error

    with pytest.raises(SpotifyAPIException) as exc_info:
        await spotify_service.get_current_track(mock_http_client, mock_spotify_auth_manager, mock_settings)

    assert "Failed to get playback state" in str(exc_info.value)


@pytest.mark.asyncio
async def test_play_success(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test successful play command."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_http_client.put.return_value = mock_response

    await spotify_service.play(mock_http_client, mock_spotify_auth_manager, mock_settings)

    mock_http_client.put.assert_called_once()
    call_args = mock_http_client.put.call_args
    assert "play" in call_args[0][0]


@pytest.mark.asyncio
async def test_pause_success(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test successful pause command."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_http_client.put.return_value = mock_response

    await spotify_service.pause(mock_http_client, mock_spotify_auth_manager, mock_settings)

    mock_http_client.put.assert_called_once()
    call_args = mock_http_client.put.call_args
    assert "pause" in call_args[0][0]


@pytest.mark.asyncio
async def test_next_track_success(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test successful next track command."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_http_client.post.return_value = mock_response

    await spotify_service.next_track(mock_http_client, mock_spotify_auth_manager, mock_settings)

    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    assert "next" in call_args[0][0]


@pytest.mark.asyncio
async def test_previous_track_success(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test successful previous track command."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_http_client.post.return_value = mock_response

    await spotify_service.previous_track(mock_http_client, mock_spotify_auth_manager, mock_settings)

    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    assert "previous" in call_args[0][0]


@pytest.mark.asyncio
async def test_play_playlist_success(mock_http_client, mock_spotify_auth_manager, mock_settings):
    """Test successful playlist playback."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_http_client.put.return_value = mock_response

    await spotify_service.play_playlist(
        mock_http_client, "spotify:playlist:test123", mock_spotify_auth_manager, mock_settings
    )

    mock_http_client.put.assert_called_once()
    call_args = mock_http_client.put.call_args
    assert "play" in call_args[0][0]


@pytest.mark.asyncio
async def test_wake_tv_and_play_success(
    mock_http_client, mock_spotify_auth_manager, mock_settings, mock_tv_state_manager
):
    """Test wake TV and play with Spotify."""
    mock_spotify_auth_manager.get_token.return_value = "test-token"

    # Mock TV wake
    with patch("home_dashboard.services.spotify_service.tv_tizen_service.wake") as mock_wake:
        mock_wake.return_value = "TV woken"

        # Mock Spotify play
        mock_response = MagicMock()
        mock_response.raise_for_status = lambda: None
        mock_http_client.put.return_value = mock_response

        # Mock asyncio.sleep
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await spotify_service.wake_tv_and_play(
                mock_http_client, mock_spotify_auth_manager, mock_tv_state_manager, mock_settings
            )

        assert "TV woken and playback transferred" in result
        mock_wake.assert_called_once_with(mock_settings, mock_tv_state_manager)


@pytest.mark.asyncio
async def test_wake_tv_and_play_tv_wake_fails(
    mock_http_client, mock_spotify_auth_manager, mock_settings, mock_tv_state_manager
):
    """Test wake TV and play when TV wake fails."""
    from home_dashboard.exceptions import TVConnectionException

    # Mock TV wake failure
    with patch("home_dashboard.services.spotify_service.tv_tizen_service.wake") as mock_wake:
        mock_wake.side_effect = TVConnectionException("TV connection failed")

        with pytest.raises(SpotifyException) as exc_info:
            await spotify_service.wake_tv_and_play(
                mock_http_client, mock_spotify_auth_manager, mock_tv_state_manager, mock_settings
            )

        assert "Failed to wake TV and play" in str(exc_info.value)


@pytest.mark.asyncio
async def test_is_authenticated_with_settings_token(mock_settings):
    """Test is_authenticated returns True when refresh token in settings."""
    mock_settings.spotify_refresh_token = "test-refresh-token"

    result = spotify_service.is_authenticated(mock_settings)

    assert result is True


@pytest.mark.asyncio
async def test_is_authenticated_no_token(mock_settings):
    """Test is_authenticated returns False when no token available."""
    mock_settings.spotify_refresh_token = None

    with patch("home_dashboard.services.spotify_service._load_refresh_token", return_value=None):
        result = spotify_service.is_authenticated(mock_settings)

        assert result is False
