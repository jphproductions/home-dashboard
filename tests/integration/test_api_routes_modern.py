"""Integration tests for API routes with dependency injection."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from api_app.main import app


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
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "main": {"temp": 20.0, "feels_like": 19.0},
        "weather": [{"main": "Clear", "icon": "01d"}],
    }
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.get.return_value = mock_response

    # Mock the dependency
    with patch("api_app.dependencies.http_client", mock_http_client):
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
    token_response = AsyncMock()
    token_response.json.return_value = {"access_token": "test_token"}
    token_response.raise_for_status = AsyncMock()

    status_response = AsyncMock()
    status_response.json.return_value = {
        "is_playing": True,
        "item": {"name": "Test Track", "artists": [{"name": "Test Artist"}]},
    }
    status_response.raise_for_status = AsyncMock()

    mock_http_client.post.return_value = token_response
    mock_http_client.get.return_value = status_response

    # Mock the dependency
    with patch("api_app.dependencies.http_client", mock_http_client):
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

    with patch("api_app.dependencies.http_client", mock_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/weather/current")

            # Assert
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"].lower()
