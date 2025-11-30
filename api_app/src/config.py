from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # TV
    tv_ip: str
    tv_spotify_device_id: str

    # Weather
    weather_api_key: str
    weather_location: str = "Den Bosch"
    weather_latitude: float = 51.5
    weather_longitude: float = 5.3

    # Spotify
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8501/callback"
    spotify_refresh_token: str = ""

    # IFTTT
    ifttt_webhook_key: str
    ifttt_event_name: str = "ring_jamie_phone"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()