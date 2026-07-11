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


def fetch_weather(city: str, timeout: int = 10) -> Weather:
    try:
        response = requests.get(
            f"https://wttr.in/{city}",
            params={"format": "j1"},
            headers={"User-Agent": "voice-weather/0.1"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
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
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        raise WeatherError(f"无法获取 {city} 的天气：{exc}") from exc

