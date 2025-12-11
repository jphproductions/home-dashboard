"""Spotify API routes with support for JSON and HTML responses."""

import asyncio
import secrets
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from home_dashboard.config import Settings, get_settings
from home_dashboard.dependencies import get_http_client, get_spotify_auth_manager, get_tv_state_manager
from home_dashboard.services import spotify_service
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager
from home_dashboard.views.template_renderer import TemplateRenderer

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Store state for OAuth flow (in production, use Redis or database)
_oauth_states = {}

# Spotify OAuth scopes needed for playback control
SPOTIFY_SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "user-read-recently-played",
]


@router.get("/status")
@limiter.limit("60/minute")
async def get_spotify_status(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
):
    """Get current Spotify playback status.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with SpotifyStatus model or HTML tile fragment
    """
    try:
        if format == "html":
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)

        # JSON response
        status = await spotify_service.get_current_track(client, auth_manager)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/play")
@limiter.limit("30/minute")
async def play(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
):
    """Resume playback.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await spotify_service.play(client, auth_manager)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)

        return {"status": "playing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/pause")
async def pause(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
):
    """Pause playback.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await spotify_service.pause(client, auth_manager)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)

        return {"status": "paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/next")
async def next_track(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    settings: Settings = Depends(get_settings),
):
    """Skip to next track.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await spotify_service.next_track(client, auth_manager)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)

        return {"status": "next_track"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/previous")
async def previous_track(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    settings: Settings = Depends(get_settings),
):
    """Go to previous track.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await spotify_service.previous_track(client, auth_manager)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)

        return {"status": "previous_track"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/wake-and-play")
async def wake_tv_and_play(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    tv_manager: TVStateManager = Depends(get_tv_state_manager),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
):
    """Wake TV and transfer Spotify playback to TV.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        tv_manager: TV state manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await spotify_service.wake_tv_and_play(client, auth_manager, tv_manager)

        if format == "html":
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)

        return {"status": "wake_and_play"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wake/Play error: {str(e)}") from e


@router.post("/play-playlist/{playlist_uri}")
async def play_playlist(
    playlist_uri: str,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
):
    """Start playing a playlist (from URL path).

    Args:
        playlist_uri: Spotify playlist URI
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection

    Returns:
        JSON with status
    """
    try:
        await spotify_service.play_playlist(client, playlist_uri, auth_manager)
        return {"status": "playing_playlist", "playlist_uri": playlist_uri}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Play playlist error: {str(e)}") from e


@router.post("/play-playlist-from-form")
async def play_playlist_from_form(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
):
    """Start playing a playlist (from form data) and return updated tile HTML.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection

    Returns:
        HTML tile fragment (always HTML for form submissions)
    """
    try:
        # Get form data
        form = await request.form()
        playlist_uri_value = form.get("playlist")

        # Ensure it's a string
        if not playlist_uri_value or not isinstance(playlist_uri_value, str):
            raise HTTPException(status_code=400, detail="No playlist selected")

        # Start playing playlist
        await spotify_service.play_playlist(client, playlist_uri_value, auth_manager)

        # Return updated tile
        return await TemplateRenderer.render_spotify_tile(request, client, auth_manager)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Play playlist error: {str(e)}") from e


@router.get("/auth/status")
async def auth_status(
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
):
    """Check if Spotify is authenticated.

    Args:
        format: Response format - 'json' for API, 'html' for status message

    Returns:
        JSON with authentication status or HTML message
    """
    authenticated = spotify_service.is_authenticated()

    if format == "html":
        status_text = "✅ Authenticated" if authenticated else "❌ Not authenticated"
        return HTMLResponse(content=f"<div>{status_text}</div>")

    return {"authenticated": authenticated}


@router.get("/auth/login")
async def auth_login(settings: Settings = Depends(get_settings)):
    """Initiate Spotify OAuth flow."""
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = True

    # Build Spotify authorization URL
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "state": state,
        "scope": " ".join(SPOTIFY_SCOPES),
        "show_dialog": "false",
    }

    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
):
    """Handle Spotify OAuth callback."""
    # Check for errors
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth failed: {error}")

    # Verify state to prevent CSRF
    if not state or state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Clean up state
    _oauth_states.pop(state, None)

    # Verify we got an authorization code
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    try:
        # Exchange code for tokens
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        # Save refresh token
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=500, detail="No refresh token received")

        spotify_service._save_refresh_token(refresh_token)

        # Redirect back to dashboard homepage
        return RedirectResponse(url="/", status_code=303)

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}") from e
