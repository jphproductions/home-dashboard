"""Home Dashboard models"""

from home_dashboard.models.base_models import ErrorResponse, HealthResponse
from home_dashboard.models.phone import PhoneRingRequest
from home_dashboard.models.spotify import SpotifyPlayRequest, SpotifyStatus
from home_dashboard.models.weather import CurrentWeather, WeatherResponse

__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "CurrentWeather",
    "WeatherResponse",
    "PhoneRingRequest",
    "SpotifyStatus",
    "SpotifyPlayRequest",
]
