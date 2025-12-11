"""Pytest configuration and shared fixtures."""

# Import app
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "home_dashboard")
from home_dashboard.config import Settings
from home_dashboard.main import app as fastapi_app


@pytest.fixture
def test_client():
    """FastAPI test client with lifespan context."""
    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture
def mock_http_client():
    """Mock httpx.AsyncClient for external API calls."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def mock_settings():
    """Mock Settings instance with test values."""
    return Settings(
        api_host="0.0.0.0",
        api_port=8000,
        tv_ip="192.168.1.100",
        tv_spotify_device_id="test-device-id",
        weather_api_key="test-weather-key",
        weather_location="Amsterdam",
        weather_latitude=52.3676,
        weather_longitude=4.9041,
        spotify_client_id="test-spotify-client-id",
        spotify_client_secret="test-spotify-client-secret",
        spotify_redirect_uri="http://localhost:8000/callback",
        spotify_refresh_token="test-refresh-token",
        ifttt_webhook_key="test-ifttt-key",
        ifttt_event_name="test-event",
    )


@pytest.fixture
def mock_spotify_auth_manager():
    """Mock SpotifyAuthManager for testing."""
    manager = AsyncMock()
    manager.initialize = AsyncMock()
    manager.cleanup = AsyncMock()
    manager.get_access_token = AsyncMock(return_value="mock-access-token")
    manager.is_authenticated = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_tv_state_manager():
    """Mock TVStateManager for testing."""
    manager = AsyncMock()
    manager.initialize = AsyncMock()
    manager.cleanup = AsyncMock()
    manager.increment_wake_failure = AsyncMock(return_value=1)
    manager.reset_wake_failures = AsyncMock()
    manager.get_wake_failure_count = AsyncMock(return_value=0)
    return manager


@pytest.fixture
def mock_weather_response():
    """Mock OpenWeatherMap API response."""
    return {
        "coord": {"lon": 4.9041, "lat": 52.3676},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
        "base": "stations",
        "main": {
            "temp": 15.5,
            "feels_like": 14.2,
            "temp_min": 14.0,
            "temp_max": 17.0,
            "pressure": 1013,
            "humidity": 65,
        },
        "visibility": 10000,
        "wind": {"speed": 3.5, "deg": 180},
        "clouds": {"all": 0},
        "dt": int(datetime.now(UTC).timestamp()),
        "sys": {
            "country": "NL",
            "sunrise": int(datetime.now(UTC).timestamp()) - 3600,
            "sunset": int(datetime.now(UTC).timestamp()) + 3600,
        },
        "timezone": 7200,
        "id": 2759794,
        "name": "Amsterdam",
        "cod": 200,
    }


@pytest.fixture
def mock_spotify_playback_response():
    """Mock Spotify playback state response."""
    return {
        "device": {"id": "test-device-id", "is_active": True, "name": "Samsung TV", "type": "TV", "volume_percent": 50},
        "is_playing": True,
        "item": {
            "name": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album", "images": [{"url": "https://example.com/image.jpg"}]},
            "duration_ms": 240000,
            "uri": "spotify:track:test123",
        },
        "progress_ms": 60000,
        "shuffle_state": False,
        "repeat_state": "off",
    }


@pytest.fixture
def mock_spotify_devices_response():
    """Mock Spotify devices list response."""
    return {
        "devices": [
            {"id": "test-device-id", "is_active": True, "name": "Samsung TV", "type": "TV", "volume_percent": 50}
        ]
    }


@pytest.fixture
def mock_websocket():
    """Mock websocket connection for TV control."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value='{"event":"ms.channel.connect"}')
    ws.close = AsyncMock()
    ws.__aenter__ = AsyncMock(return_value=ws)
    ws.__aexit__ = AsyncMock(return_value=None)
    return ws
