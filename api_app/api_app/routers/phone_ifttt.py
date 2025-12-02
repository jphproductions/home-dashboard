"""Phone IFTTT API routes."""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from api_app.dependencies import get_http_client
from api_app.services import phone_ifttt_service
from shared.models.phone import PhoneRingRequest

router = APIRouter()


@router.post("/ring")
async def ring_phone(
    request: PhoneRingRequest = PhoneRingRequest(), client: httpx.AsyncClient = Depends(get_http_client)
):
    """Ring Jamie's phone via IFTTT webhook."""
    try:
        result = await phone_ifttt_service.ring_phone(client, request.message)
        return {"status": "ring_sent", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phone ring error: {str(e)}") from e
