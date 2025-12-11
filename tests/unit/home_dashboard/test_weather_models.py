"""Tests for weather models and their properties."""

from home_dashboard.models.weather import WeatherResponse


class TestWeatherResponse:
    """Tests for WeatherResponse model and its properties."""

    def test_weather_response_creation(self):
        """Test creating a WeatherResponse."""
        weather = WeatherResponse(
            temp=22.5,
            feels_like=20.0,
            condition="Clear sky",
            icon="01d",
            location="Amsterdam",
            recommendation="Perfect weather for a walk!",
            wind_speed=5.5,
            wind_deg=180,
        )

        assert weather.temp == 22.5
        assert weather.condition == "Clear sky"
        assert weather.location == "Amsterdam"

    def test_wind_direction_compass_north(self):
        """Test wind direction compass for North (0°)."""
        weather = WeatherResponse(
            temp=20.0,
            feels_like=18.0,
            condition="Clear",
            icon="01d",
            location="Test",
            recommendation="Good",
            wind_speed=5.0,
            wind_deg=0,
        )

        assert weather.wind_direction_compass == "↑"

    def test_wind_direction_compass_east(self):
        """Test wind direction compass for East (90°)."""
        weather = WeatherResponse(
            temp=20.0,
            feels_like=18.0,
            condition="Clear",
            icon="01d",
            location="Test",
            recommendation="Good",
            wind_speed=5.0,
            wind_deg=90,
        )

        assert weather.wind_direction_compass == "→"

    def test_wind_direction_compass_south(self):
        """Test wind direction compass for South (180°)."""
        weather = WeatherResponse(
            temp=20.0,
            feels_like=18.0,
            condition="Clear",
            icon="01d",
            location="Test",
            recommendation="Good",
            wind_speed=5.0,
            wind_deg=180,
        )

        assert weather.wind_direction_compass == "↓"

    def test_wind_direction_compass_west(self):
        """Test wind direction compass for West (270°)."""
        weather = WeatherResponse(
            temp=20.0,
            feels_like=18.0,
            condition="Clear",
            icon="01d",
            location="Test",
            recommendation="Good",
            wind_speed=5.0,
            wind_deg=270,
        )

        assert weather.wind_direction_compass == "←"

    def test_weather_emoji_clear(self):
        """Test weather emoji for clear conditions."""
        weather = WeatherResponse(
            temp=25.0,
            feels_like=24.0,
            condition="Clear sky",
            icon="01d",
            location="Test",
            recommendation="Sunny day",
            wind_speed=3.0,
            wind_deg=90,
        )

        assert weather.weather_emoji == "☀️"

    def test_weather_emoji_cloudy(self):
        """Test weather emoji for cloudy conditions."""
        weather = WeatherResponse(
            temp=18.0,
            feels_like=17.0,
            condition="Partly cloudy",
            icon="02d",
            location="Test",
            recommendation="Mild",
            wind_speed=4.0,
            wind_deg=180,
        )

        assert weather.weather_emoji == "☁️"

    def test_weather_emoji_rain(self):
        """Test weather emoji for rainy conditions."""
        weather = WeatherResponse(
            temp=15.0,
            feels_like=13.0,
            condition="Light rain",
            icon="10d",
            location="Test",
            recommendation="Bring umbrella",
            wind_speed=6.0,
            wind_deg=45,
        )

        assert weather.weather_emoji == "🌧️"

    def test_weather_emoji_storm(self):
        """Test weather emoji for stormy conditions."""
        weather = WeatherResponse(
            temp=16.0,
            feels_like=14.0,
            condition="Thunderstorm",
            icon="11d",
            location="Test",
            recommendation="Stay inside",
            wind_speed=12.0,
            wind_deg=270,
        )

        assert weather.weather_emoji == "⛈️"

    def test_weather_emoji_snow(self):
        """Test weather emoji for snowy conditions."""
        weather = WeatherResponse(
            temp=-2.0,
            feels_like=-5.0,
            condition="Light snow",
            icon="13d",
            location="Test",
            recommendation="Dress warm",
            wind_speed=5.0,
            wind_deg=0,
        )

        assert weather.weather_emoji == "❄️"

    def test_weather_emoji_mist(self):
        """Test weather emoji for misty conditions."""
        weather = WeatherResponse(
            temp=10.0,
            feels_like=9.0,
            condition="Mist",
            icon="50d",
            location="Test",
            recommendation="Low visibility",
            wind_speed=2.0,
            wind_deg=135,
        )

        assert weather.weather_emoji == "🌫️"

    def test_beaufort_scale_calm(self):
        """Test Beaufort scale for calm conditions (< 0.5 m/s)."""
        weather = WeatherResponse(
            temp=20.0,
            feels_like=19.0,
            condition="Clear",
            icon="01d",
            location="Test",
            recommendation="Perfect",
            wind_speed=0.3,
            wind_deg=0,
        )

        assert weather.beaufort_scale == 0

    def test_beaufort_scale_light_breeze(self):
        """Test Beaufort scale for light breeze (1.6-3.3 m/s)."""
        weather = WeatherResponse(
            temp=22.0,
            feels_like=21.0,
            condition="Clear",
            icon="01d",
            location="Test",
            recommendation="Nice",
            wind_speed=2.5,
            wind_deg=90,
        )

        assert weather.beaufort_scale == 2

    def test_beaufort_scale_moderate_breeze(self):
        """Test Beaufort scale for moderate breeze (5.5-7.9 m/s)."""
        weather = WeatherResponse(
            temp=18.0,
            feels_like=16.0,
            condition="Cloudy",
            icon="03d",
            location="Test",
            recommendation="Breezy",
            wind_speed=6.5,
            wind_deg=180,
        )

        assert weather.beaufort_scale == 4

    def test_beaufort_scale_strong_breeze(self):
        """Test Beaufort scale for strong breeze (10.8-13.8 m/s)."""
        weather = WeatherResponse(
            temp=15.0,
            feels_like=12.0,
            condition="Windy",
            icon="03d",
            location="Test",
            recommendation="Hold onto your hat",
            wind_speed=12.0,
            wind_deg=270,
        )

        assert weather.beaufort_scale == 6
