"""Application factory for creating and configuring the FastAPI app."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from home_dashboard import __version__
from home_dashboard.config import get_settings
from home_dashboard.core.lifespan import lifespan
from home_dashboard.core.middleware import setup_middleware
from home_dashboard.middleware.error_handlers import register_error_handlers
from home_dashboard.routers import (
    health_router,
    phone_ifttt_router,
    spotify_router,
    tv_tizen_router,
    view_router,
    weather_router,
)


def custom_openapi(app: FastAPI):
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
            "description": "Enter your API key",
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
                # All API endpoints require authentication
                if path.startswith("/api/") or path == "/debug":
                    operation["security"] = [{"BearerAuth": []}]

    # Remove tile paths from schema
    for path in paths_to_remove:
        del openapi_schema["paths"][path]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    # Load settings
    settings = get_settings()

    # Create FastAPI app
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

    # Configure middleware
    setup_middleware(app, settings)

    # Register exception handlers
    register_error_handlers(app)

    # Mount static files
    STATIC_DIR = Path(__file__).parent.parent / "static"
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Include routers
    # View routes (HTML pages and tile fragments) - no prefix
    app.include_router(view_router.router, tags=["views"])

    # Health and debug endpoints
    app.include_router(health_router.router, tags=["health"])

    # API routes
    app.include_router(spotify_router.router, prefix="/api/spotify", tags=["spotify"])
    app.include_router(weather_router.router, prefix="/api/weather", tags=["weather"])
    app.include_router(phone_ifttt_router.router, prefix="/api/phone", tags=["phone"])
    app.include_router(tv_tizen_router.router, prefix="/api/tv", tags=["tv"])

    # Custom OpenAPI schema
    app.openapi = lambda: custom_openapi(app)

    return app
