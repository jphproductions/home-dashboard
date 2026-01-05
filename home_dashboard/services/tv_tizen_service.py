"""Simplified Tizen TV service for Samsung TV control."""

import asyncio
import base64
import json
import ssl

import httpx
import websockets

from home_dashboard.config import Settings, get_settings
from home_dashboard.exceptions import TVConnectionException
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.models.base_models import TVInfo
from home_dashboard.state_managers import TVStateManager

logger = get_logger(__name__)


async def get_info(settings: Settings | None = None) -> TVInfo:
    """Get TV information via HTTP REST API.

    Args:
        settings: Settings instance (defaults to singleton)

    Returns:
        TVInfo model with device information

    Raises:
        TVConnectionException: If connection fails
    """
    if settings is None:
        settings = get_settings()

    url = f"http://{settings.tv_ip}:8001/api/v2/"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            tv_info = TVInfo(**data)

            log_with_context(
                logger,
                "debug",
                "TV info received",
                tv_ip=str(settings.tv_ip),
                power_state=tv_info.device.PowerState,
                model=tv_info.device.modelName,
                event_type="tv_info",
            )

            return tv_info

    except httpx.HTTPStatusError as e:
        raise TVConnectionException(
            f"HTTP error getting TV info: {e.response.status_code}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "http_error",
                "status_code": e.response.status_code,
            },
        ) from e
    except httpx.RequestError as e:
        raise TVConnectionException(
            f"Cannot reach TV at {settings.tv_ip}: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "network_error",
            },
        ) from e


async def _send_key(key: str, settings: Settings, tv_manager: TVStateManager | None = None) -> None:
    """Send a key command to the TV via WebSocket.

    Args:
        key: Key code (e.g., 'KEY_POWER', 'KEY_VOLUP')
        settings: Settings instance
        tv_manager: TV state manager for token storage (optional)

    Raises:
        TVConnectionException: If connection fails
    """
    # Get stored token if available
    token = None
    if tv_manager:
        token = await tv_manager.get_tv_token()

    # Build WebSocket URL
    device_name = base64.b64encode(str.encode("HomeDashboard")).decode("utf-8")
    ws_url = f"wss://{settings.tv_ip}:8002/api/v2/channels/samsung.remote.control?name={device_name}"
    if token:
        ws_url += f"&token={token}"

    # SSL context for self-signed cert
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        websocket = await websockets.connect(
            ws_url,
            ssl=ssl_context,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
            open_timeout=10,
        )

        # Send handshake
        handshake = {
            "method": "ms.channel.connect",
            "params": {
                "sessionId": "",
                "clientIp": "",
                "deviceName": "HomeDashboard",
            },
        }
        await websocket.send(json.dumps(handshake))

        # Wait for authorization with timeout
        try:
            timeout_time = asyncio.get_event_loop().time() + 30.0
            authorized = False

            while asyncio.get_event_loop().time() < timeout_time:
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(), timeout=max(1.0, timeout_time - asyncio.get_event_loop().time())
                    )
                    response_data = json.loads(response)
                    event = response_data.get("event")

                    if event == "ms.channel.connect":
                        # Store token for future use
                        if tv_manager:
                            data = response_data.get("data", {})
                            auth_token = data.get("token")
                            client_id = data.get("id")
                            if auth_token:
                                await tv_manager.set_tv_auth(auth_token, client_id)
                                log_with_context(
                                    logger,
                                    "info",
                                    "Stored TV authorization token",
                                    tv_ip=str(settings.tv_ip),
                                    event_type="tv_token_stored",
                                )
                        authorized = True
                        break
                    elif event == "ms.channel.unauthorized":
                        # Keep waiting for user approval
                        continue

                except TimeoutError:
                    break

            if not authorized:
                await websocket.close()
                raise TVConnectionException(
                    "TV connection not authorized - please allow access on TV",
                    details={
                        "tv_ip": str(settings.tv_ip),
                        "error_type": "authorization_timeout",
                    },
                )

            # Send key command
            key_command = {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": "Click",
                    "DataOfCmd": key,
                    "Option": "false",
                    "TypeOfRemote": "SendRemoteKey",
                },
            }
            await websocket.send(json.dumps(key_command))

            log_with_context(
                logger,
                "info",
                f"Sent {key} to TV",
                tv_ip=str(settings.tv_ip),
                key=key,
                used_token=bool(token),
                event_type="tv_key_sent",
            )

        finally:
            await websocket.close()

    except Exception as e:
        raise TVConnectionException(
            f"Failed to send key {key} to TV: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "websocket_error",
                "key": key,
            },
        ) from e


