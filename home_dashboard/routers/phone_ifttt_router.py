"""Phone/IFTTT API routes with support for JSON and HTML responses."""

from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from home_dashboard.config import Settings, get_settings
from home_dashboard.dependencies import get_http_client
from home_dashboard.security import verify_api_key
from home_dashboard.services import phone_ifttt_service
from home_dashboard.views.template_renderer import TemplateRenderer

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/ring",
    dependencies=[Depends(verify_api_key)],
    summary="Trigger phone ring via IFTTT",
    description="""
    Triggers an IFTTT webhook to ring a phone.

    **🔒 Authentication Required:** This endpoint requires Bearer token authentication.

    **⚡ Rate Limited:** 5 requests/minute to prevent abuse.

    Use this to locate a phone or get someone's attention.
    """,
    responses={
        200: {
            "description": "Webhook triggered successfully",
            "content": {"application/json": {"example": {"status": "webhook_triggered", "action": "ring_phone"}}},
        },
        401: {"description": "Unauthorized - missing or invalid API key"},
        500: {"description": "IFTTT webhook error"},
    },
)
@limiter.limit("5/minute")
async def ring_phone(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
):
    """Trigger IFTTT webhook to ring phone.

    **Protected endpoint**: Requires API key authentication.
    **Rate limited**: 5 requests per minute per IP.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment

    Security:
        - Requires Bearer token authentication
        - Rate limited to prevent abuse
    """
    try:
        await phone_ifttt_service.ring_phone(client, settings)

        if format == "html":
            return TemplateRenderer.render_phone_tile(request)

        return {"status": "webhook_triggered", "action": "ring_phone"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IFTTT error: {str(e)}") from e
