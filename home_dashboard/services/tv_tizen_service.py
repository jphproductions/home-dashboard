"""Tizen WebSocket service for Samsung TV control."""

import json
import websockets
from home_dashboard.config import Settings, get_settings
from home_dashboard.state_managers import TVStateManager
from home_dashboard.exceptions import TVException, TVConnectionException


# NOTE: Global state is deprecated - use TVStateManager via dependency injection


async def wake(settings: Settings | None = None, tv_manager: TVStateManager | None = None) -> str:
    """
    Send KEY_POWER to TV to wake it (toggle power).

    Uses WebSocket to Tizen TV API.

    Args:
        settings: Settings instance (defaults to singleton)
        tv_manager: TV state manager for failure tracking (optional)

    Returns:
        Status message.

    Raises:
        Exception if connection fails.
    """
    if settings is None:
        settings = get_settings()

    ws = None

    try:
        # Connect to Tizen TV
        ws_url = f"wss://{settings.tv_ip}:8002/api/v2/channels/samsung.remote.control?name=PythonRemote"

        ws = await websockets.connect(
            ws_url,
            ssl=False,  # Note: self-signed cert, so ssl=False for now
            ping_interval=None,
        )

        # Send handshake
        handshake = {
            "method": "ms.channel.connect",
            "params": {
                "sessionId": "",
                "clientIp": "",
                "deviceName": "PythonDashboard",
            },
        }
        await ws.send(json.dumps(handshake))

        # Wait for response
        response = await ws.recv()
        print(f"TV handshake response: {response!r}")

        # Send KEY_POWER
        key_command = {
            "method": "ms.remote.control",
            "params": {
                "Cmd": "SendRemoteKey",
                "DataOfCmd": "KEY_POWER",
                "Option": "false",
            },
        }
        await ws.send(json.dumps(key_command))

        # Reset failure count on success
        if tv_manager:
            await tv_manager.reset_wake_failures()
        return "KEY_POWER sent to TV"

    except Exception as e:
        # Track failure
        if tv_manager:
            count = await tv_manager.increment_wake_failure()
            print(f"TV wake failed (attempt {count}): {str(e)}")

            # Optional: escalate to phone notification after N failures
            if count >= 5:
                print("TV wake failed 5+ times, consider escalating")
        else:
            print(f"TV wake failed: {str(e)}")

        raise TVConnectionException(
            f"Failed to connect to TV: {str(e)}",
            details={
                "tv_ip": settings.tv_ip,
                "error_type": "websocket_connection",
            },
        ) from e
    finally:
        # Ensure WebSocket is always closed
        if ws:
            await ws.close()


async def get_status(settings: Settings | None = None) -> bool:
    """
    Get TV power status (experimental).

    Args:
        settings: Settings instance (defaults to singleton)

    Returns:
        True if TV is on, False if off.

    Raises:
        TVException if status check fails.
    """
    if settings is None:
        settings = get_settings()

    try:
        # This is a placeholder; actual power state detection via Tizen is unreliable
        # Try to connect as a simple test
        ws_url = f"wss://{settings.tv_ip}:8002/api/v2/channels/samsung.remote.control?name=PythonRemote"

        async with websockets.connect(
            ws_url,
            ssl=False,
            ping_interval=None,
        ) as ws:
            handshake = {
                "method": "ms.channel.connect",
                "params": {
                    "sessionId": "",
                    "clientIp": "",
                    "deviceName": "PythonDashboard",
                },
            }
            await ws.send(json.dumps(handshake))
            response = await ws.recv()

            # If we got a response, assume TV is reachable (on or standby)
            return True

    except Exception as e:
        print(f"TV status check failed: {str(e)}")
        return False
