import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # home-dashboard/


# Load playlists from JSON file
def load_playlists() -> list[dict]:
    with open(BASE_DIR / "playlists.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Settings(BaseSettings):
    api_host: str = ""
    api_port: int = 0

    tv_ip: str = ""
    tv_spotify_device_id: str = ""

    weather_api_key: str = ""
    weather_location: str = ""
    weather_latitude: float = 0.0
    weather_longitude: float = 0.0

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = ""
    spotify_refresh_token: str = ""

    spotify_favorite_playlists: list[dict] = load_playlists()

    ifttt_webhook_key: str = ""
    ifttt_event_name: str = ""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()  # pyright: ignore[reportCallIssue]
