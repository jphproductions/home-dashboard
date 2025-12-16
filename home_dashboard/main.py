"""Main FastAPI application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.responses import Response

from home_dashboard.core.app_factory import create_app
from home_dashboard.logging_config import setup_logging

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Configure structured logging (JSON to file + console)
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)

# Create application
app = create_app()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Home Dashboard API", "docs": "/docs"}


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors."""
    return Response(content=b"", media_type="image/x-icon")


if __name__ == "__main__":
    import uvicorn

    from home_dashboard.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "home_dashboard.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
