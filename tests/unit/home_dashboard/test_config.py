"""Unit tests for configuration."""

from unittest.mock import mock_open, patch

import pytest

from home_dashboard.config import Settings, get_settings


def test_settings_defaults():
    """Test Settings model has correct defaults."""
    # Create minimal settings
    settings = Settings(
        tv_ip="192.168.1.100",
        tv_spotify_device_id="test-device",
        weather_api_key="test-key",
        weather_latitude=40.7128,
        weather_longitude=-74.0060,
        spotify_client_id="test-client-id",
        spotify_client_secret="test-secret",
        spotify_redirect_uri="http://localhost:8000/callback",
        spotify_refresh_token="test-refresh",
        ifttt_webhook_key="test-webhook",
        ifttt_event_name="test-event",
    )

    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.tv_ip == "192.168.1.100"


def test_settings_validation_valid_ip():
    """Test IP address validation accepts valid IPs."""
    settings = Settings(
        tv_ip="10.0.0.1",
        tv_spotify_device_id="test",
        weather_api_key="key",
        weather_latitude=0.0,
        weather_longitude=0.0,
        spotify_client_id="id",
        spotify_client_secret="secret",
        spotify_redirect_uri="http://localhost",
        spotify_refresh_token="token",
        ifttt_webhook_key="key",
        ifttt_event_name="event",
    )

    assert str(settings.tv_ip) == "10.0.0.1"


def test_settings_validation_invalid_ip():
    """Test IP address validation rejects invalid IPs."""
    with pytest.raises(ValueError):
        Settings(
            tv_ip="999.999.999.999",
            tv_spotify_device_id="test",
            weather_api_key="key",
            weather_latitude=0.0,
            weather_longitude=0.0,
            spotify_client_id="id",
            spotify_client_secret="secret",
            spotify_redirect_uri="http://localhost",
            spotify_refresh_token="token",
            ifttt_webhook_key="key",
            ifttt_event_name="event",
        )


def test_settings_env_file_loading():
    """Test settings can load from environment."""
    with patch.dict(
        "os.environ",
        {
            "TV_IP": "192.168.1.50",
            "API_PORT": "9000",
            "TV_SPOTIFY_DEVICE_ID": "env-device",
            "WEATHER_API_KEY": "env-key",
            "WEATHER_LATITUDE": "51.5074",
            "WEATHER_LONGITUDE": "-0.1278",
            "SPOTIFY_CLIENT_ID": "env-client",
            "SPOTIFY_CLIENT_SECRET": "env-secret",
            "SPOTIFY_REDIRECT_URI": "http://test",
            "SPOTIFY_REFRESH_TOKEN": "env-token",
            "IFTTT_WEBHOOK_KEY": "env-webhook",
            "IFTTT_EVENT_NAME": "env-event",
        },
    ):
        settings = Settings()

        assert settings.api_port == 9000
        assert str(settings.tv_ip) == "192.168.1.50"
        assert settings.tv_spotify_device_id == "env-device"


def test_get_settings_singleton():
    """Test get_settings returns singleton instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_spotify_favorite_playlists_valid_file():
    """Test loading playlists from valid JSON file."""
    mock_json = '{"favorites": [{"name": "Test", "uri": "spotify:playlist:123"}]}'

    settings = Settings(
        tv_ip="192.168.1.100",
        tv_spotify_device_id="test",
        weather_api_key="key",
        weather_latitude=0.0,
        weather_longitude=0.0,
        spotify_client_id="id",
        spotify_client_secret="secret",
        spotify_redirect_uri="http://localhost",
        spotify_refresh_token="token",
        ifttt_webhook_key="key",
        ifttt_event_name="event",
    )

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_json)):
            playlists = settings.spotify_favorite_playlists

            assert len(playlists) == 1
            assert playlists[0]["name"] == "Test"
            assert playlists[0]["uri"] == "spotify:playlist:123"


def test_spotify_favorite_playlists_file_not_found():
    """Test playlists returns empty list when file doesn't exist."""
    settings = Settings(
        tv_ip="192.168.1.100",
        tv_spotify_device_id="test",
        weather_api_key="key",
        weather_latitude=0.0,
        weather_longitude=0.0,
        spotify_client_id="id",
        spotify_client_secret="secret",
        spotify_redirect_uri="http://localhost",
        spotify_refresh_token="token",
        ifttt_webhook_key="key",
        ifttt_event_name="event",
    )

    with patch("pathlib.Path.exists", return_value=False):
        playlists = settings.spotify_favorite_playlists

        assert playlists == []


def test_spotify_favorite_playlists_invalid_json():
    """Test playlists handles invalid JSON gracefully."""
    settings = Settings(
        tv_ip="192.168.1.100",
        tv_spotify_device_id="test",
        weather_api_key="key",
        weather_latitude=0.0,
        weather_longitude=0.0,
        spotify_client_id="id",
        spotify_client_secret="secret",
        spotify_redirect_uri="http://localhost",
        spotify_refresh_token="token",
        ifttt_webhook_key="key",
        ifttt_event_name="event",
    )

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            playlists = settings.spotify_favorite_playlists

            assert playlists == []


def test_spotify_favorite_playlists_missing_favorites_key():
    """Test playlists handles missing 'favorites' key."""
    mock_json = '{"other_key": []}'

    settings = Settings(
        tv_ip="192.168.1.100",
        tv_spotify_device_id="test",
        weather_api_key="key",
        weather_latitude=0.0,
        weather_longitude=0.0,
        spotify_client_id="id",
        spotify_client_secret="secret",
        spotify_redirect_uri="http://localhost",
        spotify_refresh_token="token",
        ifttt_webhook_key="key",
        ifttt_event_name="event",
    )

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_json)):
            playlists = settings.spotify_favorite_playlists

            assert playlists == []
