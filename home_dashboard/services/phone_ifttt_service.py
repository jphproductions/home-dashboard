"""IFTTT webhook service for phone notifications."""

import httpx

from home_dashboard.config import Settings, get_settings
from home_dashboard.exceptions import IFTTTException, PhoneException


async def ring_phone(client: httpx.AsyncClient, settings: Settings | None = None) -> str:
    """
    Trigger IFTTT webhook to ring phone.

    Args:
        client: Shared HTTP client from dependency injection.
        settings: Settings instance (defaults to singleton)

    Returns:
        Status message.

    Raises:
        Exception if webhook call fails.
    """
    if settings is None:
        settings = get_settings()
    webhook_url = f"https://maker.ifttt.com/trigger/{settings.ifttt_event_name}/with/key/{settings.ifttt_webhook_key}"

    try:
        response = await client.post(
            webhook_url,
            json={"value1": "Ring from home dashboard"},
            timeout=10.0,
        )
        response.raise_for_status()
        return "Ring request sent successfully"
    except httpx.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else 502
        raise IFTTTException(
            f"IFTTT webhook request failed: {str(e)}",
            details={
                "event_name": settings.ifttt_event_name,
                "status_code": status_code,
            },
        ) from e
    except Exception as e:
        # Catch-all for network issues, timeouts, etc.
        raise PhoneException(
            f"Failed to send ring request: {str(e)}",
            details={"error_type": "network_error"},
        ) from e
