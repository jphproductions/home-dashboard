"""Unit tests for weather service."""

from unittest.mock import AsyncMock

import httpx
import pytest

from home_dashboard.exceptions import WeatherAPIException, WeatherException
from home_dashboard.models.weather import WeatherResponse
from home_dashboard.services import weather_service


@pytest.mark.asyncio
async def test_get_current_weather_success(mock_http_client, mock_settings, mock_weather_response):
    """Test successful weather data fetch."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: mock_weather_response  # Regular method, not async
    mock_response.raise_for_status = lambda: None  # Regular method, not async
    mock_http_client.get.return_value = mock_response

    # Call service
    result = await weather_service.get_current_weather(mock_http_client, mock_settings)

    # Assertions
    assert isinstance(result, WeatherResponse)
    assert result.location == "Amsterdam"
    assert result.temp == 15.5
    assert result.condition == "Clear"
    assert result.icon == "01d"
    assert result.feels_like == 14.2
    assert result.wind_speed == 3.5

    # Verify API call
    mock_http_client.get.assert_called_once()
    call_args = mock_http_client.get.call_args
    assert "lat" in call_args.kwargs["params"]
    assert "lon" in call_args.kwargs["params"]
    assert "appid" in call_args.kwargs["params"]


@pytest.mark.asyncio
async def test_get_current_weather_api_error(mock_http_client, mock_settings):
    """Test weather API returns error status."""
    # Setup mock error response
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid API key"

    # Create a proper HTTPStatusError
    mock_request = AsyncMock()
    error = httpx.HTTPStatusError("401 Unauthorized", request=mock_request, response=mock_response)

    # Make raise_for_status raise the error
    mock_response.raise_for_status = lambda: (_ for _ in ()).throw(error)
    mock_http_client.get.return_value = mock_response

    # Call service and expect exception
    with pytest.raises(WeatherAPIException) as exc_info:
        await weather_service.get_current_weather(mock_http_client, mock_settings)

    assert exc_info.value.status_code == 401
    assert "401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_network_error(mock_http_client, mock_settings):
    """Test network error during weather fetch."""
    # Setup mock network error
    mock_http_client.get.side_effect = httpx.NetworkError("Connection failed")

    # Call service and expect exception
    with pytest.raises(WeatherException) as exc_info:
        await weather_service.get_current_weather(mock_http_client, mock_settings)

    assert "network_error" in str(exc_info.value.details)


@pytest.mark.asyncio
async def test_get_current_weather_timeout(mock_http_client, mock_settings):
    """Test timeout during weather fetch."""
    # Setup mock timeout
    mock_http_client.get.side_effect = httpx.TimeoutException("Request timed out")

    # Call service and expect exception
    with pytest.raises(WeatherException) as exc_info:
        await weather_service.get_current_weather(mock_http_client, mock_settings)

    assert "Failed to fetch weather data" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_invalid_json(mock_http_client, mock_settings):
    """Test invalid JSON response from weather API."""
    # Setup mock invalid response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {"invalid": "data"}
    mock_response.raise_for_status = lambda: None
    mock_http_client.get.return_value = mock_response

    # Call service and expect exception
    with pytest.raises(WeatherException) as exc_info:
        await weather_service.get_current_weather(mock_http_client, mock_settings)

    assert "Failed to process weather data" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_uses_settings_values(mock_http_client, mock_settings, mock_weather_response):
    """Test that weather service uses correct settings values."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: mock_weather_response
    mock_response.raise_for_status = lambda: None
    mock_http_client.get.return_value = mock_response

    await weather_service.get_current_weather(mock_http_client, mock_settings)

    # Verify correct parameters were used
    call_args = mock_http_client.get.call_args
    params = call_args.kwargs["params"]
    assert float(params["lat"]) == mock_settings.weather_latitude
    assert float(params["lon"]) == mock_settings.weather_longitude
    assert params["appid"] == mock_settings.weather_api_key
    assert params["units"] == "metric"
