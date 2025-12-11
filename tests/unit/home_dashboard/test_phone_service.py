"""Unit tests for IFTTT phone service."""

from unittest.mock import AsyncMock

import httpx
import pytest

from home_dashboard.exceptions import IFTTTException
from home_dashboard.services import phone_ifttt_service


@pytest.mark.asyncio
async def test_ring_phone_success(mock_http_client, mock_settings):
    """Test successful phone ring request."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.post.return_value = mock_response

    # Call service
    result = await phone_ifttt_service.ring_phone(mock_http_client, settings=mock_settings)

    # Assertions
    assert "Ring request sent" in result
    assert "Jamie's phone" in result

    # Verify API call
    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    assert mock_settings.ifttt_webhook_key in call_args.args[0]
    assert mock_settings.ifttt_event_name in call_args.args[0]


@pytest.mark.asyncio
async def test_ring_phone_with_custom_message(mock_http_client, mock_settings):
    """Test phone ring with custom message."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.post.return_value = mock_response

    custom_message = "Emergency: wake up!"
    result = await phone_ifttt_service.ring_phone(mock_http_client, message=custom_message, settings=mock_settings)

    assert "Ring request sent" in result

    # Verify custom message was sent
    call_args = mock_http_client.post.call_args
    json_data = call_args.kwargs.get("json", {})
    assert json_data["value1"] == custom_message


@pytest.mark.asyncio
async def test_ring_phone_http_error(mock_http_client, mock_settings):
    """Test phone ring with HTTP error."""
    # Setup mock error response
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_http_client.post.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized", request=AsyncMock(), response=mock_response
    )

    # Call service and expect exception
    with pytest.raises(IFTTTException) as exc_info:
        await phone_ifttt_service.ring_phone(mock_http_client, settings=mock_settings)

    assert "IFTTT webhook request failed" in str(exc_info.value)
    assert mock_settings.ifttt_event_name in str(exc_info.value.details)


@pytest.mark.asyncio
async def test_ring_phone_network_error(mock_http_client, mock_settings):
    """Test phone ring with network error."""
    # Setup mock network error
    mock_http_client.post.side_effect = httpx.NetworkError("Connection failed")

    # Call service and expect exception (httpx.HTTPError raises IFTTTException)
    with pytest.raises(IFTTTException) as exc_info:
        await phone_ifttt_service.ring_phone(mock_http_client, settings=mock_settings)

    assert "IFTTT webhook request failed" in str(exc_info.value)
    assert mock_settings.ifttt_event_name in str(exc_info.value.details)


@pytest.mark.asyncio
async def test_ring_phone_timeout(mock_http_client, mock_settings):
    """Test phone ring with timeout."""
    # Setup mock timeout
    mock_http_client.post.side_effect = httpx.TimeoutException("Request timed out")

    # Call service and expect exception (httpx.HTTPError raises IFTTTException)
    with pytest.raises(IFTTTException) as exc_info:
        await phone_ifttt_service.ring_phone(mock_http_client, settings=mock_settings)

    assert "IFTTT webhook request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ring_phone_default_message(mock_http_client, mock_settings):
    """Test phone ring uses default message when none provided."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.post.return_value = mock_response

    await phone_ifttt_service.ring_phone(mock_http_client, settings=mock_settings)

    # Verify default message was used
    call_args = mock_http_client.post.call_args
    json_data = call_args.kwargs.get("json", {})
    assert "Ring from home dashboard" in json_data["value1"]


@pytest.mark.asyncio
async def test_ring_phone_timeout_parameter(mock_http_client, mock_settings):
    """Test phone ring includes timeout parameter."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    mock_http_client.post.return_value = mock_response

    await phone_ifttt_service.ring_phone(mock_http_client, settings=mock_settings)

    # Verify timeout was set
    call_args = mock_http_client.post.call_args
    assert call_args.kwargs["timeout"] == 10.0
