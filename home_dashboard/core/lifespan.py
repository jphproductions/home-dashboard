"""Application lifespan management."""

import os
import time
import warnings
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI

from home_dashboard import __version__
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager

logger = get_logger(__name__)

# Suppress SSL warnings when using verify=False with corporate proxy
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


async def log_request(request: httpx.Request) -> None:
    """Event hook to log requests with redacted sensitive data."""
    from home_dashboard.middleware.logging_middleware import redact_sensitive_data

    redacted_url = redact_sensitive_data(str(request.url))
    log_with_context(
        logger,
        "info",
        "HTTP Request",
        method=request.method,
        url=redacted_url,
        event_type="http_request",
    )


async def log_response(response: httpx.Response) -> None:
    """Event hook to log responses with redacted sensitive data."""
    from home_dashboard.middleware.logging_middleware import redact_sensitive_data

    await response.aread()  # Ensure response is read
    redacted_url = redact_sensitive_data(str(response.request.url))
    log_with_context(
        logger,
        "info",
        "HTTP Response",
        status_code=response.status_code,
        url=redacted_url,
        event_type="http_response",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan - startup and shutdown events.

    Per FastAPI 0.122.0+ breaking changes: Exceptions after yield MUST be
    re-raised to prevent memory leaks and ensure proper cleanup.
    """
    # Startup: Create HTTP client with connection pooling
    app.state.startup_time = time.time()
    app.state.request_count = 0

    log_with_context(
        logger,
        "info",
        "Starting Home Dashboard application",
        version=__version__,
        event_type="app_startup",
    )

    # Check for proxy settings
    proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")

    # Event hooks for logging with sensitive data redaction
    event_hooks: dict[str, list[Callable[..., Any]]] = {
        "request": [log_request],
        "response": [log_response],
    }

    # Configure httpx with granular timeouts
    if proxy:
        log_with_context(
            logger,
            "warning",
            "Using proxy with SSL verification disabled",
            proxy=proxy,
            event_type="proxy_config",
        )
        client = httpx.AsyncClient(  # nosec B113
            timeout=httpx.Timeout(
                connect=5.0,  # Connection establishment timeout
                read=30.0,  # Longer read timeout for proxy
                write=5.0,  # Write operation timeout
                pool=5.0,  # Pool checkout timeout
            ),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0,  # How long to keep idle connections
            ),
            follow_redirects=True,
            proxy=proxy,  # httpx 0.28+ uses 'proxy' (singular) instead of 'proxies'
            verify=False,  # Disable SSL verification for corporate proxy  # nosec B501
            event_hooks=event_hooks,
        )
    else:
        log_with_context(
            logger,
            "info",
            "Creating HTTP client with SSL verification enabled",
            event_type="http_client_config",
        )
        client = httpx.AsyncClient(  # nosec B113
            timeout=httpx.Timeout(
                connect=5.0,  # Connection establishment timeout
                read=10.0,  # Read response timeout
                write=5.0,  # Write operation timeout
                pool=5.0,  # Pool checkout timeout
            ),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0,  # How long to keep idle connections
            ),
            follow_redirects=True,
            event_hooks=event_hooks,
        )

    # Store in app state instead of global variable
    app.state.http_client = client
    log_with_context(
        logger,
        "info",
        "HTTP client initialized successfully",
        event_type="http_client_ready",
    )

    # Initialize state managers
    app.state.spotify_auth_manager = SpotifyAuthManager()
    app.state.tv_state_manager = TVStateManager()
    await app.state.spotify_auth_manager.initialize()
    await app.state.tv_state_manager.initialize()
    log_with_context(
        logger,
        "info",
        "State managers initialized",
        event_type="state_managers_ready",
    )

    try:
        yield
    except Exception as e:
        # Log the error for observability
        log_with_context(
            logger,
            "error",
            "Application error during lifespan",
            error=str(e),
            error_type=type(e).__name__,
            event_type="app_error",
        )
        raise
    finally:
        # Cleanup always runs, even if exception was raised
        log_with_context(
            logger,
            "info",
            "Shutting down Home Dashboard application",
            event_type="app_shutdown",
        )

        # Cleanup state managers
        await app.state.spotify_auth_manager.cleanup()
        await app.state.tv_state_manager.cleanup()
        log_with_context(
            logger,
            "info",
            "State managers cleaned up",
            event_type="state_managers_cleanup",
        )

        await client.aclose()
        log_with_context(
            logger,
            "info",
            "HTTP client closed",
            event_type="http_client_cleanup",
        )
