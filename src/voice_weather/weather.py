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
    uv_index: str = "Unknown"
    aqi: str = "Unknown"
    pm2_5: str = "Unknown"
    pm10: str = "Unknown"


@dataclass(frozen=True)
class ForecastDay:
    date: str
    min_c: str
    max_c: str
    description: str
    rain_chance: str
    precipitation_mm: str = "0"
    wind_max_kph: str = "Unknown"
    uv_index: str = "Unknown"
    sunrise: str = "Unknown"
    sunset: str = "Unknown"


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


def fetch_weather(city: str, timeout: int = 10) -> Weather:
    try:
        latitude, longitude = _geocode_city(city, timeout)
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,surface_pressure",
                "daily": "uv_index_max",
                "timezone": "auto",
                "forecast_days": 1,
            },
            headers={"User-Agent": "voice-weather/3.0.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        weather_data = response.json()
        current = weather_data["current"]
        air_response = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={"latitude": latitude, "longitude": longitude, "current": "us_aqi,pm2_5,pm10"},
            headers={"User-Agent": "voice-weather/3.0.0"}, timeout=timeout,
        )
        air_response.raise_for_status()
        air = air_response.json()["current"]
        return Weather(
            temperature_c=str(round(current["temperature_2m"])),
            feels_like_c=str(round(current["apparent_temperature"])),
            precipitation_mm=str(current.get("precipitation", 0)),
            humidity=str(current["relative_humidity_2m"]),
            wind_kph=str(round(current["wind_speed_10m"])),
            pressure_hpa=str(round(current["surface_pressure"])),
            description=WMO_DESCRIPTIONS.get(current["weather_code"], "Unknown"),
            local_time=current.get("time", "Unknown"),
            uv_index=str(round(weather_data["daily"]["uv_index_max"][0], 1)),
            aqi=str(round(air["us_aqi"])),
            pm2_5=str(round(air["pm2_5"], 1)),
            pm10=str(round(air["pm10"], 1)),
        )
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise WeatherError(f"无法获取 {city} 的天气：{exc}") from exc


def _geocode_result(city: str, timeout: int, language: str = "en") -> dict:
    try:
        parts = [part.strip() for part in city.split(",") if part.strip()]
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": parts[0], "count": 10, "language": language, "format": "json"},
            headers={"User-Agent": "voice-weather/3.0.0"},
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
        return selected
    except WeatherError:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise WeatherError(f"无法定位城市 {city}：{exc}") from exc


def _geocode_city(city: str, timeout: int) -> tuple[float, float]:
    selected = _geocode_result(city, timeout)
    return float(selected["latitude"]), float(selected["longitude"])


def resolve_city(city: str, language: str = "en", timeout: int = 10) -> dict:
    selected = _geocode_result(city, timeout, language)
    name = selected["name"]
    region = selected.get("admin1", "")
    country = selected.get("country", "")
    canonical = ", ".join(part for part in (name, region, country) if part)
    return {
        "city": canonical,
        "label": name,
        "latitude": float(selected["latitude"]),
        "longitude": float(selected["longitude"]),
    }


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
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,uv_index_max,sunrise,sunset",
                "timezone": "auto",
                "forecast_days": days,
            },
            headers={"User-Agent": "voice-weather/3.0.0"},
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
                precipitation_mm=str(round(daily["precipitation_sum"][index], 1)),
                wind_max_kph=str(round(daily["wind_speed_10m_max"][index])),
                uv_index=str(round(daily["uv_index_max"][index], 1)),
                sunrise=daily["sunrise"][index].split("T")[-1],
                sunset=daily["sunset"][index].split("T")[-1],
            )
            for index in range(len(daily["time"]))
        ]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise WeatherError(f"无法解析 {city} 的天气预报：{exc}") from exc
