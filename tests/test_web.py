import json
import threading
from urllib.request import urlopen

from voice_weather import web


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
        assert data["version"] == "3.0.0"
        assert data["cities"][0]["city"] == "Toronto"
        assert data["voice"] == "Samantha"
    finally:
        server.shutdown()


def test_server_is_localhost_only():
    assert web.HOST == "127.0.0.1"
