import json
import logging
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]  # home-dashboard/


class Settings(BaseSettings):
    """Application settings with validation.

    Critical fields are required and will raise validation errors if missing.
    All secrets must be provided via environment variables or .env file.
    """

    # API server settings - required
    api_host: str
    api_port: int = Field(gt=0, lt=65536)

    # TV settings - required for TV features
    tv_ip: str
    tv_spotify_device_id: str

    # Weather API - required for weather features
    weather_api_key: str
    weather_location: str
    weather_latitude: float = Field(ge=-90, le=90)
    weather_longitude: float = Field(ge=-180, le=180)

    # Spotify API - required for Spotify features
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    spotify_refresh_token: str = ""  # Optional - populated after OAuth flow

    # IFTTT - required for phone integration
    ifttt_webhook_key: str
    ifttt_event_name: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def spotify_favorite_playlists(self) -> list[dict]:
        """Load playlists from JSON file (lazy-loaded).

        This is a property to avoid loading during app startup and to handle
        missing file gracefully.
        """
        try:
            with open(BASE_DIR / "playlists.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("playlists.json not found, returning empty list")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse playlists.json: {e}")
            return []

    @field_validator("api_host")
    @classmethod
    def validate_api_host(cls, v: str) -> str:
        """Ensure api_host is not empty."""
        if not v or not v.strip():
            raise ValueError("api_host must be provided (e.g., '0.0.0.0' or 'localhost')")
        return v.strip()

    @field_validator("weather_location")
    @classmethod
    def validate_weather_location(cls, v: str) -> str:
        """Ensure weather_location is not empty."""
        if not v or not v.strip():
            raise ValueError("weather_location must be provided")
        return v.strip()

    @field_validator("spotify_redirect_uri")
    @classmethod
    def validate_spotify_redirect_uri(cls, v: str) -> str:
        """Ensure redirect URI is valid URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("spotify_redirect_uri must be a valid http:// or https:// URL")
        return v


# Global settings instance
settings = Settings()  # type: ignore[call-arg]
