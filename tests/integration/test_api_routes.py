"""Integration tests for FastAPI routes."""

import pytest


def test_health_check(test_client):
    """Test /health endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_weather_route(test_client):
    """Test /api/weather/current route."""
    # TODO: Implement with mocked weather service
    pass


def test_spotify_status_route(test_client):
    """Test /api/spotify/status route."""
    # TODO: Implement with mocked Spotify service
    pass
