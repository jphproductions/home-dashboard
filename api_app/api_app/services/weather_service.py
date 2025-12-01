import httpx
from api_app.config import settings
from shared.models.weather import CurrentWeather


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


async def get_current_weather() -> CurrentWeather:
    params = {
        "lat": settings.weather_latitude,
        "lon": settings.weather_longitude,
        "appid": settings.weather_api_key,
        "exclude": "minutely,hourly,daily,alerts",
        "units": "metric",
        "lang": "en",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(OPENWEATHER_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    # Validate and parse into Pydantic model (auto-validates)
    current_weather = CurrentWeather.model_validate(data)
    return current_weather
