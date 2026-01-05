"""State managers for handling application-wide mutable state.

This module provides thread-safe state management using asyncio.Lock
for async operations. All state managers inherit from StateManager ABC.
"""

import asyncio
import time
from abc import ABC, abstractmethod


class StateManager(ABC):
    """Base class for all state managers.

    State managers provide thread-safe access to mutable application state.
    All subclasses must implement lifecycle methods.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the state manager (called during app startup)."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources (called during app shutdown)."""
        pass


class SpotifyAuthManager(StateManager):
    """Manages Spotify authentication tokens with caching and auto-refresh.

    Provides thread-safe access to Spotify access tokens with automatic
    expiration tracking and refresh when needed.
    """

    def __init__(self):
        """Initialize the Spotify auth manager."""
        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._refresh_token: str | None = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the Spotify auth manager."""
        # No initialization needed for now, lifecycle method required by ABC
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Clear tokens on shutdown
        async with self._lock:
            self._access_token = None
            self._token_expires_at = 0
            self._refresh_token = None

    async def get_token(self) -> str | None:
        """Get the current access token if available and not expired.

        Returns:
            Access token string or None if expired/not set
        """
        async with self._lock:
            if self._access_token and self._token_expires_at > time.time():
                return self._access_token
            return None

    async def set_token(self, token: str, expires_in: int) -> None:
        """Set a new access token with expiration.

        Args:
            token: The access token string
            expires_in: Expiration time in seconds
        """
        async with self._lock:
            self._access_token = token
            self._token_expires_at = time.time() + expires_in

    async def set_refresh_token(self, refresh_token: str) -> None:
        """Set the refresh token.

        Args:
            refresh_token: The refresh token string
        """
        async with self._lock:
            self._refresh_token = refresh_token

    async def get_refresh_token(self) -> str | None:
        """Get the current refresh token if available.

        Returns:
            Refresh token string or None if not set
        """
        async with self._lock:
            return self._refresh_token


class TVStateManager(StateManager):
    """Manages TV state including authorization tokens.

    Provides thread-safe storage of TV authorization tokens to avoid
    repeated authorization prompts.
    """

    def __init__(self):
        """Initialize the TV state manager."""
        self._tv_token: str | None = None  # TV authorization token
        self._tv_client_id: str | None = None  # TV client ID
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the TV state manager."""
        # No initialization needed for now, lifecycle method required by ABC
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Clear tokens on shutdown
        async with self._lock:
            self._tv_token = None
            self._tv_client_id = None

    async def get_tv_token(self) -> str | None:
        """Get the stored TV authorization token.

        Returns:
            TV token or None if not stored
        """
        async with self._lock:
            return self._tv_token

    async def set_tv_auth(self, token: str | None, client_id: str | None) -> None:
        """Store TV authorization token and client ID.

        Args:
            token: TV authorization token
            client_id: TV client ID
        """
        async with self._lock:
            self._tv_token = token
            self._tv_client_id = client_id
