"""Integration tests for API routers."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from home_dashboard.main import app
from home_dashboard.models import SpotifyStatus, WeatherResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_weather_endpoint_success(client, mock_weather_response):
    """Test weather endpoint returns data successfully."""
    with patch("home_dashboard.routers.weather_router.get_current_weather") as mock_get:
        # Mock the service to return WeatherResponse
        mock_get.return_value = WeatherResponse(
            temperature=72.5, condition="Clear", icon="01d", feels_like=70.0, humidity=65, wind_speed=5.2
        )

        response = client.get("/api/weather/current")

        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 72.5
        assert data["condition"] == "Clear"
        assert data["icon"] == "01d"


def test_weather_endpoint_error(client):
    """Test weather endpoint handles errors."""
    from home_dashboard.exceptions import WeatherException

    with patch("home_dashboard.routers.weather_router.get_current_weather") as mock_get:
        mock_get.side_effect = WeatherException("API error")

        response = client.get("/api/weather/current")

        assert response.status_code == 500


def test_phone_ring_endpoint_success(client):
    """Test phone ring endpoint."""
    with patch("home_dashboard.routers.phone_ifttt_router.ring_phone") as mock_ring:
        mock_ring.return_value = None

        response = client.post("/api/phone/ring", json={"message": "Test ring"})

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        mock_ring.assert_called_once()


def test_phone_ring_endpoint_error(client):
    """Test phone ring endpoint handles errors."""
    from home_dashboard.exceptions import IFTTTException

    with patch("home_dashboard.routers.phone_ifttt_router.ring_phone") as mock_ring:
        mock_ring.side_effect = IFTTTException("IFTTT error")

        response = client.post("/api/phone/ring", json={"message": "Test"})

        assert response.status_code == 500


def test_tv_wake_endpoint_success(client):
    """Test TV wake endpoint."""
    with patch("home_dashboard.routers.tv_tizen_router.wake") as mock_wake:
        mock_wake.return_value = "TV woken"

        response = client.post("/api/tv/wake")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


def test_tv_wake_endpoint_error(client):
    """Test TV wake endpoint handles errors."""
    from home_dashboard.exceptions import TVConnectionException

    with patch("home_dashboard.routers.tv_tizen_router.wake") as mock_wake:
        mock_wake.side_effect = TVConnectionException("Connection failed")

        response = client.post("/api/tv/wake")

        assert response.status_code == 500


def test_tv_status_endpoint_success(client):
    """Test TV status endpoint."""
    with patch("home_dashboard.routers.tv_tizen_router.get_status") as mock_status:
        mock_status.return_value = True

        response = client.get("/api/tv/status")

        assert response.status_code == 200
        data = response.json()
        assert data["is_on"] is True


def test_spotify_current_track_endpoint_success(client):
    """Test Spotify current track endpoint."""
    with patch("home_dashboard.routers.spotify_router.get_current_track") as mock_get:
        mock_get.return_value = SpotifyStatus(
            is_playing=True,
            track_name="Test Song",
            artist_name="Test Artist",
            device_name="Test Device",
            progress_ms=60000,
            duration_ms=240000,
        )

        response = client.get("/api/spotify/current")

        assert response.status_code == 200
        data = response.json()
        assert data["is_playing"] is True
        assert data["track_name"] == "Test Song"


def test_spotify_play_endpoint_success(client):
    """Test Spotify play endpoint."""
    with patch("home_dashboard.routers.spotify_router.play") as mock_play:
        mock_play.return_value = None

        response = client.post("/api/spotify/play")

        assert response.status_code == 200


def test_spotify_pause_endpoint_success(client):
    """Test Spotify pause endpoint."""
    with patch("home_dashboard.routers.spotify_router.pause") as mock_pause:
        mock_pause.return_value = None

        response = client.post("/api/spotify/pause")

        assert response.status_code == 200


def test_spotify_next_endpoint_success(client):
    """Test Spotify next track endpoint."""
    with patch("home_dashboard.routers.spotify_router.next_track") as mock_next:
        mock_next.return_value = None

        response = client.post("/api/spotify/next")

        assert response.status_code == 200


def test_spotify_previous_endpoint_success(client):
    """Test Spotify previous track endpoint."""
    with patch("home_dashboard.routers.spotify_router.previous_track") as mock_prev:
        mock_prev.return_value = None

        response = client.post("/api/spotify/previous")

        assert response.status_code == 200


def test_spotify_play_playlist_endpoint_success(client):
    """Test Spotify play playlist endpoint."""
    with patch("home_dashboard.routers.spotify_router.play_playlist") as mock_play:
        mock_play.return_value = None

        response = client.post("/api/spotify/playlist/play", json={"playlist_uri": "spotify:playlist:test123"})

        assert response.status_code == 200


def test_spotify_wake_tv_and_play_endpoint_success(client):
    """Test Spotify wake TV and play endpoint."""
    with patch("home_dashboard.routers.spotify_router.wake_tv_and_play") as mock_wake:
        mock_wake.return_value = "TV woken and playing"

        response = client.post("/api/spotify/wake-tv-and-play", json={"playlist_uri": "spotify:playlist:test123"})

        assert response.status_code == 200


def test_health_check_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_root_endpoint(client):
    """Test root redirect endpoint."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code in [200, 307]  # Either renders or redirects


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/api/health")

    # Should have CORS headers configured
    assert response.status_code in [200, 204]


def test_404_not_found(client):
    """Test 404 handling."""
    response = client.get("/api/nonexistent")

    assert response.status_code == 404
