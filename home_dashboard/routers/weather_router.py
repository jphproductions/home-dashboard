"""Weather API routes with support for JSON and HTML responses."""

from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from home_dashboard.dependencies import get_http_client
from home_dashboard.services import weather_service
from home_dashboard.views.template_renderer import TemplateRenderer

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/current")
@limiter.limit("60/minute")
async def get_current_weather(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
):
    """Get current weather data.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with WeatherResponse model or HTML tile fragment
    """
    try:
        if format == "html":
            return await TemplateRenderer.render_weather_tile(request, client)

        # JSON response
        weather = await weather_service.get_current_weather(client)
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather error: {str(e)}") from e
