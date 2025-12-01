"""Unit tests for weather service with modern patterns."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from api_app.services import weather_service
from api_app.models import WeatherResponse


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def mock_weather_response():
    """Sample weather API response."""
    return {
        "main": {"temp": 15.5, "feels_like": 14.2},
        "weather": [{"main": "Clouds", "icon": "02d"}],
    }


@pytest.mark.asyncio
async def test_get_current_weather_success(mock_http_client, mock_weather_response):
    """Test successful weather fetch."""
    # Arrange
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_weather_response
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.get.return_value = mock_response

    # Act
    result = await weather_service.get_current_weather(mock_http_client)

    # Assert
    assert isinstance(result, WeatherResponse)
    assert result.temp == 15.5
    assert result.feels_like == 14.2
    assert result.condition == "Clouds"
    assert result.icon == "02d"
    assert result.location == "Den Bosch"
    assert result.recommendation  # Should have a recommendation

    # Verify HTTP client was called correctly
    mock_http_client.get.assert_called_once()
    call_args = mock_http_client.get.call_args
    assert "weather" in call_args[0][0]


@pytest.mark.asyncio
async def test_get_current_weather_http_error(mock_http_client):
    """Test weather fetch with HTTP error."""
    # Arrange
    mock_http_client.get.side_effect = httpx.HTTPError("API Error")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await weather_service.get_current_weather(mock_http_client)

    assert "Weather API error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_malformed_response(mock_http_client):
    """Test weather fetch with malformed response."""
    # Arrange
    mock_response = AsyncMock()
    mock_response.json.return_value = {"invalid": "data"}  # Missing required fields
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.get.return_value = mock_response

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await weather_service.get_current_weather(mock_http_client)

    assert "Invalid weather API response" in str(exc_info.value)


@pytest.mark.parametrize(
    "temp,condition,expected_keyword",
    [
        (-5, "Clear", "winter gear"),
        (3, "Clear", "coat"),
        (10, "Clear", "jacket"),
        (30, "Clear", "Sunscreen"),
        (15, "Rain", "umbrella"),
        (15, "Clouds", "cool"),
    ],
)
def test_get_recommendation(temp, condition, expected_keyword):
    """Test weather recommendation logic."""
    recommendation = weather_service._get_recommendation(temp, condition)
    assert expected_keyword.lower() in recommendation.lower()
