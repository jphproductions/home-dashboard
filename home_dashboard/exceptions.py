"""Custom exceptions for Home Dashboard with proper HTTP status codes."""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes for structured error responses."""

    # Generic errors
    DASHBOARD_ERROR = "DASHBOARD_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Spotify errors
    SPOTIFY_ERROR = "SPOTIFY_ERROR"
    SPOTIFY_AUTH_ERROR = "SPOTIFY_AUTH_ERROR"
    SPOTIFY_NOT_AUTHENTICATED = "SPOTIFY_NOT_AUTHENTICATED"
    SPOTIFY_API_ERROR = "SPOTIFY_API_ERROR"
    SPOTIFY_RATE_LIMIT = "SPOTIFY_RATE_LIMIT"

    # TV errors
    TV_ERROR = "TV_ERROR"
    TV_CONNECTION_ERROR = "TV_CONNECTION_ERROR"
    TV_TIMEOUT = "TV_TIMEOUT"

    # Weather errors
    WEATHER_ERROR = "WEATHER_ERROR"
    WEATHER_API_ERROR = "WEATHER_API_ERROR"
    WEATHER_INVALID_LOCATION = "WEATHER_INVALID_LOCATION"

    # Phone/IFTTT errors
    PHONE_ERROR = "PHONE_ERROR"
    IFTTT_ERROR = "IFTTT_ERROR"

    # Configuration errors
    CONFIG_ERROR = "CONFIG_ERROR"
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"


class DashboardException(Exception):
    """Base exception for dashboard errors with HTTP status code support.

    All custom exceptions should inherit from this class to ensure
    consistent error handling across the application.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DASHBOARD_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        """Initialize dashboard exception.

        Args:
            message: Human-readable error message
            code: Error code from ErrorCode enum
            status_code: HTTP status code (default 500)
            details: Additional error context/details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class SpotifyException(DashboardException):
    """Spotify-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.SPOTIFY_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, status_code, details)


class SpotifyAuthException(SpotifyException):
    """Spotify authentication failed."""

    def __init__(self, message: str = "Spotify authentication failed", details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code=ErrorCode.SPOTIFY_AUTH_ERROR,
            status_code=401,
            details=details,
        )


class SpotifyNotAuthenticatedException(SpotifyException):
    """User not authenticated with Spotify."""

    def __init__(self, message: str = "Not authenticated with Spotify", details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code=ErrorCode.SPOTIFY_NOT_AUTHENTICATED,
            status_code=401,
            details=details,
        )


class SpotifyAPIException(SpotifyException):
    """Spotify API request failed."""

    def __init__(self, message: str, status_code: int = 502, details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code=ErrorCode.SPOTIFY_API_ERROR,
            status_code=status_code,
            details=details,
        )


class TVException(DashboardException):
    """TV control errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.TV_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, status_code, details)


class TVConnectionException(TVException):
    """TV connection failed."""

    def __init__(self, message: str = "Failed to connect to TV", details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code=ErrorCode.TV_CONNECTION_ERROR,
            status_code=503,
            details=details,
        )


class WeatherException(DashboardException):
    """Weather service errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.WEATHER_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, status_code, details)


class WeatherAPIException(WeatherException):
    """Weather API request failed."""

    def __init__(self, message: str, status_code: int = 502, details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code=ErrorCode.WEATHER_API_ERROR,
            status_code=status_code,
            details=details,
        )


class PhoneException(DashboardException):
    """Phone/IFTTT errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.PHONE_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, status_code, details)


class IFTTTException(PhoneException):
    """IFTTT webhook request failed."""

    def __init__(self, message: str = "IFTTT webhook failed", details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code=ErrorCode.IFTTT_ERROR,
            status_code=502,
            details=details,
        )


class ConfigurationException(DashboardException):
    """Configuration errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFIG_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, status_code, details)
