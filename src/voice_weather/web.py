"""Local-only web interface for Voice Weather."""

import argparse
import json
import mimetypes
import threading
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

from . import __version__
from .app import build_script
from .i18n import LANGUAGES, weather_text
from .settings import display_cities, load_settings, save_settings
from .speech import SpeechError, speak, stop_speech, voice_for
from .weather import WeatherError, fetch_forecast, fetch_weather, resolve_city

HOST = "127.0.0.1"
PORT = 8765
STATIC_ROOT = files("voice_weather").joinpath("web_static")


def build_web_speech(city: str, label: str, language: str) -> str:
    weather = fetch_weather(city)
    return build_script(city, label or city, weather, language)


class WebHandler(BaseHTTPRequestHandler):
    server_version = "VoiceWeather/3"

    def log_message(self, fmt, *args):
        return

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_static(self, name):
        target = STATIC_ROOT.joinpath(name)
        try:
            body = target.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.send_static("index.html")
        if parsed.path.startswith("/static/"):
            name = parsed.path.removeprefix("/static/")
            if "/" in name or ".." in name:
                return self.send_error(404)
            return self.send_static(name)
        if parsed.path == "/api/state":
            settings = load_settings()
            return self.send_json({
                "version": __version__,
                "language": settings["language"],
                "voice_enabled": settings.get("voice_enabled", True),
                "voice": voice_for(settings["language"]),
                "languages": LANGUAGES,
                "cities": display_cities(settings),
                "favorites": settings.get("favorites", []),
            })
        query = parse_qs(parsed.query)
        city = query.get("city", [""])[0].strip()
        language = query.get("language", ["en"])[0]
        if parsed.path == "/api/weather" and city:
            try:
                weather = fetch_weather(city)
                data = asdict(weather)
                data["description_localized"] = weather_text(language, weather.description)
                return self.send_json({"city": city, "weather": data})
            except WeatherError as exc:
                return self.send_json({"error": str(exc)}, 502)
        if parsed.path == "/api/forecast" and city:
            try:
                days = min(7, max(1, int(query.get("days", ["7"])[0])))
                forecast = [asdict(day) for day in fetch_forecast(city, days)]
                for day in forecast:
                    day["description_localized"] = weather_text(language, day["description"])
                return self.send_json({"city": city, "forecast": forecast})
            except (WeatherError, ValueError) as exc:
                return self.send_json({"error": str(exc)}, 502)
        return self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self.send_json({"error": "Invalid JSON"}, 400)
        if self.path == "/api/preferences":
            settings = load_settings()
            language = payload.get("language")
            if language in LANGUAGES:
                settings["language"] = language
            if isinstance(payload.get("voice_enabled"), bool):
                settings["voice_enabled"] = payload["voice_enabled"]
            save_settings(settings)
            return self.send_json({"ok": True})
        if self.path == "/api/cities":
            settings = load_settings()
            favorites = settings.setdefault("favorites", [])
            action = payload.get("action")
            city = str(payload.get("city", "")).strip()
            language = payload.get("language", settings.get("language", "en"))
            label = str(payload.get("label", "")).strip()
            try:
                index = int(payload.get("index", -1))
            except (TypeError, ValueError):
                index = -1
            if action == "add":
                if not city:
                    return self.send_json({"error": "City is required"}, 400)
                try:
                    resolved = resolve_city(city, language)
                except WeatherError as exc:
                    return self.send_json({"error": str(exc)}, 422)
                canonical = resolved["city"]
                if any(item.get("city", "").casefold() == canonical.casefold() for item in favorites):
                    return self.send_json({"error": "City already exists"}, 409)
                favorites.append({"city": canonical, "labels": {language: label or resolved["label"]}})
            elif action == "replace" and 0 <= index < len(favorites):
                if not city:
                    return self.send_json({"error": "City is required"}, 400)
                try:
                    resolved = resolve_city(city, language)
                except WeatherError as exc:
                    return self.send_json({"error": str(exc)}, 422)
                old_labels = favorites[index].get("labels", {})
                old_labels[language] = label or resolved["label"]
                favorites[index] = {"city": resolved["city"], "labels": old_labels}
            elif action == "delete" and 0 <= index < len(favorites):
                favorites.pop(index)
            else:
                return self.send_json({"error": "Invalid city action"}, 400)
            save_settings(settings)
            return self.send_json({"ok": True, "favorites": favorites})
        if self.path == "/api/speak":
            language = payload.get("language", "en")
            city = str(payload.get("city", "")).strip()
            label = str(payload.get("label", "")).strip()
            try:
                text = build_web_speech(city, label, language) if city else str(payload.get("text", ""))[:1200]
                if not text:
                    return self.send_json({"error": "Missing text"}, 400)
                threading.Thread(target=speak, args=(text, language), daemon=True).start()
                return self.send_json({"ok": True})
            except (SpeechError, WeatherError) as exc:
                return self.send_json({"error": str(exc)}, 422)
        if self.path == "/api/speech/stop":
            stop_speech()
            return self.send_json({"ok": True})
        return self.send_error(404)


def serve(port=PORT, open_browser=True):
    server = ThreadingHTTPServer((HOST, port), WebHandler)
    url = f"http://{HOST}:{port}"
    print(f"Voice Weather Web: {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Voice Weather local web interface")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    return serve(args.port, not args.no_browser)
