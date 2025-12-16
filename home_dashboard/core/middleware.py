"""Middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from home_dashboard.config import Settings
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.security import get_trusted_hosts

logger = get_logger(__name__)


def setup_middleware(app: FastAPI, settings: Settings) -> Limiter:
    """Configure all middleware for the application.

    Args:
        app: FastAPI application instance
        settings: Application settings

    Returns:
        Limiter instance for rate limiting
    """
    # CORS configuration using regex pattern (wildcards don't work in allow_origins)
    log_with_context(
        logger,
        "info",
        "Configuring CORS middleware with regex pattern",
        event_type="security_config",
        pattern="http://(localhost|127\\.0\\.0\\.1|192\\.168\\.178\\.\\d+):8000",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.178\.\d+):8000",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted hosts - prevent host header injection
    trusted_hosts = get_trusted_hosts(settings)
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

    # Initialize rate limiter (60 requests per minute per IP)
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter

    # Middleware to count requests
    @app.middleware("http")
    async def count_requests(request, call_next):
        """Count total requests for debug endpoint."""
        app.state.request_count += 1
        response = await call_next(request)
        return response

    return limiter
