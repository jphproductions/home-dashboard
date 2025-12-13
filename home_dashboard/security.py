"""Security middleware and authentication for Home Dashboard."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from home_dashboard.config import Settings, get_settings
from home_dashboard.logging_config import get_logger, log_with_context

logger = get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> None:
    """Verify API key from Authorization header.

    Args:
        request: The FastAPI request object
        credentials: HTTP Bearer credentials from header
        settings: Settings instance with API key from .env

    Raises:
        HTTPException: If API key is missing or invalid

    Note:
        DASHBOARD_API_KEY is REQUIRED in all environments.
        Each developer should have their own API key.

    Example:
        Authorization: Bearer your-api-key-here
    """
    api_key = settings.dashboard_api_key

    # Debug logging
    log_with_context(
        logger,
        "debug",
        "API key check",
        configured={bool(api_key)},
        has_credentials={bool(credentials)},
        event_type="auth_check",
        path=str(request.url),
    )

    # API key is REQUIRED
    if not api_key:
        log_with_context(
            logger,
            "error",
            "DASHBOARD_API_KEY not configured",
            event_type="security_error",
            path=str(request.url),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication not configured - DASHBOARD_API_KEY environment variable is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if credentials provided
    if not credentials:
        log_with_context(
            logger,
            "warning",
            "Missing API key",
            event_type="auth_failure",
            path=str(request.url),
            ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify API key
    if credentials.credentials != api_key:
        log_with_context(
            logger,
            "warning",
            "Invalid API key",
            event_type="auth_failure",
            path=str(request.url),
            ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_with_context(
        logger,
        "debug",
        "API key verified",
        event_type="auth_success",
        path=str(request.url),
    )


def get_cors_origins(settings: Settings) -> list[str]:
    """Get allowed CORS origins from settings.

    Args:
        settings: Settings instance with CORS configuration

    Returns:
        List of allowed origin patterns
    """
    return [origin.strip() for origin in settings.cors_origins.split(",")]


def get_trusted_hosts(settings: Settings) -> list[str]:
    """Get trusted host patterns from settings.

    Args:
        settings: Settings instance with trusted hosts configuration

    Returns:
        List of trusted host patterns
    """
    return [host.strip() for host in settings.trusted_hosts.split(",")]
