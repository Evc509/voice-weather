from voice_weather.app import build_script
import requests

from voice_weather.weather import Weather, WeatherError, fetch_weather


SAMPLE = Weather("20", "19", "0", "55", "12", "1013", "Sunny", "10:00")


def test_english_script():
    assert "Weather in Toronto" in build_script("Toronto", "多伦多", SAMPLE, "en")


def test_chinese_script():
    script = build_script("Toronto", "多伦多", SAMPLE, "zh")
    assert "多伦多当前天气" in script
    assert "晴朗" in script


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "current_condition": [{
                "temp_C": "20",
                "FeelsLikeC": "19",
                "precipMM": "0",
                "humidity": "55",
                "windspeedKmph": "12",
                "pressure": "1013",
                "weatherDesc": [{"value": "Sunny"}],
            }]
        }


def test_fetch_weather_parses_response(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())
    weather = fetch_weather("Toronto")
    assert weather.temperature_c == "20"
    assert weather.description == "Sunny"


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
