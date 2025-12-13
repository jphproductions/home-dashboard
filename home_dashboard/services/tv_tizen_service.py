"""Tizen WebSocket service for Samsung TV control."""

import asyncio
import json
import ssl
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TypeVar

import websockets
from websockets.exceptions import (
    ConnectionClosedError,
    ConnectionClosedOK,
    InvalidHandshake,
    InvalidURI,
)

from home_dashboard.config import Settings, get_settings
from home_dashboard.exceptions import TVConnectionException
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.state_managers import TVStateManager

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0  # seconds

T = TypeVar("T")


async def _retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    operation_name: str,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF,
) -> T:
    """Retry an async operation with exponential backoff.

    Args:
        operation: Async function to retry
        operation_name: Name for logging
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff delay in seconds

    Returns:
        Result of operation

    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None
    backoff = initial_backoff

    for attempt in range(max_retries + 1):
        try:
            result: T = await operation()
            return result
        except (TVConnectionException, OSError, TimeoutError) as e:
            last_exception = e

            if attempt < max_retries:
                log_with_context(
                    logger,
                    "warning",
                    f"{operation_name} failed, retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    backoff=backoff,
                    error=str(e),
                    event_type="tv_retry",
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)  # Exponential backoff with cap
            else:
                log_with_context(
                    logger,
                    "error",
                    f"{operation_name} failed after all retries",
                    attempts=max_retries + 1,
                    error=str(e),
                    event_type="tv_retry_exhausted",
                )

    if last_exception:
        raise last_exception
    raise TVConnectionException(f"{operation_name} failed with no exception recorded")


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
                log_with_context(
                    logger,
                    "debug",
                    "TV handshake response received",
                    tv_ip=str(settings.tv_ip),
                    response=str(response),
                    event_type="tv_handshake",
                )
            except TimeoutError:
                raise TVConnectionException(
                    "TV handshake timeout",
                    details={"tv_ip": str(settings.tv_ip), "error_type": "handshake_timeout"},
                ) from None

            yield websocket

    except ConnectionClosedOK:
        log_with_context(
            logger,
            "info",
            "TV connection closed normally",
            tv_ip=str(settings.tv_ip),
            event_type="tv_connection_closed",
        )

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
    except TimeoutError:
        raise TVConnectionException(
            "TV connection timeout",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "connection_timeout",
                "timeout": "10s",
            },
        ) from None


async def wake(settings: Settings | None = None, tv_manager: TVStateManager | None = None) -> str:
    """
    Send KEY_POWER to TV to wake it (toggle power).

    Uses WebSocket to Tizen TV API with proper SSL handling and automatic retries.

    Args:
        settings: Settings instance (defaults to singleton)
        tv_manager: TV state manager for failure tracking (optional)

    Returns:
        Status message.

    Raises:
        TVConnectionException: If connection fails after all retries.
    """
    if settings is None:
        settings = get_settings()

    async def _send_wake_command() -> str:
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

            log_with_context(
                logger,
                "info",
                "Successfully sent KEY_POWER to TV",
                tv_ip=str(settings.tv_ip),
                event_type="tv_wake_success",
            )
            return "KEY_POWER sent to TV"

    try:
        result: str = await _retry_with_backoff(_send_wake_command, "TV wake command")

        # Reset failure count on success
        if tv_manager:
            await tv_manager.reset_wake_failures()

        return result

    except TVConnectionException as e:
        # Track failure
        if tv_manager:
            count = await tv_manager.increment_wake_failure()
            log_with_context(
                logger,
                "warning",
                "TV wake failed after retries",
                tv_ip=str(settings.tv_ip),
                attempt=count,
                error=e.message,
                event_type="tv_wake_failure",
            )

            # Log multiple failures for monitoring
            if count >= 5:
                log_with_context(
                    logger,
                    "error",
                    "TV wake failed multiple times",
                    tv_ip=str(settings.tv_ip),
                    failure_count=count,
                    event_type="tv_wake_multiple_failures",
                )
        else:
            log_with_context(
                logger,
                "warning",
                "TV wake failed after retries",
                tv_ip=str(settings.tv_ip),
                error=e.message,
                event_type="tv_wake_failure",
            )

        raise


async def get_status(settings: Settings | None = None) -> bool:
    """
    Check if TV is reachable via WebSocket connection.

    Tests TV reachability by attempting WebSocket handshake.
    If successful, TV is on and accepting connections.

    Args:
        settings: Settings instance (defaults to singleton)

    Returns:
        True if TV is reachable (on/standby), False if unreachable (off/network issue).
    """
    if settings is None:
        settings = get_settings()

    try:
        # Try to connect as a simple reachability test
        async with _connect_to_tv(settings) as _:
            # If we successfully connected and got handshake response,
            # TV is reachable (on or standby)
            return True

    except TVConnectionException as e:
        log_with_context(
            logger,
            "debug",
            "TV status check failed",
            tv_ip=str(settings.tv_ip),
            error=e.message,
            event_type="tv_status_check_failed",
        )
        return False
    except Exception as e:
        log_with_context(
            logger,
            "warning",
            "Unexpected error during TV status check",
            tv_ip=str(settings.tv_ip),
            error=str(e),
            error_type=type(e).__name__,
            event_type="tv_status_unexpected_error",
        )
        return False
