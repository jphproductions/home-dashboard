"""Main FastAPI application."""

from contextlib import asynccontextmanager
import httpx
import warnings
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Suppress SSL warnings when using verify=False with corporate proxy
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from api_app import __version__
from api_app.routers import weather, spotify, tv_tizen, phone_ifttt
from shared.models import HealthResponse

# Global HTTP client for connection pooling
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup: Create HTTP client with connection pooling
    import os

    global http_client

    # Use proxy for external APIs, but disable SSL verification to bypass corporate interception
    # Check for proxy settings
    proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")

    if proxy:
        print(f"HTTP client initialized with proxy: {proxy} (SSL verify disabled for corporate proxy)")
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),  # Longer timeout for proxy
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True,
            proxies=proxy,
            verify=False,  # Disable SSL verification for corporate proxy
        )
    else:
        print("HTTP client initialized without proxy")
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True,
        )
    yield
    # Shutdown: Clean up resources
    if http_client:
        await http_client.aclose()
        print("HTTP client closed")


app = FastAPI(
    title="Home Dashboard API",
    description="Control TV, Spotify, weather, and phone",
    version=__version__,
    lifespan=lifespan,
)

# Include routers
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(spotify.router, prefix="/api/spotify", tags=["spotify"])
app.include_router(tv_tizen.router, prefix="/api/tv", tags=["tv"])
app.include_router(phone_ifttt.router, prefix="/api/phone", tags=["phone"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Home Dashboard API", "docs": "/docs"}


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_code": "INTERNAL_ERROR"},
    )
