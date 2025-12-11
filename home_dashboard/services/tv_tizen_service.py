"""Tizen WebSocket service for Samsung TV control."""

import asyncio
import json
import logging
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import websockets
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedOK,
    ConnectionClosedError,
    InvalidHandshake,
    InvalidURI,
)

from home_dashboard.config import Settings, get_settings
from home_dashboard.state_managers import TVStateManager
from home_dashboard.exceptions import TVException, TVConnectionException

logger = logging.getLogger(__name__)

# NOTE: Global state is deprecated - use TVStateManager via dependency injection


def _create_ssl_context() -> ssl.SSLContext:
    """Create SSL context for self-signed certificates.

    Per websockets 12.0 best practices: Use ssl_context instead of ssl=False.
    This properly configures SSL while disabling certificate verification
    for Samsung TV's self-signed certificates.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


@asynccontextmanager
async def _connect_to_tv(settings: Settings) -> AsyncGenerator:
    """Connect to TV with proper error handling.

    Per websockets 12.0 best practices:
    - Use async context manager for automatic cleanup
    - Handle all exception types explicitly
    - Configure timeouts to prevent hanging
    - Use proper SSL context for self-signed certs

    Args:
        settings: Settings instance

    Yields:
        WebSocket connection

    Raises:
        TVException: If connection fails
    """
    ws_url = f"wss://{settings.tv_ip}:8002/api/v2/channels/samsung.remote.control?name=PythonDashboard"
    ssl_context = _create_ssl_context()

    try:
        async with websockets.connect(
            ws_url,
            ssl=ssl_context,  # ✅ Use SSL context, not ssl=False
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
            open_timeout=10,
        ) as websocket:
            # Send handshake
            handshake = {
                "method": "ms.channel.connect",
                "params": {
                    "sessionId": "",
                    "clientIp": "",
                    "deviceName": "PythonDashboard",
                },
            }
            await websocket.send(json.dumps(handshake))

            # Wait for handshake response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.debug(f"TV handshake response: {response!r}")
            except asyncio.TimeoutError:
                raise TVConnectionException(
                    "TV handshake timeout",
                    details={"tv_ip": str(settings.tv_ip), "error_type": "handshake_timeout"},
                )

            yield websocket

    except ConnectionClosedOK:
        logger.info("TV connection closed normally")

    except ConnectionClosedError as e:
        raise TVConnectionException(
            f"TV connection closed with error: {e.code} - {e.reason}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "connection_closed",
                "close_code": e.code,
                "reason": e.reason,
            },
        ) from e

    except InvalidURI as e:
        raise TVConnectionException(
            f"Invalid TV WebSocket URI: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "invalid_uri",
                "uri": ws_url,
            },
        ) from e

    except InvalidHandshake as e:
        raise TVConnectionException(
            f"TV WebSocket handshake failed: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "invalid_handshake",
            },
        ) from e

    except OSError as e:
        raise TVConnectionException(
            f"Cannot reach TV at {settings.tv_ip}: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "network_error",
            },
        ) from e

    except asyncio.TimeoutError:
        raise TVConnectionException(
            "TV connection timeout",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "connection_timeout",
                "timeout": "10s",
            },
        )


async def wake(settings: Settings | None = None, tv_manager: TVStateManager | None = None) -> str:
    """
    Send KEY_POWER to TV to wake it (toggle power).

    Uses WebSocket to Tizen TV API with proper SSL handling.

    Args:
        settings: Settings instance (defaults to singleton)
        tv_manager: TV state manager for failure tracking (optional)

    Returns:
        Status message.

    Raises:
        TVConnectionException: If connection fails.
    """
    if settings is None:
        settings = get_settings()

    try:
        async with _connect_to_tv(settings) as websocket:
            # Send KEY_POWER
            key_command = {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": "SendRemoteKey",
                    "DataOfCmd": "KEY_POWER",
                    "Option": "false",
                },
            }
            await websocket.send(json.dumps(key_command))

            # Reset failure count on success
            if tv_manager:
                await tv_manager.reset_wake_failures()

            logger.info(f"Successfully sent KEY_POWER to TV at {settings.tv_ip}")
            return "KEY_POWER sent to TV"

    except TVConnectionException as e:
        # Track failure
        if tv_manager:
            count = await tv_manager.increment_wake_failure()
            logger.warning(f"TV wake failed (attempt {count}): {e.message}")

            # Optional: escalate to phone notification after N failures
            if count >= 5:
                logger.error("TV wake failed 5+ times, consider escalating")
        else:
            logger.warning(f"TV wake failed: {e.message}")

        raise


async def get_status(settings: Settings | None = None) -> bool:
    """
    Get TV power status (experimental).

    Args:
        settings: Settings instance (defaults to singleton)

    Returns:
        True if TV is on, False if off.
    """
    if settings is None:
        settings = get_settings()

    try:
        # Try to connect as a simple reachability test
        # Note: actual power state detection via Tizen is unreliable
        async with _connect_to_tv(settings) as websocket:
            # If we successfully connected and got handshake response,
            # assume TV is reachable (on or standby)
            return True

    except TVConnectionException as e:
        logger.debug(f"TV status check failed: {e.message}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during TV status check: {e}")
        return False
