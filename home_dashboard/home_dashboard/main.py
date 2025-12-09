"""Main FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
import httpx
import warnings
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from typing import Any, Callable

from home_dashboard import __version__
from home_dashboard.routers import (
    phone_ifttt_router,
    spotify_router,
    tv_tizen_router,
    view_router,
    weather_router,
)
from home_dashboard.models import HealthResponse
from home_dashboard.exceptions import DashboardException
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Disable httpx's default logging since we handle it via event hooks
logging.getLogger("httpx").setLevel(logging.WARNING)

# Suppress SSL warnings when using verify=False with corporate proxy
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Sensitive parameters to redact from URLs
SENSITIVE_PARAMS = ["appid", "api_key", "token", "password", "secret", "key", "refresh_token", "access_token"]


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
    logger.info(f"HTTP Request: {request.method} {redacted_url}")


async def log_response(response: httpx.Response) -> None:
    """Event hook to log responses with redacted sensitive data."""
    await response.aread()  # Ensure response is read
    redacted_url = redact_sensitive_data(str(response.request.url))
    logger.info(f"HTTP Response: {response.status_code} from {redacted_url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup: Create HTTP client with connection pooling
    logger.info("Starting Home Dashboard application")
    logger.info(f"Version: {__version__}")

    # Check for proxy settings
    proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")

    # Event hooks for logging with sensitive data redaction
    event_hooks: dict[str, list[Callable[..., Any]]] = {
        "request": [log_request],
        "response": [log_response],
    }

    if proxy:
        logger.warning(f"Using proxy: {proxy} (SSL verification disabled for corporate proxy)")
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),  # Longer timeout for proxy
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True,
            proxies=proxy,
            verify=False,  # Disable SSL verification for corporate proxy
            event_hooks=event_hooks,
        )
    else:
        logger.info("Creating HTTP client with SSL verification enabled")
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True,
            event_hooks=event_hooks,
        )

    # Store in app state instead of global variable
    app.state.http_client = client
    logger.info("HTTP client initialized successfully")

    yield

    # Shutdown: Clean up resources
    logger.info("Shutting down Home Dashboard application")
    await app.state.http_client.aclose()
    logger.info("HTTP client closed")


app = FastAPI(
    title="Home Dashboard API",
    description="Control TV, Spotify, weather, and phone",
    version=__version__,
    lifespan=lifespan,
)

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
    """Handle custom dashboard exceptions."""
    logger.warning(f"Dashboard error: {exc.code} - {exc.message} on {request.method} {request.url}")

    return JSONResponse(status_code=400, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with logging."""
    logger.error(
        f"Unhandled exception on {request.method} {request.url}",
        exc_info=True,  # This logs the full traceback
    )

    # Don't expose internal error details to clients
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )
