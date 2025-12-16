"""Exception handlers for the application."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from home_dashboard.exceptions import DashboardException
from home_dashboard.logging_config import get_logger, log_with_context

logger = get_logger(__name__)


async def dashboard_exception_handler(request: Request, exc: DashboardException) -> JSONResponse:
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

    error_content: dict[str, Any] = {"code": exc.code.value, "message": exc.message, "details": exc.details}

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_content},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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


def register_error_handlers(app) -> None:
    """Register all exception handlers with the application.

    Args:
        app: FastAPI application instance
    """
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    app.add_exception_handler(DashboardException, dashboard_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
