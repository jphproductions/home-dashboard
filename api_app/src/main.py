"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api_app import __version__
from api_app.routers import weather, spotify, tv_tizen, phone_ifttt
from api_app.models import HealthResponse

app = FastAPI(
    title="Home Dashboard API",
    description="Control TV, Spotify, weather, and phone",
    version=__version__,
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