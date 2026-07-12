from voice_weather.app import build_script
import requests

from voice_weather.weather import Weather, WeatherError, city_metadata, city_result_by_id, fetch_forecast, fetch_weather, fetch_weather_at, localized_city_labels, search_cities


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
        return {"results": [{"id": 6167865, "name": "Toronto", "latitude": 43.65, "longitude": -79.38, "admin1": "Ontario", "country": "Canada"}]}


class FakeLocationResponse:
    def __init__(self, language):
        self.language = language

    def raise_for_status(self):
        return None

    def json(self):
        names = {"zh": "多伦多", "en": "Toronto", "fr": "Toronto", "es": "Toronto", "ja": "トロント"}
        regions = {"zh": "安大略", "en": "Ontario", "fr": "Ontario", "es": "Ontario", "ja": "オンタリオ州"}
        countries = {"zh": "加拿大", "en": "Canada", "fr": "Canada", "es": "Canadá", "ja": "カナダ"}
        return {
            "id": 6167865,
            "name": names[self.language],
            "latitude": 43.70643,
            "longitude": -79.39864,
            "admin1": regions[self.language],
            "country": countries[self.language],
        }


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


def test_city_search_returns_confirmable_location(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeGeocodingResponse())
    results = search_cities("Toronto", "fr")
    assert results[0]["canonical"] == "Toronto, Ontario, Canada"
    assert results[0]["location_id"] == 6167865
    assert results[0]["latitude"] == 43.65


def test_city_labels_are_collected_for_all_languages(monkeypatch):
    def fake_get(url, **kwargs):
        if url.endswith("/get"):
            return FakeLocationResponse(kwargs["params"]["language"])
        return FakeGeocodingResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    labels = localized_city_labels("Toronto", 43.65, -79.38)
    assert labels["zh"] == "多伦多"
    assert labels["en"] == "Toronto"


def test_city_metadata_uses_stable_id_for_every_language(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, **kwargs: FakeLocationResponse(kwargs["params"]["language"]),
    )
    metadata = city_metadata(6167865)
    assert metadata["city"] == "Toronto, Ontario, Canada"
    assert metadata["labels"]["zh"] == "多伦多"
    assert metadata["labels"]["ja"] == "トロント"
    assert metadata["location_id"] == 6167865


def test_city_result_by_id_localizes_without_changing_identity(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, **kwargs: FakeLocationResponse(kwargs["params"]["language"]),
    )
    result = city_result_by_id(6167865, "zh")
    assert result["name"] == "多伦多"
    assert result["location_id"] == 6167865
    assert result["latitude"] == 43.70643


def test_coordinate_weather_skips_geocoding(monkeypatch):
    urls = []
    def fake_get(url, **kwargs):
        urls.append(url)
        return FakeAirResponse() if "air-quality" in url else FakeCurrentResponse()
    monkeypatch.setattr(requests, "get", fake_get)
    assert fetch_weather_at(43.65, -79.38).temperature_c == "20"
    assert not any("geocoding" in url for url in urls)
