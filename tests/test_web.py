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
        assert "/static/app.js" in body
    finally:
        server.shutdown()


def test_state_api(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        data = json.loads(urlopen(base + "/api/state", timeout=2).read())
        assert data["version"] == "3.1.0"
        assert data["cities"][0]["city"] == "Toronto"
        assert data["voice"] == "Samantha"
    finally:
        server.shutdown()


def test_server_is_localhost_only():
    assert web.HOST == "127.0.0.1"


def test_city_add_api(monkeypatch):
    settings = {"version": 5, "language": "en", "voice_enabled": True, "local_city": None, "favorites": []}
    monkeypatch.setattr(web, "load_settings", lambda: settings)
    monkeypatch.setattr(web, "save_settings", lambda data: None)
    monkeypatch.setattr(web, "localized_city_labels", lambda name, latitude, longitude: {"zh": "巴黎", "en": "Paris", "fr": "Paris", "es": "París", "ja": "パリ"})
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = json.dumps({"action": "add", "city": "Paris, Île-de-France, France", "name": "Paris", "latitude": 48.85, "longitude": 2.35, "language": "fr"}).encode()
        request = Request(f"http://{web.HOST}:{server.server_port}/api/cities", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        data = json.loads(urlopen(request, timeout=2).read())
        assert data["favorites"][0]["city"] == "Paris, Île-de-France, France"
        assert data["favorites"][0]["labels"]["fr"] == "Paris"
    finally:
        server.shutdown()


def test_web_speech_uses_selected_language(monkeypatch):
    sample = Weather("20", "19", "0", "55", "12", "1013", "Clear", "10:00")
    monkeypatch.setattr(web, "fetch_weather", lambda city: sample)
    text = web.build_web_speech("Paris, France", "Paris", "fr")
    assert "Météo à Paris" in text
    assert "degrés Celsius" in text
