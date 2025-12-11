"""Unit tests for state managers."""

import asyncio

import pytest

from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager

# SpotifyAuthManager Tests


@pytest.mark.asyncio
async def test_spotify_auth_manager_initialize():
    """Test Spotify auth manager initialization."""
    manager = SpotifyAuthManager()
    await manager.initialize()

    # Should have no token initially
    token = await manager.get_token()
    assert token is None


@pytest.mark.asyncio
async def test_spotify_auth_manager_set_and_get_token():
    """Test setting and getting access token."""
    manager = SpotifyAuthManager()
    await manager.initialize()

    await manager.set_token("test-access-token", expires_in=3600)

    token = await manager.get_token()
    assert token == "test-access-token"


@pytest.mark.asyncio
async def test_spotify_auth_manager_token_expiration():
    """Test token expiration logic."""
    manager = SpotifyAuthManager()
    await manager.initialize()

    # Set token with very short expiration
    await manager.set_token("expiring-token", expires_in=0)

    # Token should be expired immediately
    await asyncio.sleep(0.1)
    token = await manager.get_token()
    assert token is None


@pytest.mark.asyncio
async def test_spotify_auth_manager_token_not_expired():
    """Test token is returned when not expired."""
    manager = SpotifyAuthManager()
    await manager.initialize()

    # Set token with long expiration
    await manager.set_token("valid-token", expires_in=3600)

    token = await manager.get_token()
    assert token == "valid-token"


@pytest.mark.asyncio
async def test_spotify_auth_manager_cleanup():
    """Test cleanup clears token."""
    manager = SpotifyAuthManager()
    await manager.initialize()

    await manager.set_token("test-token", expires_in=3600)
    assert await manager.get_token() == "test-token"

    await manager.cleanup()

    # Token should be cleared after cleanup
    token = await manager.get_token()
    assert token is None


@pytest.mark.asyncio
async def test_spotify_auth_manager_concurrent_access():
    """Test thread-safe concurrent access to token."""
    manager = SpotifyAuthManager()
    await manager.initialize()

    await manager.set_token("concurrent-token", expires_in=3600)

    # Simulate concurrent reads
    tasks = [manager.get_token() for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # All should get the same token
    assert all(token == "concurrent-token" for token in results)


# TVStateManager Tests


@pytest.mark.asyncio
async def test_tv_state_manager_initialize():
    """Test TV state manager initialization."""
    manager = TVStateManager()
    await manager.initialize()

    # Should have zero failures initially
    count = await manager.get_wake_failure_count()
    assert count == 0


@pytest.mark.asyncio
async def test_tv_state_manager_increment_failure():
    """Test incrementing wake failure count."""
    manager = TVStateManager()
    await manager.initialize()

    count = await manager.increment_wake_failure()
    assert count == 1

    count = await manager.increment_wake_failure()
    assert count == 2


@pytest.mark.asyncio
async def test_tv_state_manager_reset_failures():
    """Test resetting wake failure count."""
    manager = TVStateManager()
    await manager.initialize()

    # Increment a few times
    await manager.increment_wake_failure()
    await manager.increment_wake_failure()
    await manager.increment_wake_failure()

    assert await manager.get_wake_failure_count() == 3

    # Reset
    await manager.reset_wake_failures()

    assert await manager.get_wake_failure_count() == 0


@pytest.mark.asyncio
async def test_tv_state_manager_cleanup():
    """Test cleanup resets failure count."""
    manager = TVStateManager()
    await manager.initialize()

    await manager.increment_wake_failure()
    await manager.increment_wake_failure()
    assert await manager.get_wake_failure_count() == 2

    await manager.cleanup()

    # Counter should be reset after cleanup
    count = await manager.get_wake_failure_count()
    assert count == 0


@pytest.mark.asyncio
async def test_tv_state_manager_concurrent_increment():
    """Test thread-safe concurrent incrementing."""
    manager = TVStateManager()
    await manager.initialize()

    # Simulate 20 concurrent increments
    tasks = [manager.increment_wake_failure() for _ in range(20)]
    await asyncio.gather(*tasks)

    # Should have exactly 20 failures
    count = await manager.get_wake_failure_count()
    assert count == 20


@pytest.mark.asyncio
async def test_tv_state_manager_get_failure_count():
    """Test getting current failure count."""
    manager = TVStateManager()
    await manager.initialize()

    # Initial count
    assert await manager.get_wake_failure_count() == 0

    # After incrementing
    await manager.increment_wake_failure()
    assert await manager.get_wake_failure_count() == 1

    await manager.increment_wake_failure()
    assert await manager.get_wake_failure_count() == 2
