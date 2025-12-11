"""Weather service for OpenWeatherMap API integration."""

import httpx
from home_dashboard.config import Settings, get_settings
from home_dashboard.models.weather import CurrentWeather, WeatherResponse
from home_dashboard.exceptions import WeatherException, WeatherAPIException


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


async def get_current_weather(client: httpx.AsyncClient, settings: Settings | None = None) -> WeatherResponse:
    """Get current weather from OpenWeatherMap API.

    Args:
        client: Shared HTTP client for making requests
        settings: Settings instance (defaults to singleton)

    Returns:
        WeatherResponse with formatted weather data

    Raises:
        httpx.HTTPError: If API request fails
    """
    if settings is None:
        settings = get_settings()
    params: dict[str, str | float] = {
        "lat": str(settings.weather_latitude),
        "lon": str(settings.weather_longitude),
        "appid": settings.weather_api_key,
        "exclude": "minutely,hourly,daily,alerts",
        "units": "metric",
        "lang": "en",
    }

    try:
        response = await client.get(OPENWEATHER_URL, params=params, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        data = response.json()

        # Validate and parse into Pydantic model
        current_weather = CurrentWeather.model_validate(data)

        # Convert to simplified response
        return WeatherResponse.from_openweather(current_weather)

    except httpx.HTTPStatusError as e:
        raise WeatherAPIException(
            f"Weather API request failed (HTTP {e.response.status_code}): {e.response.text}",
            status_code=e.response.status_code,
            details={"api_response": e.response.text},
        ) from e
    except httpx.HTTPError as e:
        raise WeatherException(
            f"Failed to fetch weather data: {str(e)}",
            details={"error_type": "network_error"},
        ) from e
    except Exception as e:
        raise WeatherException(
            f"Failed to process weather data: {str(e)}",
            details={"error_type": "data_processing"},
        ) from e
