"""Unit tests for Spotify service with modern patterns."""

import pytest
import httpx
from unittest.mock import AsyncMock

from api_app.services import spotify_service
from shared.models.spotify import SpotifyStatus


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def mock_spotify_token_response():
    """Sample Spotify token response."""
    return {"access_token": "test_token_123"}


@pytest.fixture
def mock_spotify_playing_response():
    """Sample Spotify currently playing response."""
    return {
        "is_playing": True,
        "item": {
            "name": "Test Song",
            "duration_ms": 240000,
            "artists": [{"name": "Test Artist"}],
        },
        "device": {"name": "Living Room TV"},
        "progress_ms": 120000,
    }


@pytest.mark.asyncio
async def test_get_current_track_success(
    mock_http_client, mock_spotify_token_response, mock_spotify_playing_response
):
    """Test successful Spotify track fetch."""
    # Arrange
    token_response = AsyncMock()
    token_response.json.return_value = mock_spotify_token_response
    token_response.raise_for_status = AsyncMock()

    track_response = AsyncMock()
    track_response.json.return_value = mock_spotify_playing_response
    track_response.raise_for_status = AsyncMock()

    # First call for token, second for track
    mock_http_client.post.return_value = token_response
    mock_http_client.get.return_value = track_response

    # Act
    result = await spotify_service.get_current_track(mock_http_client)

    # Assert
    assert isinstance(result, SpotifyStatus)
    assert result.is_playing is True
    assert result.track_name == "Test Song"
    assert result.artist_name == "Test Artist"
    assert result.device_name == "Living Room TV"
    assert result.duration_ms == 240000
    assert result.progress_ms == 120000


@pytest.mark.asyncio
async def test_get_current_track_nothing_playing(
    mock_http_client, mock_spotify_token_response
):
    """Test Spotify status when nothing is playing."""
    # Arrange
    token_response = AsyncMock()
    token_response.json.return_value = mock_spotify_token_response
    token_response.raise_for_status = AsyncMock()

    track_response = AsyncMock()
    track_response.json.return_value = {"is_playing": False}
    track_response.raise_for_status = AsyncMock()

    mock_http_client.post.return_value = token_response
    mock_http_client.get.return_value = track_response

    # Act
    result = await spotify_service.get_current_track(mock_http_client)

    # Assert
    assert result.is_playing is False
    assert result.track_name is None
    assert result.artist_name is None


@pytest.mark.asyncio
async def test_play_success(mock_http_client, mock_spotify_token_response):
    """Test successful play command."""
    # Arrange
    token_response = AsyncMock()
    token_response.json.return_value = mock_spotify_token_response
    token_response.raise_for_status = AsyncMock()

    play_response = AsyncMock()
    play_response.raise_for_status = AsyncMock()

    mock_http_client.post.return_value = token_response
    mock_http_client.put.return_value = play_response

    # Act
    await spotify_service.play(mock_http_client)

    # Assert - no exception means success
    mock_http_client.put.assert_called_once()


@pytest.mark.asyncio
async def test_pause_success(mock_http_client, mock_spotify_token_response):
    """Test successful pause command."""
    # Arrange
    token_response = AsyncMock()
    token_response.json.return_value = mock_spotify_token_response
    token_response.raise_for_status = AsyncMock()

    pause_response = AsyncMock()
    pause_response.raise_for_status = AsyncMock()

    mock_http_client.post.return_value = token_response
    mock_http_client.put.return_value = pause_response

    # Act
    await spotify_service.pause(mock_http_client)

    # Assert
    mock_http_client.put.assert_called_once()


@pytest.mark.asyncio
async def test_next_track_success(mock_http_client, mock_spotify_token_response):
    """Test successful next track command."""
    # Arrange
    token_response = AsyncMock()
    token_response.json.return_value = mock_spotify_token_response
    token_response.raise_for_status = AsyncMock()

    next_response = AsyncMock()
    next_response.raise_for_status = AsyncMock()

    # Token call uses post, next also uses post
    mock_http_client.post.side_effect = [token_response, next_response]

    # Act
    await spotify_service.next_track(mock_http_client)

    # Assert
    assert mock_http_client.post.call_count == 2


@pytest.mark.asyncio
async def test_spotify_http_error(mock_http_client):
    """Test Spotify service with HTTP error."""
    # Arrange
    mock_http_client.post.side_effect = httpx.HTTPError("Auth failed")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await spotify_service.play(mock_http_client)

    assert "Spotify" in str(exc_info.value)
