import requests


class LocationError(RuntimeError):
    pass


def detect_location(timeout: int = 10) -> dict:
    try:
        response = requests.get("https://wttr.in/", params={"format": "j1"}, headers={"User-Agent": "voice-weather/2.0.0"}, timeout=timeout)
        response.raise_for_status()
        area = response.json()["nearest_area"][0]
        city = area["areaName"][0]["value"]
        region = area.get("region", [{"value": ""}])[0]["value"]
        country = area.get("country", [{"value": ""}])[0]["value"]
        label = ", ".join(part for part in (city, region, country) if part)
        return {"city": label, "zh": city, "latitude": float(area["latitude"]), "longitude": float(area["longitude"])}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise LocationError(f"Unable to detect location: {exc}") from exc
