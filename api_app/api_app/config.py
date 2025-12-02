from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # home-dashboard/


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    tv_ip: str = ""
    tv_spotify_device_id: str = ""

    weather_api_key: str = ""
    weather_location: str = "Den Bosch"
    weather_latitude: float = 51.6978
    weather_longitude: float = 5.3048

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8501/callback"
    spotify_refresh_token: str = ""

    ifttt_webhook_key: str = ""
    ifttt_event_name: str = "ring_jamie_phone"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()  # pyright: ignore[reportCallIssue]
