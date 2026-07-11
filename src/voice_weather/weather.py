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


WMO_DESCRIPTIONS = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


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


def _geocode_city(city: str, timeout: int) -> tuple[float, float]:
    try:
        parts = [part.strip() for part in city.split(",") if part.strip()]
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": parts[0], "count": 10, "language": "en", "format": "json"},
            headers={"User-Agent": "voice-weather/0.2.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            raise WeatherError(f"找不到城市：{city}")
        selected = results[0]
        if len(parts) > 1:
            qualifier = " ".join(parts[1:]).lower()
            selected = next(
                (item for item in results if qualifier in " ".join(
                    str(item.get(key, "")) for key in ("country", "country_code", "admin1", "admin2")
                ).lower()),
                selected,
            )
        return float(selected["latitude"]), float(selected["longitude"])
    except WeatherError:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise WeatherError(f"无法定位城市 {city}：{exc}") from exc


def fetch_forecast(city: str, days: int = 7, timeout: int = 10) -> list[ForecastDay]:
    if not 1 <= days <= 7:
        raise ValueError("days must be between 1 and 7")
    try:
        latitude, longitude = _geocode_city(city, timeout)
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": days,
            },
            headers={"User-Agent": "voice-weather/0.2.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        daily = response.json()["daily"]
        return [
            ForecastDay(
                date=daily["time"][index],
                min_c=str(round(daily["temperature_2m_min"][index])),
                max_c=str(round(daily["temperature_2m_max"][index])),
                description=WMO_DESCRIPTIONS.get(daily["weather_code"][index], "Unknown"),
                rain_chance=str(daily["precipitation_probability_max"][index] or 0),
            )
            for index in range(len(daily["time"]))
        ]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise WeatherError(f"无法解析 {city} 的天气预报：{exc}") from exc
