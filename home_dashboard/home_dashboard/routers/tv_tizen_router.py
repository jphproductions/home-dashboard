"""TV Tizen API routes."""

from fastapi import APIRouter, HTTPException
from home_dashboard.services import tv_tizen_service

router = APIRouter()


@router.post("/wake")
async def wake_tv():
    """Wake TV by sending KEY_POWER."""
    try:
        result = await tv_tizen_service.wake()
        return {"status": "wake_sent", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TV error: {str(e)}")


@router.get("/status")
async def get_tv_status():
    """Get TV power status (experimental)."""
    try:
        status = await tv_tizen_service.get_status()
        return {"power_on": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TV status error: {str(e)}")
