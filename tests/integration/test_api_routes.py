"""Integration tests for API routes with dependency injection."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from home_dashboard.main import app


@pytest.fixture
def mock_http_client():
    """Mock the global HTTP client."""
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_weather_endpoint_with_mock_client(mock_http_client):
    """Test weather endpoint with mocked HTTP client."""
    # Arrange
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.json = Mock(
        return_value={
            "coord": {"lon": 5.3048, "lat": 51.6978},
            "weather": [
                {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
            ],
            "base": "stations",
            "main": {
                "temp": 20.0,
                "feels_like": 19.0,
                "pressure": 1013,
                "humidity": 60,
                "sea_level": 1013,
                "grnd_level": 1011,
            },
            "visibility": 10000,
            "wind": {"speed": 3.5, "deg": 180, "gust": 5.0},
            "clouds": {"all": 0},
            "dt": 1701432000,
            "sys": {
                "type": 2,
                "id": 2012552,
                "country": "NL",
                "sunrise": 1701414000,
                "sunset": 1701444000,
            },
            "timezone": 3600,
            "id": 2747891,
            "name": "Den Bosch",
            "cod": 200,
        }
    )
    mock_response.raise_for_status = Mock()
    mock_http_client.get.return_value = mock_response

    # Mock the dependency
    with patch("home_dashboard.main.http_client", mock_http_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/weather/current")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["temp"] == 20.0
            assert data["condition"] == "Clear"
            assert data["location"] == "Den Bosch"


@pytest.mark.asyncio
async def test_spotify_status_endpoint_with_mock(mock_http_client):
    """Test Spotify status endpoint with mocked client."""
    # Arrange
    from unittest.mock import Mock

    token_response = Mock()
    token_response.json = Mock(return_value={"access_token": "test_token"})
    token_response.raise_for_status = Mock()

    status_response = Mock()
    status_response.json = Mock(
        return_value={
            "is_playing": True,
            "item": {"name": "Test Track", "artists": [{"name": "Test Artist"}]},
        }
    )
    status_response.raise_for_status = Mock()

    mock_http_client.post.return_value = token_response
    mock_http_client.get.return_value = status_response

    # Mock the dependency
    with patch("home_dashboard.main.http_client", mock_http_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/spotify/status")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_playing"] is True
            assert data["track_name"] == "Test Track"


@pytest.mark.asyncio
async def test_error_handling_propagation():
    """Test that exceptions are properly propagated as HTTP errors."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Simulated error")

    with patch("home_dashboard.main.http_client", mock_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/weather/current")

            # Assert
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"].lower()
