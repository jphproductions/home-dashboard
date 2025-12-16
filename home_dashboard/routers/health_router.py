"""Health and debug endpoints."""

import os
import platform
import sys
import time
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from home_dashboard import __version__
from home_dashboard.cache import get_cache
from home_dashboard.config import get_settings
from home_dashboard.dependencies import get_http_client, get_spotify_auth_manager
from home_dashboard.models import DebugInfo, DetailedHealthResponse, HealthResponse
from home_dashboard.security import get_cors_origins, get_trusted_hosts, verify_api_key
from home_dashboard.services import spotify_service, weather_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint.

    Returns simple status for Docker healthcheck and basic monitoring.
    For detailed health status, use `/health/ready`.
    """
    return HealthResponse(status="ok", version=__version__)


@router.get("/health/ready", response_model=DetailedHealthResponse)
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
    # Apply rate limit from app state
    limiter = request.app.state.limiter
    await limiter.check_request_limit(request, "30/minute")

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


@router.get(
    "/debug",
    response_model=DebugInfo,
    dependencies=[Depends(verify_api_key)],
    responses={
        200: {"description": "System diagnostics and state information"},
        401: {"description": "Unauthorized - missing or invalid API key"},
    },
)
async def debug_info(
    request: Request,
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
    uptime_seconds = int(time.time() - request.app.state.startup_time)

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
    tv_manager = request.app.state.tv_state_manager
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
        "cors_origins": get_cors_origins(settings),
        "trusted_hosts": get_trusted_hosts(settings),
        "rate_limit_default": "60/minute",
    }

    # Request stats
    request_stats = {
        "total_requests": request.app.state.request_count,
    }

    return DebugInfo(
        system=system_info,
        state=state_info,
        config=config_info,
        requests=request_stats,
    )
