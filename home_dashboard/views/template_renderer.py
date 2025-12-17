"""Template rendering utilities for HTML views."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from home_dashboard.config import Settings
from home_dashboard.logging_config import get_logger, log_with_context
from home_dashboard.services import spotify_service, weather_service

if TYPE_CHECKING:
    from home_dashboard.state_managers import SpotifyAuthManager


logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class TemplateRenderer:
    """Handles rendering of Jinja2 templates for all dashboard views."""

    @staticmethod
    def render_index(request: Request) -> HTMLResponse:
        """Render main dashboard page."""
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def render_spotify_tile(
        request: Request,
        client: httpx.AsyncClient,
        auth_manager: "SpotifyAuthManager",
        settings: Settings,
    ) -> HTMLResponse:
        """Render Spotify tile fragment.

        Args:
            request: FastAPI request object
            client: HTTP client for API calls
            auth_manager: Spotify authentication manager
            settings: Settings instance (must be provided by router via Depends)

        Returns:
            HTMLResponse with rendered Spotify tile
        """
        # Check authentication
        authenticated = spotify_service.is_authenticated(settings)

        if not authenticated:
            return templates.TemplateResponse(
                "tiles/spotify.html",
                {
                    "request": request,
                    "authenticated": False,
                },
            )

        # Get current track status
        try:
            track_data = await spotify_service.get_current_track(client, auth_manager, settings)
        except Exception as e:
            log_with_context(
                logger,
                "warning",
                "Failed to get current Spotify track",
                error=str(e),
                error_type=type(e).__name__,
                event_type="spotify_track_error",
            )
            track_data = None

        # Get playlists from config
        playlists = settings.spotify_favorite_playlists

        return templates.TemplateResponse(
            "tiles/spotify.html",
            {
                "request": request,
                "authenticated": True,
                "track_name": track_data.track_name if track_data else None,
                "artist_name": track_data.artist_name if track_data else None,
                "device_name": track_data.device_name if track_data else None,
                "is_playing": track_data.is_playing if track_data else False,
                "progress_ms": track_data.progress_ms if track_data else None,
                "duration_ms": track_data.duration_ms if track_data else None,
                "playlists": playlists,
            },
        )

    @staticmethod
    async def render_spotify_playback_status(
        request: Request,
        client: httpx.AsyncClient,
        auth_manager: "SpotifyAuthManager",
        settings: Settings,
    ) -> HTMLResponse:
        """Render just the Spotify playback status fragment for HTMX partial updates.

        Args:
            request: FastAPI request object
            client: HTTP client for API calls
            auth_manager: Spotify authentication manager
            settings: Settings instance

        Returns:
            HTMLResponse with rendered playback status fragment
        """
        # Get current track status
        try:
            track_data = await spotify_service.get_current_track(client, auth_manager, settings)
        except Exception as e:
            log_with_context(
                logger,
                "warning",
                "Failed to get current Spotify track",
                error=str(e),
                error_type=type(e).__name__,
                event_type="spotify_track_error",
            )
            track_data = None

        return templates.TemplateResponse(
            "tiles/spotify_playback_status.html",
            {
                "request": request,
                "track_name": track_data.track_name if track_data else None,
                "artist_name": track_data.artist_name if track_data else None,
                "device_name": track_data.device_name if track_data else None,
                "is_playing": track_data.is_playing if track_data else False,
            },
        )

    @staticmethod
    async def render_weather_tile(
        request: Request,
        client: httpx.AsyncClient,
        settings: Settings,
    ) -> HTMLResponse:
        """Render Weather tile fragment.

        Args:
            request: FastAPI request object
            client: HTTP client for API calls
            settings: Settings instance (must be provided by router via Depends)

        Returns:
            HTMLResponse with rendered weather tile
        """
        try:
            weather = await weather_service.get_current_weather(client, settings)

            return templates.TemplateResponse(
                "tiles/weather.html",
                {
                    "request": request,
                    "temp": weather.temp,
                    "feels_like": weather.feels_like,
                    "condition": weather.condition,
                    "location": weather.location,
                    "wind_speed": weather.wind_speed,
                    "wind_deg": weather.wind_deg,
                    "wind_direction": weather.wind_direction_compass,
                    "beaufort": weather.beaufort_scale,
                    "beaufort_description": weather.beaufort_description,
                    "icon_url": weather.icon_url,
                    "recommendation": weather.recommendation,
                    "error": None,
                },
            )
        except Exception as e:
            log_with_context(
                logger,
                "warning",
                "Failed to get weather data",
                error=str(e),
                error_type=type(e).__name__,
                event_type="weather_error",
            )
            return templates.TemplateResponse(
                "tiles/weather.html",
                {
                    "request": request,
                    "error": str(e),
                },
            )

    @staticmethod
    def render_phone_tile(request: Request) -> HTMLResponse:
        """Render Phone tile fragment.

        Args:
            request: FastAPI request object

        Returns:
            HTMLResponse with rendered phone tile
        """
        return templates.TemplateResponse(
            "tiles/phone.html",
            {
                "request": request,
                "success": False,
                "error": None,
            },
        )

    @staticmethod
    def render_quick_actions_tile(request: Request) -> HTMLResponse:
        """Render Quick Actions tile fragment.

        Args:
            request: FastAPI request object

        Returns:
            HTMLResponse with rendered quick actions tile
        """
        return templates.TemplateResponse(
            "tiles/quick_actions.html",
            {
                "request": request,
            },
        )

    @staticmethod
    def render_status_tile(request: Request) -> HTMLResponse:
        """Render Status tile fragment.

        Args:
            request: FastAPI request object

        Returns:
            HTMLResponse with rendered status tile
        """
        return templates.TemplateResponse(
            "tiles/status.html",
            {
                "request": request,
                "last_updated": datetime.now().strftime("%H:%M:%S"),
            },
        )
