"""Weather API routes with support for JSON and HTML responses."""

from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from home_dashboard.config import Settings, get_settings
from home_dashboard.dependencies import get_http_client
from home_dashboard.security import verify_api_key
from home_dashboard.services import weather_service
from home_dashboard.views.template_renderer import TemplateRenderer

router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/current",
    summary="Get current weather",
    description="""
    Retrieves current weather conditions from OpenWeatherMap API.

    Includes temperature, conditions, wind speed, and clothing recommendations.
    Results are cached for 5 minutes to reduce API calls.

    **Rate Limited:** 60 requests/minute
    """,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "location": "s-Hertogenbosch",
                        "temp": 12.5,
                        "condition": "Cloudy",
                        "wind_speed": 5.2,
                        "wind_deg": 180,
                        "humidity": 75,
                        "clothing_recommendation": "Wear a jacket",
                    }
                }
            },
        },
        500: {"description": "Weather API error or configuration issue"},
    },
)
@limiter.limit("60/minute")
async def get_current_weather(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
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
            return await TemplateRenderer.render_weather_tile(request, client, settings)

        # JSON response
        weather = await weather_service.get_current_weather(client, settings)
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather error: {str(e)}") from e
