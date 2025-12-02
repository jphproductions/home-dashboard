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
