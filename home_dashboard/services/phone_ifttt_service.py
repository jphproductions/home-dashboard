"""IFTTT webhook service for phone notifications."""

import httpx
from typing import Optional
from home_dashboard.config import Settings, get_settings


async def ring_phone(client: httpx.AsyncClient, message: Optional[str] = None, settings: Settings | None = None) -> str:
    """
    Trigger IFTTT webhook to ring Jamie's phone.

    Args:
        client: Shared HTTP client from dependency injection.
        message: Optional custom message (not used for basic ring, but for logging).
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
            json={"value1": message or "Ring from home dashboard"},
            timeout=10.0,
        )
        response.raise_for_status()
        return "Ring request sent to Jamie's phone"
    except httpx.HTTPError as e:
        raise Exception(f"IFTTT webhook error: {str(e)}") from e
    except Exception as e:
        # Catch-all for network issues, timeouts, etc.
        raise Exception(f"Failed to send ring request: {str(e)}") from e
