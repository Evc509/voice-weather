from dataclasses import dataclass

import requests


class WeatherError(RuntimeError):
    pass


@dataclass(frozen=True)
class Weather:
    temperature_c: str
    feels_like_c: str
    precipitation_mm: str
    humidity: str
    wind_kph: str
    pressure_hpa: str
    description: str
    local_time: str


@dataclass(frozen=True)
class ForecastDay:
    date: str
    min_c: str
    max_c: str
    description: str
    rain_chance: str


def _get_weather_data(city: str, timeout: int) -> dict:
    try:
        response = requests.get(
            f"https://wttr.in/{city}",
            params={"format": "j1"},
            headers={"User-Agent": "voice-weather/0.2.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherError(f"无法获取 {city} 的天气：{exc}") from exc


def fetch_weather(city: str, timeout: int = 10) -> Weather:
    try:
        data = _get_weather_data(city, timeout)
        current = data["current_condition"][0]
        nearest = data.get("nearest_area", [{}])[0]
        local_time = nearest.get("localObsDateTime") or current.get("localObsDateTime", "未知")
        description = current.get("weatherDesc", [{"value": "Unknown"}])[0]["value"]
        return Weather(
            temperature_c=current["temp_C"],
            feels_like_c=current.get("FeelsLikeC", current["temp_C"]),
            precipitation_mm=current.get("precipMM", "0"),
            humidity=current.get("humidity", "未知"),
            wind_kph=current.get("windspeedKmph", "未知"),
            pressure_hpa=current.get("pressure", "未知"),
            description=description,
            local_time=local_time,
        )
    except (KeyError, IndexError, TypeError) as exc:
        raise WeatherError(f"无法获取 {city} 的天气：{exc}") from exc


def fetch_forecast(city: str, days: int = 3, timeout: int = 10) -> list[ForecastDay]:
    if not 1 <= days <= 3:
        raise ValueError("days must be between 1 and 3")
    try:
        result = []
        for day in _get_weather_data(city, timeout)["weather"][:days]:
            hourly = day.get("hourly", [])
            midday = next((item for item in hourly if item.get("time") == "1200"), hourly[0])
            description = midday.get("weatherDesc", [{"value": "Unknown"}])[0]["value"]
            rain_chance = max((int(item.get("chanceofrain", 0)) for item in hourly), default=0)
            result.append(ForecastDay(
                date=day["date"],
                min_c=day["mintempC"],
                max_c=day["maxtempC"],
                description=description,
                rain_chance=str(rain_chance),
            ))
        return result
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise WeatherError(f"无法解析 {city} 的天气预报：{exc}") from exc
