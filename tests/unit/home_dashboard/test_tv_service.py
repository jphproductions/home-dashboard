"""Unit tests for TV Tizen service."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from websockets.exceptions import ConnectionClosedError, InvalidHandshake, InvalidURI

from home_dashboard.exceptions import TVConnectionException
from home_dashboard.services import tv_tizen_service


@pytest.mark.asyncio
async def test_wake_tv_success(mock_settings, mock_websocket, mock_tv_state_manager):
    """Test successful TV wake command."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        result = await tv_tizen_service.wake(mock_settings, mock_tv_state_manager)

        assert "KEY_POWER sent to TV" in result
        # Verify websocket.send was called with KEY_POWER command
        assert mock_websocket.send.called
        call_arg = json.loads(mock_websocket.send.call_args[0][0])
        assert call_arg["params"]["Cmd"] == "SendRemoteKey"
        assert call_arg["params"]["DataOfCmd"] == "KEY_POWER"
        # Verify failure count was reset
        mock_tv_state_manager.reset_wake_failures.assert_called_once()


@pytest.mark.asyncio
async def test_wake_tv_connection_error(mock_settings, mock_tv_state_manager):
    """Test TV wake fails with connection error."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.side_effect = ConnectionClosedError(None, None)

        with pytest.raises(TVConnectionException) as exc_info:
            await tv_tizen_service.wake(mock_settings, mock_tv_state_manager)

        assert "TV connection closed with error" in str(exc_info.value)
        # Verify failure was tracked
        mock_tv_state_manager.increment_wake_failure.assert_called_once()


@pytest.mark.asyncio
async def test_wake_tv_invalid_handshake(mock_settings, mock_tv_state_manager):
    """Test TV wake fails with invalid handshake."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.side_effect = InvalidHandshake("Invalid handshake")

        with pytest.raises(TVConnectionException) as exc_info:
            await tv_tizen_service.wake(mock_settings, mock_tv_state_manager)

        assert "TV WebSocket handshake failed" in str(exc_info.value)
        mock_tv_state_manager.increment_wake_failure.assert_called_once()


@pytest.mark.asyncio
async def test_wake_tv_invalid_uri(mock_settings, mock_tv_state_manager):
    """Test TV wake fails with invalid URI."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.side_effect = InvalidURI("wss://bad", "Invalid URI")

        with pytest.raises(TVConnectionException) as exc_info:
            await tv_tizen_service.wake(mock_settings, mock_tv_state_manager)

        assert "Invalid TV WebSocket URI" in str(exc_info.value)
        mock_tv_state_manager.increment_wake_failure.assert_called_once()


@pytest.mark.asyncio
async def test_wake_tv_handshake_timeout(mock_settings, mock_tv_state_manager):
    """Test TV wake fails when handshake times out."""
    mock_websocket = AsyncMock()
    mock_websocket.send = AsyncMock()
    # Make recv timeout
    mock_websocket.recv = AsyncMock(side_effect=TimeoutError())

    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        with pytest.raises(TVConnectionException) as exc_info:
            await tv_tizen_service.wake(mock_settings, mock_tv_state_manager)

        assert "TV handshake timeout" in str(exc_info.value)
        assert "handshake_timeout" in str(exc_info.value.details)


@pytest.mark.asyncio
async def test_wake_tv_tracks_multiple_failures(mock_settings, mock_tv_state_manager):
    """Test TV wake tracks failure count."""
    # Simulate 5th failure
    mock_tv_state_manager.increment_wake_failure.return_value = 5

    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.side_effect = ConnectionClosedError(None, None)

        with pytest.raises(TVConnectionException):
            await tv_tizen_service.wake(mock_settings, mock_tv_state_manager)

        # Should track failure and log critical after 5+ failures
        assert mock_tv_state_manager.increment_wake_failure.called


@pytest.mark.asyncio
async def test_wake_tv_without_state_manager(mock_settings, mock_websocket):
    """Test TV wake works without state manager."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        result = await tv_tizen_service.wake(mock_settings, tv_manager=None)

        assert "KEY_POWER sent to TV" in result
        assert mock_websocket.send.called


@pytest.mark.asyncio
async def test_get_status_success(mock_settings, mock_websocket):
    """Test successful TV status check returns True."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        result = await tv_tizen_service.get_status(mock_settings)

        assert result is True


@pytest.mark.asyncio
async def test_get_status_connection_failure(mock_settings):
    """Test TV status check returns False when connection fails."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.side_effect = ConnectionClosedError(None, None)

        result = await tv_tizen_service.get_status(mock_settings)

        assert result is False


@pytest.mark.asyncio
async def test_get_status_unexpected_error(mock_settings):
    """Test TV status check returns False on unexpected error."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.side_effect = Exception("Unexpected error")

        result = await tv_tizen_service.get_status(mock_settings)

        assert result is False


@pytest.mark.asyncio
async def test_create_ssl_context():
    """Test SSL context creation for self-signed certificates."""
    import ssl

    ssl_context = tv_tizen_service._create_ssl_context()

    assert isinstance(ssl_context, ssl.SSLContext)
    assert ssl_context.check_hostname is False
    assert ssl_context.verify_mode == ssl.CERT_NONE


@pytest.mark.asyncio
async def test_wake_tv_uses_correct_ip(mock_settings, mock_websocket):
    """Test wake command uses correct TV IP from settings."""
    with patch("home_dashboard.services.tv_tizen_service.websockets.connect") as mock_connect:
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        await tv_tizen_service.wake(mock_settings, tv_manager=None)

        # Verify connect was called with correct URL containing TV IP
        call_args = mock_connect.call_args
        assert str(mock_settings.tv_ip) in call_args[0][0]
        assert "8002" in call_args[0][0]  # WebSocket port
