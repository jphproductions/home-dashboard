"""Main FastAPI application."""

import os
import re
import warnings
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from home_dashboard import __version__
from home_dashboard.exceptions import DashboardException
from home_dashboard.logging_config import get_logger, log_with_context, setup_logging
from home_dashboard.models import HealthResponse
from home_dashboard.routers import (
    phone_ifttt_router,
    spotify_router,
    tv_tizen_router,
    view_router,
    weather_router,
)
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager

# Configure structured logging (JSON to file + console)
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)
logger = get_logger(__name__)

# Suppress SSL warnings when using verify=False with corporate proxy
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Sensitive parameters to redact from URLs
SENSITIVE_PARAMS = ["appid", "api_key", "token", "password", "secret", "key", "refresh_token", "access_token"]

# Initialize rate limiter (100 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def redact_sensitive_data(url: str) -> str:
    """Redact sensitive query parameters from URL."""
    redacted = url
    for param in SENSITIVE_PARAMS:
        pattern = rf"{param}=([^&\s\"]+)"
        redacted = re.sub(pattern, f"{param}=***REDACTED***", redacted)
    return redacted


async def log_request(request: httpx.Request) -> None:
    """Event hook to log requests with redacted sensitive data."""
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

    # Configure httpx with granular timeouts (per httpx 0.27.2 best practices)
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
            proxies=proxy,
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
        # ✅ CRITICAL: Must re-raise per FastAPI 0.122.0+ to prevent memory leaks!
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


app = FastAPI(
    title="Home Dashboard API",
    description="Control TV, Spotify, weather, and phone",
    version=__version__,
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
# View routes (HTML pages and tile fragments) - no prefix
app.include_router(view_router.router, tags=["views"])

# API routes - support both JSON and HTML responses via ?format=json|html
app.include_router(spotify_router.router, prefix="/api/spotify", tags=["spotify"])
app.include_router(weather_router.router, prefix="/api/weather", tags=["weather"])
app.include_router(phone_ifttt_router.router, prefix="/api/phone", tags=["phone"])
app.include_router(tv_tizen_router.router, prefix="/api/tv", tags=["tv"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Home Dashboard API", "docs": "/docs"}


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors."""
    return Response(content=b"", media_type="image/x-icon")


@app.exception_handler(DashboardException)
async def dashboard_exception_handler(request, exc: DashboardException):
    """Handle custom dashboard exceptions with proper HTTP status codes.

    Returns structured JSON error responses with status code, error code,
    message, and optional details for client-side error handling.
    """
    log_with_context(
        logger,
        "warning",
        "Dashboard error",
        error_code=exc.code.value,
        error_message=exc.message,
        status_code=exc.status_code,
        method=request.method,
        url=str(request.url),
        event_type="dashboard_error",
    )

    error_content: dict[str, Any] = {
        "code": exc.code.value,
        "message": exc.message,
    }

    # Include details only if present (avoid empty objects)
    if exc.details:
        error_content["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_content},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with logging."""
    log_with_context(
        logger,
        "error",
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        method=request.method,
        url=str(request.url),
        event_type="unhandled_error",
    )
    # Also log the traceback separately for debugging
    logger.error("Exception traceback:", exc_info=True)

    # Don't expose internal error details to clients
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )
