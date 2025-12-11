"""Unit tests for router endpoints with mocked dependencies."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from home_dashboard.main import app
from home_dashboard.models.spotify import SpotifyStatus
from home_dashboard.models.weather import WeatherResponse
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager


# Fixtures for mocked dependencies
@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    return AsyncMock(spec=AsyncClient)


@pytest.fixture
def mock_spotify_auth_manager():
    """Mock Spotify auth manager."""
    manager = MagicMock(spec=SpotifyAuthManager)
    manager.get_access_token = AsyncMock(return_value="mock_token_123")
    return manager


@pytest.fixture
def mock_tv_state_manager():
    """Mock TV state manager."""
    return MagicMock(spec=TVStateManager)


# Weather Router Tests
class TestWeatherRouter:
    """Tests for weather router endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_weather_json(self, mock_http_client):
        """Test getting current weather in JSON format."""
        from home_dashboard.routers import weather_router
        from home_dashboard.services import weather_service

        # Mock weather service response
        mock_weather = WeatherResponse(
            temperature=22.5, feels_like=20.0, description="Partly cloudy", icon="02d", location="Amsterdam"
        )
        weather_service.get_current_weather = AsyncMock(return_value=mock_weather)

        # Override dependency
        app.dependency_overrides[weather_router.get_http_client] = lambda: mock_http_client

        client = TestClient(app)
        response = client.get("/weather/current?format=json")

        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 22.5
        assert data["description"] == "Partly cloudy"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_current_weather_error(self, mock_http_client):
        """Test weather endpoint handles errors."""
        from home_dashboard.routers import weather_router
        from home_dashboard.services import weather_service

        # Mock weather service to raise error
        weather_service.get_current_weather = AsyncMock(side_effect=Exception("API error"))

        app.dependency_overrides[weather_router.get_http_client] = lambda: mock_http_client

        client = TestClient(app)
        response = client.get("/weather/current?format=json")

        assert response.status_code == 500
        assert "Weather error" in response.json()["detail"]

        app.dependency_overrides.clear()


