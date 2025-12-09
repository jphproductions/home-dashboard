"""Custom exceptions for Home Dashboard."""


class DashboardException(Exception):
    """Base exception for dashboard errors."""

    def __init__(self, message: str, code: str = "DASHBOARD_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class SpotifyException(DashboardException):
    """Spotify-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "SPOTIFY_ERROR")


class SpotifyAuthException(SpotifyException):
    """Spotify authentication failed."""

    def __init__(self, message: str = "Spotify authentication failed"):
        super().__init__(message)
        self.code = "SPOTIFY_AUTH_ERROR"


class TVException(DashboardException):
    """TV control errors."""

    def __init__(self, message: str):
        super().__init__(message, "TV_ERROR")


class WeatherException(DashboardException):
    """Weather service errors."""

    def __init__(self, message: str):
        super().__init__(message, "WEATHER_ERROR")


class PhoneException(DashboardException):
    """Phone/IFTTT errors."""

    def __init__(self, message: str):
        super().__init__(message, "PHONE_ERROR")


class ConfigurationException(DashboardException):
    """Configuration errors."""

    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")