async def launch_app(
    app_id: str,
    settings: Settings | None = None,
    tv_manager: TVStateManager | None = None,
    app_type: str = "DEEP_LINK",
    meta_tag: str = "",
) -> None:
    """Launch an application on the TV via WebSocket.

    Args:
        app_id: Application ID (e.g., '3201606009684' for Spotify)
        settings: Settings instance (defaults to singleton)
        tv_manager: TV state manager for token storage (optional)
        app_type: Launch type - 'DEEP_LINK' or 'NATIVE_LAUNCH' (default: 'DEEP_LINK')
        meta_tag: Optional metadata/deep link payload

    Raises:
        TVConnectionException: If connection fails
    """
    if settings is None:
        settings = get_settings()

    device_name = base64.b64encode(b"home-dashboard").decode("utf-8")
    token = tv_manager.get_tv_token() if tv_manager else None

    ws_url = f"wss://{settings.tv_ip}:8002/api/v2/channels/samsung.remote.control"
    if token:
        ws_url += f"?name={device_name}&token={token}"
    else:
        ws_url += f"?name={device_name}"

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(ws_url, ssl=ssl_context, close_timeout=2) as websocket:
            # Wait for authorization response
            auth_response = await websocket.recv()
            auth_data = json.loads(auth_response)

            # Extract and store token if present
            if not token and auth_data.get("data", {}).get("token"):
                new_token = auth_data["data"]["token"]
                client_id = auth_data["data"].get("clients", [{}])[0].get("id")
                if tv_manager:
                    tv_manager.set_tv_auth(new_token, client_id)

            # Send app launch command
            launch_command = {
                "method": "ms.channel.emit",
                "params": {
                    "event": "ed.apps.launch",
                    "to": "host",
                    "data": {
                        "action_type": app_type,
                        "appId": app_id,
                        "metaTag": meta_tag,
                    },
                },
            }
            await websocket.send(json.dumps(launch_command))

            log_with_context(
                logger,
                "info",
                f"Launched app {app_id}",
                tv_ip=str(settings.tv_ip),
                app_id=app_id,
                app_type=app_type,
                used_token=bool(token),
                event_type="tv_app_launch",
            )

    except Exception as e:
        raise TVConnectionException(
            f"Failed to launch app {app_id}: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "websocket_error",
                "app_id": app_id,
            },
        ) from e


async def wake(settings: Settings | None = None, tv_manager: TVStateManager | None = None) -> str:
    """Wake the TV if it's in standby.

    Gets the TV power state and sends KEY_POWER only if needed.

    Args:
        settings: Settings instance (defaults to singleton)
        tv_manager: TV state manager for token storage (optional)

    Returns:
        Status message

    Raises:
        TVConnectionException: If connection fails
    """
    if settings is None:
        settings = get_settings()

    try:
        # Get TV info to check power state
        tv_info = await get_info(settings)
        power_state = tv_info.power_state

        log_with_context(
            logger,
            "info",
            "TV power state checked",
            tv_ip=str(settings.tv_ip),
            power_state=power_state,
            event_type="tv_power_check",
        )

        if power_state == "standby":
            # TV is off, send power key
            await _send_key("KEY_POWER", settings, tv_manager)
            return "TV was in standby, sent KEY_POWER"
        elif power_state == "on":
            # TV is already on
            return "TV is already on"
        else:
            # Unknown state, try to wake anyway
            await _send_key("KEY_POWER", settings, tv_manager)
            return f"TV power state unknown ({power_state}), sent KEY_POWER"

    except TVConnectionException:
        raise
    except Exception as e:
        raise TVConnectionException(
            f"Failed to wake TV: {e}",
            details={
                "tv_ip": str(settings.tv_ip),
                "error_type": "wake_error",
            },
        ) from e
