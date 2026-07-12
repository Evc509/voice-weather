import json
import threading
from urllib.request import Request, urlopen

from voice_weather import web
from voice_weather.weather import Weather


def run_server(monkeypatch):
    monkeypatch.setattr(web, "load_settings", lambda: {
        "language": "en", "voice_enabled": True,
        "local_city": {"city": "Toronto", "zh": "多伦多"},
        "favorites": [],
    })
    monkeypatch.setattr(web, "voice_for", lambda language: "Samantha")
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://{web.HOST}:{server.server_port}"


def test_home_page(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        body = urlopen(base, timeout=2).read().decode()
        assert "Voice Weather" in body
        assert "/static/app.js?v=320-city-sync" in body
    finally:
        server.shutdown()


def test_static_assets_disable_browser_cache(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        response = urlopen(base + "/static/app.js?v=320-city-sync", timeout=2)
        assert response.headers["Cache-Control"] == "no-store"
    finally:
        server.shutdown()


def test_state_api(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        data = json.loads(urlopen(base + "/api/state", timeout=2).read())
        assert data["version"] == "3.2.0"
        assert data["cities"][0]["city"] == "Toronto"
        assert data["voice"] == "Samantha"
    finally:
        server.shutdown()


def test_server_is_localhost_only():
    assert web.HOST == "127.0.0.1"


def test_created_server_uses_literal_localhost_name():
    server = web.create_server(0)
    try:
        assert isinstance(server, web.LocalThreadingHTTPServer)
        assert server.server_name == web.HOST
    finally:
        server.server_close()


def test_city_add_api(monkeypatch):
    settings = {"version": 5, "language": "en", "voice_enabled": True, "local_city": None, "favorites": []}
    monkeypatch.setattr(web, "load_settings", lambda: settings)
    monkeypatch.setattr(web, "save_settings", lambda data: None)
    monkeypatch.setattr(web, "city_metadata", lambda location_id: {
        "city": "Paris, Île-de-France, France",
        "labels": {"zh": "巴黎", "en": "Paris", "fr": "Paris", "es": "París", "ja": "パリ"},
        "latitude": 48.85,
        "longitude": 2.35,
        "location_id": location_id,
    })
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = json.dumps({"action": "add", "location_id": 2988507}).encode()
        request = Request(f"http://{web.HOST}:{server.server_port}/api/cities", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        data = json.loads(urlopen(request, timeout=2).read())
        assert data["favorites"][0]["city"] == "Paris, Île-de-France, France"
        assert data["favorites"][0]["labels"]["fr"] == "Paris"
        assert data["favorites"][0]["location_id"] == 2988507
    finally:
        server.shutdown()


def test_web_speech_uses_selected_language(monkeypatch):
    sample = Weather("20", "19", "0", "55", "12", "1013", "Clear", "10:00")
    monkeypatch.setattr(web, "fetch_weather", lambda city: sample)
    text = web.build_web_speech("Paris, France", "Paris", "fr")
    assert "Météo à Paris" in text
    assert "degrés Celsius" in text


def test_web_speech_uses_displayed_snapshot_without_refetching(monkeypatch):
    sample = Weather("11", "9", "0", "62", "15", "1009", "Partly cloudy", "10:30")
    monkeypatch.setattr(web, "fetch_weather", lambda city: (_ for _ in ()).throw(AssertionError("refetched")))
    text = web.build_web_speech("Waterloo, Ontario, Canada", "滑铁卢", "zh", sample)
    assert "滑铁卢当前天气局部多云" in text
    assert "温度摄氏11度" in text


def test_repairs_legacy_localized_city_with_location_id(monkeypatch):
    city = {
        "city": "多伦多, 安大略, 加拿大",
        "labels": {"zh": "多伦多"},
        "latitude": 43.70643,
        "longitude": -79.39864,
    }
    monkeypatch.setattr(web, "search_cities", lambda *args: [{
        "location_id": 6167865, "latitude": 43.70643, "longitude": -79.39864,
    }])
    monkeypatch.setattr(web, "city_metadata", lambda location_id: {
        "city": "Toronto, Ontario, Canada",
        "labels": {"zh": "多伦多", "en": "Toronto", "fr": "Toronto", "es": "Toronto", "ja": "トロント"},
        "latitude": 43.70643,
        "longitude": -79.39864,
        "location_id": location_id,
    })

    assert web.repair_city_entry(city, "zh") is True
    assert city["city"] == "Toronto, Ontario, Canada"
    assert city["labels"]["en"] == "Toronto"
