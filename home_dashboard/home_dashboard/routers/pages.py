"""Page rendering routes for HTML UI."""

from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

from home_dashboard.services import spotify_service
from home_dashboard.config import settings
from home_dashboard.dependencies import get_http_client

router = APIRouter()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_wind_direction_compass(degrees: int) -> str:
    """Convert wind direction degrees to compass arrow."""
    directions = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    idx = round(degrees / 45) % 8
    return directions[idx]


def get_weather_emoji(condition: str) -> str:
    """Get emoji for weather condition."""
    condition_lower = condition.lower()
    if "clear" in condition_lower:
        return "☀️"
    elif "cloud" in condition_lower:
        return "☁️"
    elif "rain" in condition_lower or "drizzle" in condition_lower:
        return "🌧️"
    elif "thunder" in condition_lower or "storm" in condition_lower:
        return "⛈️"
    elif "snow" in condition_lower:
        return "❄️"
    elif "mist" in condition_lower or "fog" in condition_lower:
        return "🌫️"
    else:
        return "🌤️"


def get_beaufort_scale(wind_speed_ms: float) -> tuple[int, str]:
    """Convert wind speed in m/s to Beaufort scale."""
    if wind_speed_ms < 0.5:
        return (0, "Calm")
    elif wind_speed_ms < 1.6:
        return (1, "Light air")
    elif wind_speed_ms < 3.4:
        return (2, "Light breeze")
    elif wind_speed_ms < 5.5:
        return (3, "Gentle breeze")
    elif wind_speed_ms < 8.0:
        return (4, "Moderate breeze")
    elif wind_speed_ms < 10.8:
        return (5, "Fresh breeze")
    elif wind_speed_ms < 13.9:
        return (6, "Strong breeze")
    elif wind_speed_ms < 17.2:
        return (7, "Near gale")
    elif wind_speed_ms < 20.8:
        return (8, "Gale")
    elif wind_speed_ms < 24.5:
        return (9, "Strong gale")
    elif wind_speed_ms < 28.5:
        return (10, "Storm")
    elif wind_speed_ms < 32.7:
        return (11, "Violent storm")
    else:
        return (12, "Hurricane")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/tiles/spotify", response_class=HTMLResponse)
async def spotify_tile(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Render Spotify tile fragment."""
    # Check authentication
    authenticated = spotify_service.is_authenticated()
    
    if not authenticated:
        return templates.TemplateResponse(
            "tiles/spotify.html",
            {
                "request": request,
                "authenticated": False,
            }
        )
    
    # Get current track status
    try:
        track_data = await spotify_service.get_current_track(client)
    except Exception:
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
        }
    )


@router.get("/tiles/weather", response_class=HTMLResponse)
async def weather_tile(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Render Weather tile fragment."""
    try:
        # Import here to avoid circular dependency
        from home_dashboard.services import weather_service
        
        weather = await weather_service.get_current_weather(client)
        beaufort, beaufort_desc = get_beaufort_scale(weather.wind_speed)
        
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
                "wind_direction": get_wind_direction_compass(weather.wind_deg),
                "beaufort": beaufort,
                "beaufort_description": beaufort_desc,
                "weather_emoji": get_weather_emoji(weather.condition),
                "recommendation": weather.recommendation,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "tiles/weather.html",
            {
                "request": request,
                "error": str(e),
            }
        )


@router.get("/tiles/phone", response_class=HTMLResponse)
async def phone_tile(request: Request):
    """Render Phone tile fragment."""
    return templates.TemplateResponse(
        "tiles/phone.html",
        {
            "request": request,
            "success": False,
            "error": None,
        }
    )


@router.get("/tiles/quick-actions", response_class=HTMLResponse)
async def quick_actions_tile(request: Request):
    """Render Quick Actions tile fragment."""
    return templates.TemplateResponse(
        "tiles/quick_actions.html",
        {
            "request": request,
        }
    )


@router.get("/tiles/status", response_class=HTMLResponse)
async def status_tile(request: Request):
    """Render Status tile fragment."""
    return templates.TemplateResponse(
        "tiles/status.html",
        {
            "request": request,
            "last_updated": datetime.now().strftime("%H:%M:%S"),
        }
    )
