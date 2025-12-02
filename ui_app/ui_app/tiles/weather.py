"""Weather tile for displaying current conditions."""

import streamlit as st
import httpx
from shared.models.weather import WeatherResponse


@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_weather_data(api_base_url: str) -> WeatherResponse:
    """Fetch weather data from API with caching.

    Args:
        api_base_url: Base URL of FastAPI backend.

    Returns:
        WeatherResponse model with weather data.

    Raises:
        Exception: If API call fails.
    """
    # Disable proxy for localhost connections to avoid corporate proxy redirects
    with httpx.Client(timeout=5.0, proxies={}) as client:
        response = client.get(f"{api_base_url}/api/weather/current")
        response.raise_for_status()
        data = response.json()
        return WeatherResponse.model_validate(data)


def get_wind_direction_compass(degrees: int) -> str:
    """Convert wind direction degrees to compass arrow.

    Args:
        degrees: Wind direction in degrees (0-360).

    Returns:
        Arrow symbol pointing where wind is blowing TO.
    """
    # Wind degree indicates where wind is coming FROM, so arrow points opposite direction
    # 0° = from North, blowing south (↓), 180° = from South, blowing north (↑)
    directions = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    idx = round(degrees / 45) % 8
    return directions[idx]


def get_weather_emoji(condition: str) -> str:
    """Get emoji for weather condition.

    Args:
        condition: Weather condition string from API.

    Returns:
        Emoji representing the weather condition.
    """
    condition_lower = condition.lower()

    if "clear" in condition_lower:
        return "☀️"
    elif "cloud" in condition_lower:
        return "☁️"
    elif "rain" in condition_lower or "drizzle" in condition_lower:
        return "🌧️"
    elif "thunder" in condition_lower or "storm" in condition_lower:
        return "⛈️"
    elif "snow" in condition_lower:
        return "❄️"
    elif "mist" in condition_lower or "fog" in condition_lower:
        return "🌫️"
    else:
        return "🌤️"


def get_beaufort_scale(wind_speed_ms: float) -> tuple[int, str]:
    """Convert wind speed in m/s to Beaufort scale.

    Args:
        wind_speed_ms: Wind speed in meters per second.

    Returns:
        Tuple of (Beaufort number, description).
    """
    if wind_speed_ms < 0.5:
        return (0, "Calm")
    elif wind_speed_ms < 1.6:
        return (1, "Light air")
    elif wind_speed_ms < 3.4:
        return (2, "Light breeze")
    elif wind_speed_ms < 5.5:
        return (3, "Gentle breeze")
    elif wind_speed_ms < 8.0:
        return (4, "Moderate breeze")
    elif wind_speed_ms < 10.8:
        return (5, "Fresh breeze")
    elif wind_speed_ms < 13.9:
        return (6, "Strong breeze")
    elif wind_speed_ms < 17.2:
        return (7, "Near gale")
    elif wind_speed_ms < 20.8:
        return (8, "Gale")
    elif wind_speed_ms < 24.5:
        return (9, "Strong gale")
    elif wind_speed_ms < 28.5:
        return (10, "Storm")
    elif wind_speed_ms < 32.7:
        return (11, "Violent storm")
    else:
        return (12, "Hurricane")


def render_tile(api_base_url: str):
    """Render weather tile with current conditions and recommendation.

    Args:
        api_base_url: Base URL of FastAPI backend.
    """
    try:
        weather = fetch_weather_data(api_base_url)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Temperature**")
            st.markdown(
                f"<h2 style='margin: 0; line-height: 1;'>{weather.temp:.1f}°C</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(f"Feels like {weather.feels_like:.1f}°C")

            # Check if wind data is available (for backwards compatibility with cached data)
            if hasattr(weather, "wind_deg") and hasattr(weather, "wind_speed"):
                beaufort, description = get_beaufort_scale(weather.wind_speed)
                direction = get_wind_direction_compass(weather.wind_deg)
                st.markdown("**Wind**")
                st.markdown(
                    f"<h2 style='margin: 0; line-height: 1;'>{beaufort} <span style='font-size: 2.5rem;'>{direction}</span></h2>",
                    unsafe_allow_html=True,
                )
                st.markdown(description)

        with col2:
            weather_emoji = get_weather_emoji(weather.condition)
            st.write(f"**Condition:** {weather_emoji} {weather.condition}")
            st.write(f"**Location:** {weather.location}")
            st.info(f"💡 {weather.recommendation}")

    except Exception as e:
        st.error(f"Failed to load weather: {str(e)}")
