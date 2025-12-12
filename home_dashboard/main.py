"""Main FastAPI application."""

import os
import platform
import re
import sys
import time
import warnings
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from home_dashboard import __version__
from home_dashboard.cache import get_cache
from home_dashboard.config import get_settings
from home_dashboard.dependencies import get_http_client, get_spotify_auth_manager
from home_dashboard.exceptions import DashboardException
from home_dashboard.logging_config import get_logger, log_with_context, setup_logging
from home_dashboard.models import DebugInfo, DetailedHealthResponse, HealthResponse
from home_dashboard.routers import (
    phone_ifttt_router,
    spotify_router,
    tv_tizen_router,
    view_router,
    weather_router,
)
from home_dashboard.security import get_cors_origins, get_trusted_hosts, verify_api_key
from home_dashboard.services import spotify_service, weather_service
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager

# Load environment variables from .env file (must be before other imports that use env vars)
load_dotenv(Path(__file__).parent.parent / ".env")

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
    description="""
    🏠 **Home Dashboard** - Control your smart home devices

    ## 🔐 Authentication
    Most API endpoints require authentication via Bearer token.

    **To authenticate:**
    1. Click the **"Authorize"** button (🔓) at the top right
    2. Enter your API key in the format: `Bearer YOUR_API_KEY`
    3. All subsequent "Try it out" requests will include authentication automatically

    ## 🎵 Spotify Setup
    Before using Spotify endpoints, you must authenticate:
    1. Visit /api/spotify/auth/login in your browser
    2. Log in with your Spotify account and approve access
    3. You'll be redirected back and authentication is complete
    4. All Spotify endpoints will now work

    ## 📊 Health & Monitoring
    - `/health` - Basic health check (Docker/K8s)
    - `/health/live` - Liveness probe (is app running?)
    - `/health/ready` - Readiness probe (can serve traffic?)
    - `/debug` - System state and diagnostics (requires auth)

    ## ⚡ Rate Limits
    - Most endpoints: 60 requests/minute per IP
    - Phone ring: 5 requests/minute per IP (abuse prevention)
    - Spotify play/pause: 30 requests/minute per IP
    """,
    version=__version__,
    lifespan=lifespan,
    contact={
        "name": "Jelle Hilbrands",
        "url": "https://github.com/jphproductions/home-dashboard",
    },
    license_info={
        "name": "MIT",
    },
)

