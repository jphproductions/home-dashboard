"""Spotify API routes with support for JSON and HTML responses."""

import asyncio
import secrets
import time
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from home_dashboard.config import Settings, get_settings
from home_dashboard.dependencies import get_http_client, get_spotify_auth_manager, get_tv_state_manager
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.protocols import TVServiceProtocol
from home_dashboard.security import verify_api_key
from home_dashboard.services import spotify_service, tv_tizen_service
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager
from home_dashboard.utils.env_updater import get_env_path, update_env_file
from home_dashboard.views.template_renderer import TemplateRenderer

# Note: OAuth endpoints (/auth/login, /auth/callback) are excluded from API key requirement
# All other endpoints require API key via Depends(verify_api_key) on each route
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)

# OAuth state storage with TTL cleanup
# States expire after 10 minutes to prevent memory leaks from abandoned auth flows
# In production with multiple instances, use Redis or database
_oauth_states: dict[str, float] = {}  # state -> timestamp
OAUTH_STATE_TTL_SECONDS = 600  # 10 minutes


def get_tv_service() -> TVServiceProtocol:
    """Dependency to provide TV service implementation.

    Returns:
        TV service implementation (tv_tizen_service module)
    """
    return tv_tizen_service


def _cleanup_expired_oauth_states() -> None:
    """Remove expired OAuth states to prevent memory leaks."""
    current_time = time.time()
    expired_states = [
        state for state, timestamp in _oauth_states.items() if current_time - timestamp > OAUTH_STATE_TTL_SECONDS
    ]
    for state in expired_states:
        _oauth_states.pop(state, None)


# Spotify OAuth scopes needed for playback control
SPOTIFY_SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "user-read-recently-played",
]


