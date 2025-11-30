"""Pydantic models for request/response validation."""

from pydantic import BaseModel


class WeatherInfo(BaseModel):
    id: int
    main: str
    description: str
    icon: str


class MainInfo(BaseModel):
    temp: float
    feels_like: float
    pressure: int
    humidity: int
    sea_level: int | None = None
    grnd_level: int | None = None


class WindInfo(BaseModel):
    speed: float
    deg: int
    gust: float | None = None


class CloudsInfo(BaseModel):
    all: int


class CurrentWeather(BaseModel):
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
