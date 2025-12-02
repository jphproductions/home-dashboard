"""Home Dashboard shared models"""

from shared.models.base_models import ErrorResponse, HealthResponse
from shared.models.phone import PhoneRingRequest
from shared.models.spotify import SpotifyPlayRequest, SpotifyStatus
from shared.models.weather import CurrentWeather, WeatherResponse

__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "CurrentWeather",
    "WeatherResponse",
    "PhoneRingRequest",
    "SpotifyStatus",
    "SpotifyPlayRequest",
]

__version__ = "0.1.0"
