"""Weather API routes."""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from home_dashboard.dependencies import get_http_client
from home_dashboard.services import weather_service
from home_dashboard.models.weather import WeatherResponse

router = APIRouter()


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(client: httpx.AsyncClient = Depends(get_http_client)):
    """Get current weather conditions.

    Returns:
        WeatherResponse with temperature, condition, and recommendation
    """
    try:
        weather = await weather_service.get_current_weather(client)
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather service error: {str(e)}") from e
