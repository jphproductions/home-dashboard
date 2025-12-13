"""TV (Tizen) API routes with support for JSON and HTML responses."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from home_dashboard.dependencies import get_tv_state_manager
from home_dashboard.security import verify_api_key
from home_dashboard.services import tv_tizen_service
from home_dashboard.state_managers import TVStateManager

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post(
    "/wake",
    summary="Wake Samsung TV",
    description="""
    Sends Wake-on-LAN magic packet to Samsung Tizen TV.

    Uses retry logic with exponential backoff (3 attempts: 1s, 2s, 4s delays).

    **Note:** TV must be on the same network and have Wake-on-LAN enabled.
    """,
    responses={
        200: {
            "description": "Wake command sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "wol_sent",
                        "action": "wake_tv",
                        "message": "TV woken successfully",
                    }
                }
            },
        },
        500: {"description": "TV wake error after retries"},
    },
)
async def wake_tv(
    tv_manager: TVStateManager = Depends(get_tv_state_manager),
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
):
    """Send Wake-on-LAN packet to TV.

    Args:
        client: HTTP client from dependency injection
        tv_manager: TV state manager from dependency injection
        format: Response format - 'json' for API (html not applicable for this endpoint)

    Returns:
        JSON with status
    """
    try:
        result = await tv_tizen_service.wake(tv_manager=tv_manager)
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
