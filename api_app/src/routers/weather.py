"""Weather API routes."""

from fastapi import APIRouter, HTTPException
from api_app.services import weather_service
from api_app.models import WeatherResponse

router = APIRouter()


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather():
    """Get current weather."""
    try:
        weather = await weather_service.get_current_weather()
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather service error: {str(e)}")
