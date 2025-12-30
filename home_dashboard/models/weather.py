"""Pydantic models for weather data."""

from pydantic import BaseModel


class WeatherInfo(BaseModel):
    """Weather condition info from OpenWeatherMap."""

    id: int
    main: str
    description: str
    icon: str


class MainInfo(BaseModel):
    """Main weather metrics from OpenWeatherMap."""

    temp: float
    feels_like: float
    pressure: int
    humidity: int
    sea_level: int | None = None
    grnd_level: int | None = None


class WindInfo(BaseModel):
    """Wind information from OpenWeatherMap."""

    speed: float
    deg: int
    gust: float | None = None


class CloudsInfo(BaseModel):
    """Cloud coverage information."""

    all: int


class CurrentWeather(BaseModel):
    """Raw OpenWeatherMap API response model."""

    coord: dict[str, float]
    weather: list[WeatherInfo]
    base: str
    main: MainInfo
    visibility: int
    wind: WindInfo
    clouds: CloudsInfo
    dt: int
    sys: dict[str, int | str]
    timezone: int
    id: int
    name: str
    cod: int


class WeatherResponse(BaseModel):
    """Simplified weather response for API endpoints and UI."""

    temp: float
    feels_like: float
    condition: str
    icon: str
    location: str
    recommendation: str
    wind_speed: float
    wind_deg: int

    @property
    def icon_url(self) -> str:
        """Get OpenWeatherMap icon URL from icon code."""
        return f"https://openweathermap.org/img/wn/{self.icon}@2x.png"

    @property
    def wind_direction_compass(self) -> str:
        """Convert wind direction degrees to compass arrow."""
        directions = ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"]
        idx = round(self.wind_deg / 45) % 8
        return directions[idx]

    @property
    def beaufort_scale(self) -> int:
        """Get Beaufort scale number from wind speed (m/s).

        Uses binary search for efficient lookup of wind speed thresholds.
        Beaufort scale ranges from 0 (calm) to 12 (hurricane).
        """
        import bisect

        # Beaufort scale thresholds in m/s (lower bounds for each scale)
        thresholds = [0.5, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.7]
        return bisect.bisect_right(thresholds, self.wind_speed)

    @property
    def beaufort_description(self) -> str:
        """Get Beaufort scale description from wind speed."""
        beaufort_descriptions = {
            0: "Calm",
            1: "Light air",
            2: "Light breeze",
            3: "Gentle breeze",
            4: "Moderate breeze",
            5: "Fresh breeze",
            6: "Strong breeze",
            7: "Near gale",
            8: "Gale",
            9: "Strong gale",
            10: "Storm",
            11: "Violent storm",
            12: "Hurricane",
        }
        return beaufort_descriptions[self.beaufort_scale]

    @classmethod
    def from_openweather(cls, data: CurrentWeather) -> "WeatherResponse":
        """Create WeatherResponse from OpenWeatherMap data.

        Args:
            data: Raw CurrentWeather data from OpenWeatherMap API

        Returns:
            WeatherResponse with simplified, formatted data
        """
        temp = data.main.temp
        condition = data.weather[0].main if data.weather else "Unknown"
        icon = data.weather[0].icon if data.weather else ""

        # Generate recommendation based on temperature (Celsius)
        import bisect

        temp_thresholds = [5, 10, 15, 20, 25]
        recommendations = [
            "Bundle up! It's very cold outside. ❄️",
            "Wear a warm jacket. 🧥",
            "Light jacket recommended. 🍂",
            "Perfect temperature! 😊",
            "Nice and warm! ☀️",
            "Stay cool and hydrated! 🌡️",
        ]
        idx = bisect.bisect_right(temp_thresholds, temp)
        recommendation = recommendations[idx]

        return cls(
            temp=temp,
            feels_like=data.main.feels_like,
            condition=condition,
            icon=icon,
            location=data.name,
            recommendation=recommendation,
            wind_speed=data.wind.speed,
            wind_deg=data.wind.deg,
        )
