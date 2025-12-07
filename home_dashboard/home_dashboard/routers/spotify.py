"""Spotify API routes."""

import asyncio
import httpx
import secrets
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from home_dashboard.dependencies import get_http_client
from home_dashboard.services import spotify_service
from home_dashboard.config import settings
from home_dashboard.models.spotify import SpotifyStatus

router = APIRouter()

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


@router.get("/status", response_model=SpotifyStatus)
async def get_spotify_status(client: httpx.AsyncClient = Depends(get_http_client)):
    """Get current Spotify playback status."""
    try:
        status = await spotify_service.get_current_track(client)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/play")
async def play(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Resume playback and return updated tile HTML."""
    from home_dashboard.routers.pages import spotify_tile

    try:
        await spotify_service.play(client)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state
        return await spotify_tile(request, client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/pause")
async def pause(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Pause playback and return updated tile HTML."""
    from home_dashboard.routers.pages import spotify_tile

    try:
        await spotify_service.pause(client)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state
        return await spotify_tile(request, client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/next")
async def next_track(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Skip to next track and return updated tile HTML."""
    from home_dashboard.routers.pages import spotify_tile

    try:
        await spotify_service.next_track(client)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state
        return await spotify_tile(request, client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/previous")
async def previous_track(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Go to previous track and return updated tile HTML."""
    from home_dashboard.routers.pages import spotify_tile

    try:
        await spotify_service.previous_track(client)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state
        return await spotify_tile(request, client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/wake-and-play")
async def wake_tv_and_play(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Wake TV and transfer current playback, return updated tile HTML."""
    from home_dashboard.routers.pages import spotify_tile

    try:
        await spotify_service.wake_tv_and_play(client)
        return await spotify_tile(request, client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wake/Play error: {str(e)}") from e


@router.get("/playlists/favorites")
async def get_favorite_playlists():
    """Get hardcoded favorite playlists from config (10 playlists)."""
    return {"playlists": settings.spotify_favorite_playlists}


@router.get("/playlists")
async def get_playlists():
    """Get hardcoded favorite playlists from config."""
    return {"playlists": config.spotify_favorite_playlists}


@router.post("/play-playlist/{playlist_uri}")
async def play_playlist(playlist_uri: str, client: httpx.AsyncClient = Depends(get_http_client)):
    """Start playing a playlist (from URL path)."""
    try:
        await spotify_service.play_playlist(client, playlist_uri)
        return {"status": "playing_playlist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Play playlist error: {str(e)}") from e


@router.post("/play-playlist-from-form")
async def play_playlist_from_form(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Start playing a playlist (from form data) and return updated tile HTML."""
    from home_dashboard.routers.pages import spotify_tile

    try:
        # Get form data
        form = await request.form()
        playlist_uri_value = form.get("playlist")

        # Ensure it's a string
        if not playlist_uri_value or not isinstance(playlist_uri_value, str):
            raise HTTPException(status_code=400, detail="No playlist selected")

        # Start playing playlist
        await spotify_service.play_playlist(client, playlist_uri_value)

        # Return updated tile
        return await spotify_tile(request, client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Play playlist error: {str(e)}") from e


@router.get("/auth/status")
async def auth_status():
    """Check if Spotify is authenticated."""
    return {"authenticated": spotify_service.is_authenticated()}


@router.get("/auth/login")
async def auth_login():
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
