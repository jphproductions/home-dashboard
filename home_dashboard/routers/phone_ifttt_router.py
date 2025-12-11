"""Phone/IFTTT API routes with support for JSON and HTML responses."""

from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from home_dashboard.dependencies import get_http_client
from home_dashboard.services import phone_ifttt_service
from home_dashboard.views.template_renderer import TemplateRenderer

router = APIRouter()


@router.post("/ring")
async def ring_phone(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
):
    """Trigger IFTTT webhook to ring phone.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await phone_ifttt_service.ring_phone(client)

        if format == "html":
            return TemplateRenderer.render_phone_tile(request)

        return {"status": "webhook_triggered", "action": "ring_phone"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IFTTT error: {str(e)}") from e
