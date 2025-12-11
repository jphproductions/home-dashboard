"""Tests for dependency injection functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from home_dashboard.dependencies import get_http_client, get_spotify_auth_manager, get_tv_state_manager
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager


class TestDependencies:
    """Tests for dependency injection functions."""

    @pytest.mark.asyncio
    async def test_get_http_client(self):
        """Test getting HTTP client from app state."""
        # Create a mock request with app state
        mock_request = MagicMock()
        mock_client = AsyncMock(spec=AsyncClient)
        mock_request.app.state.http_client = mock_client

        # Get the client
        client = await get_http_client(mock_request)

        assert client == mock_client

    @pytest.mark.asyncio
    async def test_get_spotify_auth_manager(self):
        """Test getting Spotify auth manager from app state."""
        # Create a mock request with app state
        mock_request = MagicMock()
        mock_manager = MagicMock(spec=SpotifyAuthManager)
        mock_request.app.state.spotify_auth_manager = mock_manager

        # Get the manager
        manager = await get_spotify_auth_manager(mock_request)

        assert manager == mock_manager

    @pytest.mark.asyncio
    async def test_get_tv_state_manager(self):
        """Test getting TV state manager from app state."""
        # Create a mock request with app state
        mock_request = MagicMock()
        mock_manager = MagicMock(spec=TVStateManager)
        mock_request.app.state.tv_state_manager = mock_manager

        # Get the manager
        manager = await get_tv_state_manager(mock_request)

        assert manager == mock_manager
