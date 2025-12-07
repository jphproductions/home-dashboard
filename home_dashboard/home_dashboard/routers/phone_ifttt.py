"""Phone IFTTT API routes."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from home_dashboard.dependencies import get_http_client
from home_dashboard.services import phone_ifttt_service
from home_dashboard.models.phone import PhoneRingRequest

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


@router.post("/ring-and-refresh")
async def ring_phone_and_refresh(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Ring Jamie's phone and return updated tile HTML."""
    from fastapi.templating import Jinja2Templates
    from pathlib import Path
    
    TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    
    try:
        await phone_ifttt_service.ring_phone(client, "Ring from dashboard")
        
        return templates.TemplateResponse(
            "tiles/phone.html",
            {
                "request": request,
                "success": True,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "tiles/phone.html",
            {
                "request": request,
                "success": False,
                "error": str(e),
            }
        )
