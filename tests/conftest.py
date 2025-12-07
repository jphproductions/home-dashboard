"""Pytest configuration and shared fixtures."""

import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import app
import sys

sys.path.insert(0, "home_dashboard")
from home_dashboard.main import app as fastapi_app


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(fastapi_app)


@pytest.fixture
def mock_httpx():
    """Mock httpx for external API calls."""
    with patch("httpx.AsyncClient") as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    return {
        "TV_IP": "192.168.178.79",
        "TV_SPOTIFY_DEVICE_ID": "test-device-id",
        "WEATHER_API_KEY": "test-key",
        "SPOTIFY_CLIENT_ID": "test-id",
        "SPOTIFY_CLIENT_SECRET": "test-secret",
        "IFTTT_WEBHOOK_KEY": "test-webhook",
    }
