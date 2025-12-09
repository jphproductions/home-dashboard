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
    def wind_direction_compass(self) -> str:
        """Convert wind direction degrees to compass arrow."""
        directions = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        idx = round(self.wind_deg / 45) % 8
        return directions[idx]

    @property
    def weather_emoji(self) -> str:
        """Get emoji for weather condition."""
        condition_lower = self.condition.lower()
        if "clear" in condition_lower:
            return "☀️"
        elif "cloud" in condition_lower:
            return "☁️"
        elif "rain" in condition_lower or "drizzle" in condition_lower:
            return "🌧️"
        elif "thunder" in condition_lower or "storm" in condition_lower:
            return "⛈️"
        elif "snow" in condition_lower:
            return "❄️"
        elif "mist" in condition_lower or "fog" in condition_lower:
            return "🌫️"
        else:
            return "🌤️"

    @property
    def beaufort_scale(self) -> int:
        """Get Beaufort scale number from wind speed (m/s)."""
        if self.wind_speed < 0.5:
            return 0
        elif self.wind_speed < 1.6:
            return 1
        elif self.wind_speed < 3.4:
            return 2
        elif self.wind_speed < 5.5:
            return 3
        elif self.wind_speed < 8.0:
            return 4
        elif self.wind_speed < 10.8:
            return 5
        elif self.wind_speed < 13.9:
            return 6
        elif self.wind_speed < 17.2:
            return 7
        elif self.wind_speed < 20.8:
            return 8
        elif self.wind_speed < 24.5:
            return 9
        elif self.wind_speed < 28.5:
            return 10
        elif self.wind_speed < 32.7:
            return 11
        else:
            return 12

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

        # Generate recommendation based on temperature
        if temp < 5:
            recommendation = "Bundle up! It's very cold outside. ❄️"
        elif temp < 10:
            recommendation = "Wear a warm jacket. 🧥"
        elif temp < 15:
            recommendation = "Light jacket recommended. 🍂"
        elif temp < 20:
            recommendation = "Perfect temperature! 😊"
        elif temp < 25:
            recommendation = "Nice and warm! ☀️"
        else:
            recommendation = "Stay cool and hydrated! 🌡️"

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
