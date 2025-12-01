"""Tizen WebSocket service for Samsung TV control."""

import asyncio
import json
import websockets
from api_app.config import settings


# Simple in-memory state tracker
_wake_failure_count = 0


async def wake() -> str:
    """
    Send KEY_POWER to TV to wake it (toggle power).

    Uses WebSocket to Tizen TV API.

    Returns:
        Status message.

    Raises:
        Exception if connection fails.
    """
    global _wake_failure_count
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
        print(f"TV handshake response: {response}")

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

        _wake_failure_count = 0
        return "KEY_POWER sent to TV"

    except Exception as e:
        _wake_failure_count += 1
        print(f"TV wake failed (attempt {_wake_failure_count}): {str(e)}")

        # Optional: escalate to phone notification after N failures
        if _wake_failure_count >= 5:
            print("TV wake failed 5+ times, consider escalating")

        raise Exception(f"Tizen wake error: {str(e)}") from e
    finally:
        # Ensure WebSocket is always closed
        if ws:
            await ws.close()


async def get_status() -> bool:
    """
    Get TV power status (experimental).

    Returns:
        True if TV is on, False if off.

    Raises:
        Exception if status check fails.
    """
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
