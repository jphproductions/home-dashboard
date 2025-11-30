"""IFTTT webhook service for phone notifications."""

import httpx
from api_app.config import settings


async def ring_phone(message: str = None) -> str:
    """
    Trigger IFTTT webhook to ring Jamie's phone.
    
    Args:
        message: Optional custom message (not used for basic ring, but for logging).
    
    Returns:
        Status message.
    
    Raises:
        Exception if webhook call fails.
    """
    try:
        webhook_url = f"https://maker.ifttt.com/trigger/{settings.ifttt_event_name}/with/key/{settings.ifttt_webhook_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={"value1": message or "Ring from home dashboard"},
                timeout=10.0,
            )
            response.raise_for_status()
        
        return "Ring request sent to Jamie's phone"
        
    except httpx.HTTPError as e:
        raise Exception(f"IFTTT webhook error: {str(e)}")
