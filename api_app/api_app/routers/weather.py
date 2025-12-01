"""Weather API routes."""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from api_app.services import weather_service
from api_app.models import WeatherResponse
from api_app.dependencies import get_http_client

router = APIRouter()


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(client: httpx.AsyncClient = Depends(get_http_client)):
    """Get current weather."""
    try:
        weather = await weather_service.get_current_weather(client)
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather service error: {str(e)}") from e