# Add security middleware
# CORS - restrict to local network
cors_origins = get_cors_origins()
log_with_context(
    logger,
    "info",
    "Configuring CORS middleware",
    event_type="security_config",
    origins=cors_origins,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts - prevent host header injection
trusted_hosts = get_trusted_hosts()
log_with_context(
    logger,
    "info",
    "Configuring TrustedHost middleware",
    event_type="security_config",
    hosts=trusted_hosts,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=trusted_hosts,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom OpenAPI schema with security definitions
def custom_openapi():
    """Generate custom OpenAPI schema with security scheme."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )

    # Add security scheme for Bearer token authentication
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Enter your API key (without 'Bearer' prefix)",
        }
    }

    # Apply security to endpoints that require authentication
    # Also remove tile endpoints from docs (they're HTML fragments, not useful in API docs)
    paths_to_remove = []
    for path, path_item in openapi_schema.get("paths", {}).items():
        # Remove tile endpoints from docs (HTML fragments for HTMX)
        if path.startswith("/tiles/"):
            paths_to_remove.append(path)
            continue

        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # All API endpoints require authentication (weather, spotify, tv, phone, debug)
                if path.startswith("/api/") or path == "/debug":
                    operation["security"] = [{"BearerAuth": []}]

    # Remove tile paths from schema
    for path in paths_to_remove:
        del openapi_schema["paths"][path]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Middleware to count requests
@app.middleware("http")
async def count_requests(request, call_next):
    """Count total requests for debug endpoint."""
    app.state.request_count += 1
    response = await call_next(request)
    return response


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
    """Basic health check endpoint.

    Returns simple status for Docker healthcheck and basic monitoring.
    For detailed health status, use `/health/ready`.
    """
    return HealthResponse(status="ok", version=__version__)


@app.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """Liveness probe - is the application running?

    This endpoint always returns 200 if the app process is alive.
    Use this for Kubernetes liveness probes or basic uptime monitoring.

    **Returns:**
    - 200: Application is running
    """
    return HealthResponse(status="alive", version=__version__)


@app.get("/health/ready", response_model=DetailedHealthResponse)
@limiter.limit("30/minute")
async def readiness_check(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager=Depends(get_spotify_auth_manager),
):
    """Readiness probe - can the application serve traffic?

    Performs actual checks of external dependencies:
    - HTTP client initialization
    - Weather API connectivity (cached 60s)
    - Spotify authentication status

    **Rate Limited:** 30 requests/minute to avoid quota exhaustion

    **Returns:**
    - 200: Application is ready to serve requests
    - 503: Application is not ready (dependency failure)
    """
    checks = {}
    all_healthy = True

    # Check 1: HTTP client
    checks["http_client"] = "ok" if client else "failed"
    if not client:
        all_healthy = False

    # Check 2: Spotify auth (check if refresh token exists)
    try:
        settings = get_settings()
        is_auth = spotify_service.is_authenticated(settings)
        checks["spotify_auth"] = "ok" if is_auth else "not_authenticated"
        if not is_auth:
            all_healthy = False
    except Exception as e:
        checks["spotify_auth"] = f"error: {str(e)[:50]}"
        all_healthy = False

    # Check 3: Weather API (with caching to avoid quota issues)
    # Cache the weather check for 60 seconds
    cache = get_cache()
    cache_key = "health:weather_check"
    cached_result = await cache.get(cache_key)

    if cached_result is not None:
        checks["weather_api"] = cached_result
        if cached_result != "ok":
            all_healthy = False
    else:
        try:
            settings = get_settings()
            # Quick check with 2s timeout
            await weather_service.get_current_weather(client, settings)
            checks["weather_api"] = "ok"
            await cache.set(cache_key, "ok", 60)
        except Exception as e:
            error_msg = f"failed: {str(e)[:50]}"
            checks["weather_api"] = error_msg
            await cache.set(cache_key, error_msg, 60)
            all_healthy = False

    status_code = 200 if all_healthy else 503
    status = "healthy" if all_healthy else "unhealthy"

    return JSONResponse(
        status_code=status_code,
        content=DetailedHealthResponse(
            status=status,
            version=__version__,
            timestamp=datetime.now(UTC),
            checks=checks,
        ).model_dump(mode="json"),
    )


@app.get(
    "/debug",
    response_model=DebugInfo,
    dependencies=[Depends(verify_api_key)],
    responses={
        200: {"description": "System diagnostics and state information"},
        401: {"description": "Unauthorized - missing or invalid API key"},
    },
)
async def debug_info(
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager=Depends(get_spotify_auth_manager),
):
    """Debug endpoint with system state and diagnostics.

    **🔒 Authentication Required:** This endpoint requires Bearer token authentication.

    Returns detailed information about:
    - System info (version, uptime, Python version)
    - Application state (HTTP client, Spotify auth, cache)
    - Configuration (sanitized, no secrets)
    - Request statistics

    Useful for troubleshooting and monitoring internal application state.
    """
    settings = get_settings()
    cache = get_cache()

    # Calculate uptime
    uptime_seconds = int(time.time() - app.state.startup_time)

    # System info
    system_info = {
        "version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system(),
        "uptime_seconds": uptime_seconds,
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }

    # State info
    state_info = {
        "http_client": "initialized" if client else "not_initialized",
    }

    # Spotify auth status
    try:
        token = await auth_manager.get_token()
        if token:
            # Token exists, check if it's about to expire
            state_info["spotify_auth"] = "authenticated"
        else:
            state_info["spotify_auth"] = "not_authenticated"
    except Exception:
        state_info["spotify_auth"] = "error"

    # TV state
    tv_manager = app.state.tv_state_manager
    state_info["tv_wake_failures"] = await tv_manager.get_wake_failure_count()

    # Cache stats
    cache_size = len(cache._cache)
    state_info["cache_size"] = str(cache_size)
    state_info["cache_keys"] = ", ".join(cache._cache.keys()) if cache_size < 20 else f"{cache_size} keys"

    # Config info (sanitized - no secrets)
    config_info = {
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "weather_location": settings.weather_location,
        "spotify_redirect_uri": settings.spotify_redirect_uri,
        "cors_origins": get_cors_origins(),
        "trusted_hosts": get_trusted_hosts(),
        "rate_limit_default": "100/minute",
    }

    # Request stats
    request_stats = {
        "total_requests": app.state.request_count,
    }

    return DebugInfo(
        system=system_info,
        state=state_info,
        config=config_info,
        requests=request_stats,
    )


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
