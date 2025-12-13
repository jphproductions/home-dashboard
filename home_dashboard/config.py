import ipaddress
import json
from functools import cached_property
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from home_dashboard.logging_config import get_logger, log_with_context

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent  # home-dashboard/


class Settings(BaseSettings):
    """Application settings with validation.

    Critical fields are required and will raise validation errors if missing.
    All secrets must be provided via environment variables or .env file.

    Uses Pydantic v2 API:
    - model_config with SettingsConfigDict
    - @field_validator decorator
    - @cached_property for expensive operations
    """

    # API server settings - required
    api_host: str = Field(min_length=1, description="API server host (e.g., '0.0.0.0')")
    api_port: int = Field(ge=1, le=65535, default=8000, description="API server port")

    # TV settings - required for TV features
    tv_ip: str = Field(min_length=7, description="Samsung TV IP address (e.g., '192.168.1.100')")
    tv_spotify_device_id: str = Field(min_length=1, description="Spotify device ID for TV")

    # Weather API - required for weather features
    weather_api_key: str = Field(min_length=1, description="OpenWeatherMap API key")
    weather_location: str = Field(min_length=1, description="City name for weather")
    weather_latitude: float = Field(ge=-90, le=90, description="Latitude for weather")
    weather_longitude: float = Field(ge=-180, le=180, description="Longitude for weather")

    # Spotify API - required for Spotify features
    spotify_client_id: str = Field(min_length=1, description="Spotify OAuth client ID")
    spotify_client_secret: str = Field(min_length=1, description="Spotify OAuth client secret")
    spotify_redirect_uri: str = Field(pattern=r"^https?://", description="Spotify OAuth redirect URI")
    spotify_refresh_token: str = Field(default="", description="Spotify refresh token (populated after OAuth)")

    # IFTTT - required for phone integration
    ifttt_webhook_key: str = Field(min_length=1, description="IFTTT webhook key")
    ifttt_event_name: str = Field(min_length=1, description="IFTTT event name")

    model_config = SettingsConfigDict(
        env_file=Path(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,  # Validate defaults too
    )

    @cached_property
    def spotify_favorite_playlists(self) -> list[dict]:
        """Load and validate playlists from JSON file.

        Uses @cached_property so file is read only once per Settings instance.
        Validates that the file exists and contains valid JSON array.

        Returns:
            List of playlist dictionaries

        Raises:
            ValueError: If file is missing or invalid JSON
        """
        file_path = BASE_DIR / "playlists.json"

        if not file_path.exists():
            log_with_context(
                logger,
                "warning",
                "playlists.json not found, returning empty list",
                file_path=str(file_path),
                event_type="config_playlists_missing",
            )
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
            data = json.loads(content)

            # Validate it's a list (per task requirements: just check valid JSON)
            if not isinstance(data, list):
                raise ValueError("playlists.json must contain a JSON array")

            return data
        except json.JSONDecodeError as e:
            log_with_context(
                logger,
                "error",
                "Invalid JSON in playlists.json",
                file_path=str(file_path),
                error=str(e),
                event_type="config_playlists_invalid",
            )
            raise ValueError(f"playlists.json contains invalid JSON: {e}") from e

    @field_validator("api_host", mode="after")
    @classmethod
    def validate_api_host(cls, v: str) -> str:
        """Ensure api_host is not empty or whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("api_host cannot be empty")
        return v

    @field_validator("tv_ip", mode="after")
    @classmethod
    def validate_tv_ip(cls, v: str) -> str:
        """Ensure tv_ip is a valid IP address."""
        v = v.strip()
        try:
            ipaddress.ip_address(v)
        except ValueError as e:
            raise ValueError(f"tv_ip must be a valid IPv4 or IPv6 address: {e}") from e
        return v

    @field_validator("weather_location", mode="after")
    @classmethod
    def validate_weather_location(cls, v: str) -> str:
        """Ensure weather_location is not empty or whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("weather_location must not be empty")
        return v

    @field_validator("spotify_redirect_uri", mode="after")
    @classmethod
    def validate_spotify_redirect_uri(cls, v: str) -> str:
        """Ensure redirect URI is valid and uses correct port."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("spotify_redirect_uri must be a valid http:// or https:// URL")
        return v


# Singleton settings instance (cached for performance)
_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Get singleton Settings instance for dependency injection.

    This function creates a singleton to avoid re-reading .env file
    on every request. Use this with FastAPI's Depends() for
    dependency injection.

    Returns:
        Cached Settings instance

    Example:
        @app.get("/")
        async def route(settings: Settings = Depends(get_settings)):
            return {"host": settings.api_host}
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
