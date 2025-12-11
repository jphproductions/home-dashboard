"""State managers for handling application-wide mutable state.

This module provides thread-safe state management using asyncio.Lock
for async operations. All state managers inherit from StateManager ABC.
"""

import asyncio
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
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the Spotify auth manager."""
        # No initialization needed for now
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Clear token on shutdown
        async with self._lock:
            self._access_token = None
            self._token_expires_at = 0

    async def get_token(self) -> str | None:
        """Get the current access token if available and not expired.

        Returns:
            Access token string or None if expired/not set
        """
        async with self._lock:
            import time

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
            import time

            self._access_token = token
            self._token_expires_at = time.time() + expires_in


class TVStateManager(StateManager):
    """Manages TV state including wake failure tracking.

    Provides thread-safe tracking of TV wake failures for monitoring
    and debugging purposes.
    """

    def __init__(self):
        """Initialize the TV state manager."""
        self._wake_failure_count: int = 0
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the TV state manager."""
        # No initialization needed for now
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Reset counter on shutdown
        async with self._lock:
            self._wake_failure_count = 0

    async def get_wake_failure_count(self) -> int:
        """Get the current wake failure count.

        Returns:
            Number of wake failures
        """
        async with self._lock:
            return self._wake_failure_count

    async def increment_wake_failure(self) -> int:
        """Increment wake failure count.

        Returns:
            Updated failure count
        """
        async with self._lock:
            self._wake_failure_count += 1
            return self._wake_failure_count

    async def reset_wake_failures(self) -> None:
        """Reset wake failure count to zero."""
        async with self._lock:
            self._wake_failure_count = 0
