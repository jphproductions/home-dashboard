"""Weather service for OpenWeatherMap API."""

import httpx
from api_app.config import settings
from api_app.models import WeatherResponse


async def get_current_weather() -> WeatherResponse:
    """
    Fetch current weather from OpenWeatherMap API.
    
    Returns:
        WeatherResponse with temperature, condition, icon, and recommendation.
    
    Raises:
        Exception if API call fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": settings.weather_latitude,
                    "lon": settings.weather_longitude,
                    "appid": settings.weather_api_key,
                    "units": "metric",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            condition = data["weather"][0]["main"]
            icon = data["weather"][0]["icon"]
            
            # Simple recommendation logic
            recommendation = _get_recommendation(temp, condition)
            
            return WeatherResponse(
                temp=temp,
                feels_like=feels_like,
                condition=condition,
                icon=icon,
                location=settings.weather_location,
                recommendation=recommendation,
            )
    except httpx.HTTPError as e:
        raise Exception(f"Weather API error: {str(e)}")


def _get_recommendation(temp: float, condition: str) -> str:
    """
    Simple rule-based weather recommendation.
    
    Args:
        temp: Temperature in Celsius.
        condition: Weather condition string.
    
    Returns:
        Recommendation string.
    """
    if temp < 0:
        return "❄️ Heavy winter gear"
    elif temp < 5:
        return "🧥 Warm coat + layers"
    elif temp < 15:
        return "🧢 Light jacket"
    elif temp > 25:
        return "☀️ Sunscreen + hat"
    
    if "rain" in condition.lower():
        return "☔ Bring umbrella"
    elif "cloud" in condition.lower():
        return "☁️ Might get cool"
    
    return "👍 Nice weather!"