# Spotify Router Tests
class TestSpotifyRouter:
    """Tests for Spotify router endpoints."""

    @pytest.mark.asyncio
    async def test_get_spotify_status_json(self, mock_http_client, mock_spotify_auth_manager):
        """Test getting Spotify status in JSON format."""
        from home_dashboard.routers import spotify_router
        from home_dashboard.services import spotify_service

        # Mock Spotify service response
        mock_status = SpotifyStatus(
            is_playing=True,
            track_name="Test Song",
            artist_name="Test Artist",
            album_name="Test Album",
            progress_ms=60000,
            duration_ms=180000,
            album_art_url="https://example.com/art.jpg",
        )
        spotify_service.get_current_track = AsyncMock(return_value=mock_status)

        # Override dependencies
        app.dependency_overrides[spotify_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[spotify_router.get_spotify_auth_manager] = lambda: mock_spotify_auth_manager

        client = TestClient(app)
        response = client.get("/spotify/status?format=json")

        assert response.status_code == 200
        data = response.json()
        assert data["is_playing"] is True
        assert data["track_name"] == "Test Song"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_spotify_play(self, mock_http_client, mock_spotify_auth_manager):
        """Test Spotify play endpoint."""
        from home_dashboard.routers import spotify_router
        from home_dashboard.services import spotify_service

        # Mock Spotify service
        spotify_service.play = AsyncMock()
        spotify_service.get_current_track = AsyncMock(
            return_value=SpotifyStatus(is_playing=True, track_name="Test Song", artist_name="Test Artist")
        )

        app.dependency_overrides[spotify_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[spotify_router.get_spotify_auth_manager] = lambda: mock_spotify_auth_manager

        client = TestClient(app)
        response = client.post("/spotify/play?format=json")

        assert response.status_code == 200
        spotify_service.play.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_spotify_pause(self, mock_http_client, mock_spotify_auth_manager):
        """Test Spotify pause endpoint."""
        from home_dashboard.routers import spotify_router
        from home_dashboard.services import spotify_service

        # Mock Spotify service
        spotify_service.pause = AsyncMock()
        spotify_service.get_current_track = AsyncMock(
            return_value=SpotifyStatus(is_playing=False, track_name="Test Song", artist_name="Test Artist")
        )

        app.dependency_overrides[spotify_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[spotify_router.get_spotify_auth_manager] = lambda: mock_spotify_auth_manager

        client = TestClient(app)
        response = client.post("/spotify/pause?format=json")

        assert response.status_code == 200
        spotify_service.pause.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_spotify_error(self, mock_http_client, mock_spotify_auth_manager):
        """Test Spotify endpoint handles errors."""
        from home_dashboard.routers import spotify_router
        from home_dashboard.services import spotify_service

        # Mock Spotify service to raise error
        spotify_service.get_current_track = AsyncMock(side_effect=Exception("Token error"))

        app.dependency_overrides[spotify_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[spotify_router.get_spotify_auth_manager] = lambda: mock_spotify_auth_manager

        client = TestClient(app)
        response = client.get("/spotify/status?format=json")

        assert response.status_code == 500
        assert "Spotify error" in response.json()["detail"]

        app.dependency_overrides.clear()


# Phone Router Tests
class TestPhoneRouter:
    """Tests for phone/IFTTT router endpoints."""

    @pytest.mark.asyncio
    async def test_ring_phone_success(self, mock_http_client):
        """Test ringing phone successfully."""
        from home_dashboard.routers import phone_ifttt_router
        from home_dashboard.services import phone_ifttt_service

        # Mock phone service
        phone_ifttt_service.ring_phone = AsyncMock()

        app.dependency_overrides[phone_ifttt_router.get_http_client] = lambda: mock_http_client

        client = TestClient(app)
        response = client.post("/phone/ring?format=json")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "webhook_triggered"
        assert data["action"] == "ring_phone"
        phone_ifttt_service.ring_phone.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_ring_phone_error(self, mock_http_client):
        """Test phone endpoint handles errors."""
        from home_dashboard.routers import phone_ifttt_router
        from home_dashboard.services import phone_ifttt_service

        # Mock phone service to raise error
        phone_ifttt_service.ring_phone = AsyncMock(side_effect=Exception("Connection error"))

        app.dependency_overrides[phone_ifttt_router.get_http_client] = lambda: mock_http_client

        client = TestClient(app)
        response = client.post("/phone/ring?format=json")

        assert response.status_code == 500
        assert "IFTTT error" in response.json()["detail"]

        app.dependency_overrides.clear()


# TV Router Tests
class TestTVRouter:
    """Tests for TV/Tizen router endpoints."""

    @pytest.mark.asyncio
    async def test_wake_tv_success(self, mock_http_client, mock_tv_state_manager):
        """Test waking TV successfully."""
        from home_dashboard.routers import tv_tizen_router
        from home_dashboard.services import tv_tizen_service

        # Mock TV service
        tv_tizen_service.wake_tv = AsyncMock()

        app.dependency_overrides[tv_tizen_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[tv_tizen_router.get_tv_state_manager] = lambda: mock_tv_state_manager

        client = TestClient(app)
        response = client.post("/tv/wake")

        assert response.status_code == 200
        assert response.json()["status"] == "TV wake signal sent"
        tv_tizen_service.wake_tv.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_turn_off_tv(self, mock_http_client, mock_tv_state_manager):
        """Test turning off TV."""
        from home_dashboard.routers import tv_tizen_router
        from home_dashboard.services import tv_tizen_service

        # Mock TV service
        tv_tizen_service.turn_off = AsyncMock()

        app.dependency_overrides[tv_tizen_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[tv_tizen_router.get_tv_state_manager] = lambda: mock_tv_state_manager

        client = TestClient(app)
        response = client.post("/tv/off")

        assert response.status_code == 200
        assert "TV off signal sent" in response.json()["status"]
        tv_tizen_service.turn_off.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_tv_error(self, mock_http_client, mock_tv_state_manager):
        """Test TV endpoint handles errors."""
        from home_dashboard.routers import tv_tizen_router
        from home_dashboard.services import tv_tizen_service

        # Mock TV service to raise error
        tv_tizen_service.wake_tv = AsyncMock(side_effect=Exception("Network error"))

        app.dependency_overrides[tv_tizen_router.get_http_client] = lambda: mock_http_client
        app.dependency_overrides[tv_tizen_router.get_tv_state_manager] = lambda: mock_tv_state_manager

        client = TestClient(app)
        response = client.post("/tv/wake")

        assert response.status_code == 500
        assert "TV error" in response.json()["detail"]

        app.dependency_overrides.clear()


# Root endpoint test
class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Home Dashboard API"
        assert "version" in data
        assert "status" in data
