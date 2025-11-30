"""Phone IFTTT API routes."""

from fastapi import APIRouter, HTTPException
from api_app.services import phone_ifttt_service
from api_app.models import PhoneRingRequest

router = APIRouter()


@router.post("/ring")
async def ring_phone(request: PhoneRingRequest = PhoneRingRequest()):
    """Ring Jamie's phone via IFTTT webhook."""
    try:
        result = await phone_ifttt_service.ring_phone(request.message)
        return {"status": "ring_sent", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phone ring error: {str(e)}")
