"""Configuration for UI app."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Streamlit Configuration
STREAMLIT_THEME = "dark"
REFRESH_INTERVAL = 10  # seconds