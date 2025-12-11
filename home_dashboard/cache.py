"""Simple in-memory cache for API responses."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any, TypeVar

from home_dashboard.logging_config import get_logger, log_with_context

logger = get_logger(__name__)

T = TypeVar("T")


class CacheEntry:
    """A cached value with expiration time."""

    def __init__(self, value: Any, expires_at: datetime):
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() >= self.expires_at


class SimpleCache:
    """Simple in-memory cache with TTL support.

    Thread-safe for async operations using asyncio.Lock.
    """

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                log_with_context(
                    logger,
                    "debug",
                    "Cache hit",
                    cache_key=key,
                    event_type="cache_hit",
                )
                return entry.value

            # Remove expired entry
            if entry:
                del self._cache[key]
                log_with_context(
                    logger,
                    "debug",
                    "Cache expired",
                    cache_key=key,
                    event_type="cache_expired",
                )

            return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set cached value with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        async with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self._cache[key] = CacheEntry(value, expires_at)
            log_with_context(
                logger,
                "debug",
                "Cache set",
                cache_key=key,
                ttl_seconds=ttl_seconds,
                event_type="cache_set",
            )

    async def clear(self, key: str | None = None) -> None:
        """Clear cache entry or entire cache.

        Args:
            key: Specific key to clear, or None to clear all
        """
        async with self._lock:
            if key:
                if key in self._cache:
                    del self._cache[key]
                    log_with_context(
                        logger,
                        "debug",
                        "Cache key cleared",
                        cache_key=key,
                        event_type="cache_clear",
                    )
            else:
                self._cache.clear()
                log_with_context(
                    logger,
                    "info",
                    "Cache cleared",
                    event_type="cache_clear_all",
                )

    async def cleanup_expired(self) -> None:
        """Remove all expired entries from cache."""
        async with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                log_with_context(
                    logger,
                    "debug",
                    "Cleaned up expired cache entries",
                    count=len(expired_keys),
                    event_type="cache_cleanup",
                )


async def cached(
    cache: SimpleCache,
    key: str,
    ttl_seconds: int,
    fetch_func: Callable[[], Awaitable[T] | Any],
) -> T:
    """Cached wrapper for async functions.

    Args:
        cache: Cache instance
        key: Cache key
        ttl_seconds: Time to live in seconds
        fetch_func: Async function to call if cache miss

    Returns:
        Cached or freshly fetched value
    """
    # Try cache first
    cached_value: T | None = await cache.get(key)
    if cached_value is not None:
        return cached_value

    # Cache miss - fetch new value
    log_with_context(
        logger,
        "debug",
        "Cache miss, fetching fresh data",
        cache_key=key,
        event_type="cache_miss",
    )
    value: T = await fetch_func()

    # Store in cache
    await cache.set(key, value, ttl_seconds)

    return value


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance."""
    return _cache
