from voice_weather.app import build_script
import requests

from voice_weather.weather import Weather, WeatherError, fetch_forecast, fetch_weather


SAMPLE = Weather("20", "19", "0", "55", "12", "1013", "Sunny", "10:00")


def test_english_script():
    assert "Weather in Toronto" in build_script("Toronto", "多伦多", SAMPLE, "en")


def test_chinese_script():
    script = build_script("Toronto", "多伦多", SAMPLE, "zh")
    assert "多伦多当前天气" in script
    assert "晴朗" in script


class FakeCurrentResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"current": {
            "temperature_2m": 20.2, "apparent_temperature": 18.7,
            "precipitation": 0, "relative_humidity_2m": 55,
            "wind_speed_10m": 12.1, "surface_pressure": 1013.2,
            "weather_code": 0, "time": "2026-07-10T10:00",
        }, "daily": {"uv_index_max": [6.4]}}


class FakeAirResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"current": {"us_aqi": 42, "pm2_5": 7.2, "pm10": 12.8}}


class FakeGeocodingResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"results": [{"name": "Toronto", "latitude": 43.65, "longitude": -79.38, "admin1": "Ontario", "country": "Canada"}]}


class FakeForecastResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"daily": {
            "time": ["2026-07-10"],
            "temperature_2m_min": [18.2],
            "temperature_2m_max": [27.4],
            "precipitation_probability_max": [35],
            "weather_code": [0],
            "precipitation_sum": [2.3],
            "wind_speed_10m_max": [22.4],
            "uv_index_max": [6.4],
            "sunrise": ["2026-07-10T05:45"],
            "sunset": ["2026-07-10T21:00"],
        }}


def test_fetch_weather_parses_response(monkeypatch):
    def fake_get(url, **kwargs):
        if "geocoding" in url:
            return FakeGeocodingResponse()
        return FakeAirResponse() if "air-quality" in url else FakeCurrentResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    weather = fetch_weather("Toronto")
    assert weather.temperature_c == "20"
    assert weather.description == "Clear"
    assert weather.aqi == "42"
    assert weather.uv_index == "6.4"


def test_fetch_weather_wraps_network_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(requests, "get", fail)
    try:
        fetch_weather("Toronto")
    except WeatherError as exc:
        assert "Toronto" in str(exc)
    else:
        raise AssertionError("WeatherError was not raised")


def test_fetch_forecast_parses_daily_summary(monkeypatch):
    def fake_get(url, **kwargs):
        return FakeGeocodingResponse() if "geocoding" in url else FakeForecastResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    forecast = fetch_forecast("Toronto", days=1)
    assert forecast[0].date == "2026-07-10"
    assert forecast[0].max_c == "27"
    assert forecast[0].description == "Clear"
    assert forecast[0].rain_chance == "35"
    assert forecast[0].sunrise == "05:45"
