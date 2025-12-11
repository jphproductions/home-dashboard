"""TV (Tizen) API routes with support for JSON and HTML responses."""

from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
import httpx

from home_dashboard.dependencies import get_http_client
from home_dashboard.services import tv_tizen_service

router = APIRouter()


@router.post("/wake")
async def wake_tv(
    client: httpx.AsyncClient = Depends(get_http_client),
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
):
    """Send Wake-on-LAN packet to TV.

    Args:
        client: HTTP client from dependency injection
        format: Response format - 'json' for API (html not applicable for this endpoint)

    Returns:
        JSON with status
    """
    try:
        result = await tv_tizen_service.wake()
        return {"status": "wol_sent", "action": "wake_tv", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TV wake error: {str(e)}") from e


@router.get("/status")
async def get_tv_status(
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
):
    """Get TV power status.

    Args:
        format: Response format - 'json' for API (html not applicable for this endpoint)

    Returns:
        JSON with TV status
    """
    try:
        is_on = await tv_tizen_service.get_status()
        return {"status": "on" if is_on else "off", "is_on": is_on}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TV power off error: {str(e)}") from e
