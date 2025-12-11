"""Tests for custom exception classes."""

from home_dashboard.exceptions import (
    ConfigurationException,
    DashboardException,
    ErrorCode,
    PhoneException,
    SpotifyException,
    TVException,
    WeatherException,
)


class TestErrorCodes:
    """Tests for ErrorCode enum."""

    def test_error_code_values(self):
        """Test that error codes have correct values."""
        assert ErrorCode.DASHBOARD_ERROR == "DASHBOARD_ERROR"
        assert ErrorCode.SPOTIFY_ERROR == "SPOTIFY_ERROR"
        assert ErrorCode.TV_ERROR == "TV_ERROR"
        assert ErrorCode.WEATHER_ERROR == "WEATHER_ERROR"
        assert ErrorCode.PHONE_ERROR == "PHONE_ERROR"


class TestDashboardException:
    """Tests for DashboardException."""

    def test_dashboard_exception_basic(self):
        """Test creating basic dashboard exception."""
        exc = DashboardException(message="Test error")

        assert exc.message == "Test error"
        assert exc.code == ErrorCode.DASHBOARD_ERROR
        assert exc.status_code == 500
        assert exc.details == {}
        assert str(exc) == "Test error"

    def test_dashboard_exception_with_details(self):
        """Test dashboard exception with details."""
        exc = DashboardException(
            message="Test error", code=ErrorCode.INTERNAL_ERROR, status_code=503, details={"key": "value", "count": 42}
        )

        assert exc.message == "Test error"
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 503
        assert exc.details["key"] == "value"
        assert exc.details["count"] == 42


class TestSpotifyException:
    """Tests for SpotifyException."""

    def test_spotify_exception_defaults(self):
        """Test Spotify exception with defaults."""
        exc = SpotifyException(message="Spotify error")

        assert exc.message == "Spotify error"
        assert exc.code == ErrorCode.SPOTIFY_ERROR
        assert exc.status_code == 500

    def test_spotify_auth_error(self):
        """Test Spotify auth error."""
        exc = SpotifyException(message="Authentication failed", code=ErrorCode.SPOTIFY_AUTH_ERROR, status_code=401)

        assert exc.code == ErrorCode.SPOTIFY_AUTH_ERROR
        assert exc.status_code == 401

    def test_spotify_rate_limit_error(self):
        """Test Spotify rate limit error."""
        exc = SpotifyException(
            message="Rate limit exceeded",
            code=ErrorCode.SPOTIFY_RATE_LIMIT,
            status_code=429,
            details={"retry_after": 60},
        )

        assert exc.code == ErrorCode.SPOTIFY_RATE_LIMIT
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60


class TestTVException:
    """Tests for TVException."""

    def test_tv_exception_defaults(self):
        """Test TV exception with defaults."""
        exc = TVException(message="TV error")

        assert exc.message == "TV error"
        assert exc.code == ErrorCode.TV_ERROR
        assert exc.status_code == 500

    def test_tv_connection_error(self):
        """Test TV connection error."""
        exc = TVException(message="Cannot connect to TV", code=ErrorCode.TV_CONNECTION_ERROR, status_code=503)

        assert exc.code == ErrorCode.TV_CONNECTION_ERROR
        assert exc.status_code == 503

    def test_tv_timeout_error(self):
        """Test TV timeout error."""
        exc = TVException(
            message="TV did not respond", code=ErrorCode.TV_TIMEOUT, status_code=504, details={"timeout_seconds": 5}
        )

        assert exc.code == ErrorCode.TV_TIMEOUT
        assert exc.status_code == 504
        assert exc.details["timeout_seconds"] == 5


class TestWeatherException:
    """Tests for WeatherException."""

    def test_weather_exception_defaults(self):
        """Test Weather exception with defaults."""
        exc = WeatherException(message="Weather API error")

        assert exc.message == "Weather API error"
        assert exc.code == ErrorCode.WEATHER_ERROR
        assert exc.status_code == 500

    def test_weather_api_error(self):
        """Test Weather API error."""
        exc = WeatherException(message="API request failed", code=ErrorCode.WEATHER_API_ERROR, status_code=503)

        assert exc.code == ErrorCode.WEATHER_API_ERROR
        assert exc.status_code == 503


class TestPhoneException:
    """Tests for PhoneException."""

    def test_phone_exception_defaults(self):
        """Test Phone exception with defaults."""
        exc = PhoneException(message="Phone error")

        assert exc.message == "Phone error"
        assert exc.code == ErrorCode.PHONE_ERROR
        assert exc.status_code == 500

    def test_ifttt_error(self):
        """Test IFTTT webhook error."""
        exc = PhoneException(message="IFTTT webhook failed", code=ErrorCode.IFTTT_ERROR, status_code=503)

        assert exc.code == ErrorCode.IFTTT_ERROR
        assert exc.status_code == 503


class TestConfigurationException:
    """Tests for ConfigurationException."""

    def test_config_exception_defaults(self):
        """Test Configuration exception with defaults."""
        exc = ConfigurationException(message="Config error")

        assert exc.message == "Config error"
        assert exc.code == ErrorCode.CONFIG_ERROR
        assert exc.status_code == 500

    def test_config_missing_error(self):
        """Test missing configuration error."""
        exc = ConfigurationException(
            message="Required config missing",
            code=ErrorCode.CONFIG_MISSING,
            status_code=500,
            details={"missing_key": "API_KEY"},
        )

        assert exc.code == ErrorCode.CONFIG_MISSING
        assert exc.details["missing_key"] == "API_KEY"

    def test_config_invalid_error(self):
        """Test invalid configuration error."""
        exc = ConfigurationException(message="Invalid config value", code=ErrorCode.CONFIG_INVALID, status_code=500)

        assert exc.code == ErrorCode.CONFIG_INVALID
