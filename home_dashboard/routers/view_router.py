"""Page/view routes for serving HTML pages and tile fragments."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import httpx

from home_dashboard.dependencies import get_http_client, get_spotify_auth_manager
from home_dashboard.views.template_renderer import TemplateRenderer
from home_dashboard.state_managers import SpotifyAuthManager

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render main dashboard page."""
    return TemplateRenderer.render_index(request)


@router.get("/tiles/spotify", response_class=HTMLResponse)
async def spotify_tile(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
):
    """Render Spotify tile fragment."""
    return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)


@router.get("/tiles/weather", response_class=HTMLResponse)
async def weather_tile(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Render Weather tile fragment."""
    return await TemplateRenderer.render_weather_tile(request, client)


@router.get("/tiles/phone", response_class=HTMLResponse)
async def phone_tile(request: Request):
    """Render Phone tile fragment."""
    return TemplateRenderer.render_phone_tile(request)


@router.get("/tiles/quick-actions", response_class=HTMLResponse)
async def quick_actions_tile(request: Request):
    """Render Quick Actions tile fragment."""
    return TemplateRenderer.render_quick_actions_tile(request)


@router.get("/tiles/status", response_class=HTMLResponse)
async def status_tile(request: Request):
    """Render Status tile fragment."""
    return TemplateRenderer.render_status_tile(request)
