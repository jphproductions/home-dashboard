"""Unit tests for weather service."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_current_weather():
    """Test weather service fetches current weather."""
    # TODO: Implement test with mocked httpx
    pass


def test_weather_recommendation_logic():
    """Test weather recommendation generation."""
    from home_dashboard.models.weather import (
        WeatherResponse,
        CurrentWeather,
        WeatherInfo,
        MainInfo,
        WindInfo,
        CloudsInfo,
    )

    # Create a sample CurrentWeather object
    current_weather = CurrentWeather(
        coord={"lat": 51.685, "lon": 5.296},
        weather=[
            WeatherInfo(id=800, main="Clear", description="clear sky", icon="01d")
        ],
        base="stations",
        main=MainInfo(temp=10.0, feels_like=8.0, pressure=1013, humidity=70),
        visibility=10000,
        wind=WindInfo(speed=3.5, deg=180),
        clouds=CloudsInfo(all=0),
        dt=1701432000,
        sys={"country": "NL", "sunrise": 1701414000, "sunset": 1701444000},
        timezone=3600,
        id=2747891,
        name="Den Bosch",
        cod=200,
    )

    response = WeatherResponse.from_openweather(current_weather)
    assert "jacket" in response.recommendation.lower()
