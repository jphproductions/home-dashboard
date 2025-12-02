from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]  # home-dashboard/


class UISettings(BaseSettings):
    api_base_url: str = "http://127.0.0.1:8000"
    streamlit_host: str = "127.0.0.1"
    streamlit_port: int = 8501
    refresh_interval: int = 10

    class Config:
        env_file = BASE_DIR / ".env"
        case_sensitive = False
        extra = "ignore"


ui_settings = UISettings()