@router.get(
    "/status",
    summary="Get Spotify playback status",
    description="""
    Retrieves the current playback status from Spotify.

    Returns track information, playback state, and device name.
    Cached for 5 seconds to reduce API calls.

    **Note:** Requires Spotify authentication. Visit `/api/spotify/auth/login` first if not authenticated.
    """,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "is_playing": True,
                        "track_name": "Bohemian Rhapsody",
                        "artist_name": "Queen",
                        "device_name": "Living Room TV",
                        "progress_ms": 125000,
                        "duration_ms": 354000,
                    }
                }
            },
        },
        401: {"description": "Not authenticated - visit /api/spotify/auth/login"},
        500: {"description": "Spotify API error"},
    },
)
@limiter.limit("60/minute")
async def get_spotify_status(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
    _api_key: str = Depends(verify_api_key),
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
            return await TemplateRenderer.render_spotify_tile(request, client, auth_manager, settings)

        # JSON response
        status = await spotify_service.get_current_track(client, auth_manager, settings)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post(
    "/play",
    summary="Resume Spotify playback",
    description="""
    Resume playback on the active Spotify device.

    If no device is active, you may need to start playback manually first.

    **Rate Limited:** 30 requests/minute
    """,
    responses={
        200: {
            "description": "Playback resumed successfully",
            "content": {"application/json": {"example": {"status": "playing"}}},
        },
        401: {"description": "Not authenticated"},
        500: {"description": "Spotify API error (no active device, etc.)"},
    },
)
@limiter.limit("30/minute")
async def play(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    _api_key: str = Depends(verify_api_key),
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
        await spotify_service.play(client, auth_manager, settings)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_playback_status(request, client, auth_manager, settings)

        return {"status": "playing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post(
    "/pause",
    summary="Pause Spotify playback",
    description="Pause playback on the active Spotify device.",
    responses={
        200: {
            "description": "Playback paused successfully",
            "content": {"application/json": {"example": {"status": "paused"}}},
        },
        401: {"description": "Not authenticated"},
        500: {"description": "Spotify API error"},
    },
)
async def pause(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    _api_key: str = Depends(verify_api_key),
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
        await spotify_service.pause(client, auth_manager, settings)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_playback_status(request, client, auth_manager, settings)

        return {"status": "paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/next")
async def next_track(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    _api_key: str = Depends(verify_api_key),
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
        await spotify_service.next_track(client, auth_manager, settings)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_playback_status(request, client, auth_manager, settings)

        return {"status": "next_track"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/previous")
async def previous_track(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    _api_key: str = Depends(verify_api_key),
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
        await spotify_service.previous_track(client, auth_manager, settings)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_playback_status(request, client, auth_manager, settings)

        return {"status": "previous_track"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/wake-and-play")
async def wake_tv_and_play(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    tv_service: TVServiceProtocol = Depends(get_tv_service),
    tv_manager: TVStateManager = Depends(get_tv_state_manager),
    settings: Settings = Depends(get_settings),
    format: Literal["json", "html"] = Query(default="html", description="Response format"),
    _api_key: str = Depends(verify_api_key),
):
    """Wake TV and transfer Spotify playback to TV.

    Args:
        request: FastAPI request object
        client: HTTP client from dependency injection
        auth_manager: Spotify auth manager from dependency injection
        tv_service: TV service from dependency injection
        tv_manager: TV state manager from dependency injection
        format: Response format - 'json' for API, 'html' for HTMX

    Returns:
        JSON with status or HTML tile fragment
    """
    try:
        await spotify_service.wake_tv_and_play(client, auth_manager, tv_service, tv_manager, settings)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        if format == "html":
            return await TemplateRenderer.render_spotify_playback_status(request, client, auth_manager, settings)

        return {"status": "wake_and_play"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wake/Play error: {str(e)}") from e


@router.post("/play-playlist/{playlist_uri}")
async def play_playlist(
    playlist_uri: str,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    _api_key: str = Depends(verify_api_key),
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
    settings: Settings = Depends(get_settings),
    _api_key: str = Depends(verify_api_key),
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
        await spotify_service.play_playlist(client, playlist_uri_value, auth_manager, settings)
        await asyncio.sleep(0.5)  # Wait for Spotify API to update state

        # Return updated playback status fragment
        return await TemplateRenderer.render_spotify_playback_status(request, client, auth_manager, settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Play playlist error: {str(e)}") from e


@router.get("/auth/status")
async def auth_status(
    format: Literal["json", "html"] = Query(default="json", description="Response format"),
    _api_key: str = Depends(verify_api_key),
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
    # Clean up expired states before adding new one
    _cleanup_expired_oauth_states()

    # Generate random state for CSRF protection with timestamp
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time()

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

        # Get refresh token
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=500, detail="No refresh token received")

        # Auto-save refresh token to .env
        save_success = False
        save_error = ""
        try:
            env_path = get_env_path()
            update_env_file(env_path, "SPOTIFY_REFRESH_TOKEN", refresh_token)
            save_success = True

            log_with_context(
                logger,
                "info",
                "Spotify refresh token saved to .env",
                event_type="spotify_auth_success",
            )

        except Exception as e:
            save_error = str(e)
            log_with_context(
                logger,
                "error",
                "Failed to save refresh token to .env",
                event_type="env_update_failed",
                error=save_error,
            )

        # Display appropriate success message
        if save_success:
            html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spotify Authentication Successful</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 700px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }
                h1 {
                    color: #1DB954;
                    margin-bottom: 20px;
                }
                .success-icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
                .info-box {
                    background-color: #d1ecf1;
                    padding: 20px;
                    border-radius: 4px;
                    border-left: 4px solid #0c5460;
                    margin: 20px 0;
                    text-align: left;
                }
                .info-box strong {
                    display: block;
                    margin-bottom: 10px;
                    color: #0c5460;
                }
                .button {
                    background-color: #1DB954;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                    text-decoration: none;
                    display: inline-block;
                }
                .button:hover {
                    background-color: #1ed760;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Authentication Complete!</h1>

                <div class="info-box">
                    <strong>✨ Token automatically saved to .env</strong>
                    <p>Your Spotify refresh token has been securely saved to your <code>.env</code> file.</p>
                    <p><strong>Next step:</strong> Please restart the dashboard application for the changes to take effect.</p>
                </div>

                <a href="/" class="button">← Return to Dashboard</a>

                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    After restarting, you'll be able to control Spotify playback from the dashboard.
                </p>
            </div>
        </body>
        </html>
        """
        else:
            # Fallback to manual save if auto-save failed
            html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spotify Authentication - Manual Save Required</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #ff9800;
                }}
                .token-box {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    border-radius: 4px;
                    font-family: monospace;
                    word-break: break-all;
                    margin: 20px 0;
                    border: 1px solid #ddd;
                }}
                .instructions {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 4px;
                    border-left: 4px solid #ffc107;
                    margin: 20px 0;
                }}
                .error-info {{
                    background-color: #f8d7da;
                    padding: 15px;
                    border-radius: 4px;
                    border-left: 4px solid #dc3545;
                    margin: 20px 0;
                    color: #721c24;
                }}
                button {{
                    background-color: #1DB954;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 10px;
                }}
                button:hover {{
                    background-color: #1ed760;
                }}
                a {{
                    color: #1DB954;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ Authentication Successful - Manual Save Required</h1>

                <div class="error-info">
                    <strong>Auto-save failed:</strong> {save_error}
                </div>

                <div class="instructions">
                    <strong>Please manually save your token:</strong>
                    <ol>
                        <li>Copy the refresh token below</li>
                        <li>Open your <code>.env</code> file</li>
                        <li>Set <code>SPOTIFY_REFRESH_TOKEN=your_token_here</code></li>
                        <li>Restart the dashboard application</li>
                    </ol>
                </div>

                <h3>Your Refresh Token:</h3>
                <div class="token-box" id="token">{refresh_token}</div>

                <button onclick="copyToken()">📋 Copy Token to Clipboard</button>
                <span id="copyStatus" style="margin-left: 10px; color: #1DB954;"></span>

                <p style="margin-top: 30px;">
                    <a href="/">← Return to Dashboard</a>
                </p>
            </div>

            <script>
                function copyToken() {{
                    const token = document.getElementById('token').textContent;
                    navigator.clipboard.writeText(token).then(function() {{
                        document.getElementById('copyStatus').textContent = '✓ Copied!';
                        setTimeout(function() {{
                            document.getElementById('copyStatus').textContent = '';
                        }}, 2000);
                    }}, function(err) {{
                        document.getElementById('copyStatus').textContent = '✗ Copy failed';
                        document.getElementById('copyStatus').style.color = 'red';
                    }});
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}") from e
