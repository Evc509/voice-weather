"""Local-only web interface for Voice Weather."""

import argparse
import json
import mimetypes
import threading
import webbrowser
from dataclasses import asdict, fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from socketserver import TCPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

from . import __version__
from .app import build_script
from .i18n import LANGUAGES, weather_text
from .settings import MAX_FAVORITES, cities_match, display_cities, load_settings, save_settings
from .speech import SpeechError, speak, stop_speech, voice_for
from .weather import Weather, WeatherError, city_metadata, fetch_forecast, fetch_forecast_at, fetch_weather, fetch_weather_at, localized_city_labels, search_cities

HOST = "127.0.0.1"
PORT = 8765
STATIC_ROOT = files("voice_weather").joinpath("web_static")


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    """HTTP server that avoids an unnecessary reverse-DNS lookup at startup."""

    def server_bind(self):
        TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port


WEATHER_FIELDS = tuple(field.name for field in fields(Weather))
CITY_MESSAGES = {
    "zh": {"duplicate": "该城市已经在列表中", "limit": f"城市列表最多保存 {MAX_FAVORITES} 个城市"},
    "en": {"duplicate": "This city is already in the list", "limit": f"The city list is limited to {MAX_FAVORITES} cities"},
    "fr": {"duplicate": "Cette ville est déjà dans la liste", "limit": f"La liste est limitée à {MAX_FAVORITES} villes"},
    "es": {"duplicate": "Esta ciudad ya está en la lista", "limit": f"La lista está limitada a {MAX_FAVORITES} ciudades"},
    "ja": {"duplicate": "この都市はすでにリストにあります", "limit": f"都市は最大 {MAX_FAVORITES} 件までです"},
}


def city_message(language: str, key: str) -> str:
    return CITY_MESSAGES.get(language, CITY_MESSAGES["en"])[key]


def weather_from_payload(payload) -> Optional[Weather]:
    if not isinstance(payload, dict) or not all(name in payload for name in WEATHER_FIELDS):
        return None
    return Weather(**{name: str(payload[name]) for name in WEATHER_FIELDS})


def build_web_speech(city: str, label: str, language: str, weather: Optional[Weather] = None) -> str:
    weather = weather or fetch_weather(city)
    spoken_city = label or city
    return build_script(spoken_city, spoken_city, weather, language)


def repair_city_entry(city: dict, language: str) -> bool:
    """Repair legacy localized city records using Open-Meteo's stable location ID."""
    labels = city.get("labels") if isinstance(city.get("labels"), dict) else {}
    if all(labels.get(code) for code in LANGUAGES):
        return False
    if city.get("latitude") is None or city.get("longitude") is None:
        return False
    try:
        location_id = city.get("location_id")
        if location_id is None:
            query = labels.get(language) or labels.get("en") or city.get("city", "").split(",")[0]
            candidates = search_cities(query, language, 10)
            if not candidates:
                return False
            latitude, longitude = float(city["latitude"]), float(city["longitude"])
            closest = min(
                candidates,
                key=lambda item: abs(item["latitude"] - latitude) + abs(item["longitude"] - longitude),
            )
            if abs(closest["latitude"] - latitude) + abs(closest["longitude"] - longitude) > 1:
                return False
            location_id = closest["location_id"]
        metadata = city_metadata(int(location_id))
        city.update(metadata)
        city["zh"] = metadata["labels"]["zh"]
        return True
    except (WeatherError, TypeError, ValueError):
        return False


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
        self.send_header("Cache-Control", "no-store")
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
            changed = False
            for favorite in settings.get("favorites", []):
                changed = repair_city_entry(favorite, settings.get("language", "en")) or changed
            local = settings.get("local_city")
            if local and not local.get("labels") and local.get("latitude") is not None:
                try:
                    local["labels"] = localized_city_labels(local["city"].split(",")[0], float(local["latitude"]), float(local["longitude"]))
                    changed = True
                except WeatherError:
                    pass
            if changed:
                save_settings(settings)
            return self.send_json({
                "version": __version__,
                "language": settings["language"],
                "voice_enabled": settings.get("voice_enabled", True),
                "voice": voice_for(settings["language"]),
                "languages": LANGUAGES,
                "cities": display_cities(settings),
                "favorites": settings.get("favorites", []),
                "max_favorites": MAX_FAVORITES,
            })
        query = parse_qs(parsed.query)
        city = query.get("city", [""])[0].strip()
        language = query.get("language", ["en"])[0]
        try:
            latitude = float(query.get("latitude", [""])[0])
            longitude = float(query.get("longitude", [""])[0])
        except ValueError:
            latitude = longitude = None
        if parsed.path == "/api/weather" and city:
            try:
                weather = fetch_weather_at(latitude, longitude, city) if latitude is not None else fetch_weather(city)
                data = asdict(weather)
                data["description_localized"] = weather_text(language, weather.description)
                return self.send_json({"city": city, "weather": data})
            except WeatherError as exc:
                return self.send_json({"error": str(exc)}, 502)
        if parsed.path == "/api/cities/search":
            term = query.get("q", [""])[0].strip()
            try:
                results = search_cities(term, language)
                settings = load_settings()
                existing_ids = {item.get("location_id") for item in settings.get("favorites", [])}
                existing_names = {
                    str(item.get("labels", {}).get(language, "")).strip().casefold()
                    for item in settings.get("favorites", [])
                }
                for result in results:
                    result["duplicate"] = (
                        result["location_id"] in existing_ids
                        or result["name"].strip().casefold() in existing_names
                    )
                return self.send_json({"results": results, "max_favorites": MAX_FAVORITES})
            except WeatherError as exc:
                return self.send_json({"error": str(exc)}, 502)
        if parsed.path == "/api/forecast" and city:
            try:
                days = min(7, max(1, int(query.get("days", ["7"])[0])))
                days_data = fetch_forecast_at(latitude, longitude, days, city) if latitude is not None else fetch_forecast(city, days)
                forecast = [asdict(day) for day in days_data]
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
            language = settings.get("language", "en")
            try:
                index = int(payload.get("index", -1))
            except (TypeError, ValueError):
                index = -1
            if action == "add":
                try:
                    location_id = int(payload["location_id"])
                except (KeyError, TypeError, ValueError):
                    return self.send_json({"error": "A confirmed search result is required"}, 400)
                if any(item.get("location_id") == location_id for item in favorites):
                    return self.send_json({"error": city_message(language, "duplicate")}, 409)
                if len(favorites) >= MAX_FAVORITES:
                    return self.send_json({"error": city_message(language, "limit")}, 409)
                try:
                    metadata = city_metadata(location_id)
                except WeatherError as exc:
                    return self.send_json({"error": str(exc)}, 422)
                if any(cities_match(item, metadata) for item in favorites):
                    return self.send_json({"error": city_message(language, "duplicate")}, 409)
                metadata["zh"] = metadata["labels"]["zh"]
                favorites.append(metadata)
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
                snapshot = weather_from_payload(payload.get("weather"))
                text = build_web_speech(city, label, language, snapshot) if city else str(payload.get("text", ""))[:1200]
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


def create_server(port=PORT):
    """Create a localhost-only server without starting its request loop."""
    return LocalThreadingHTTPServer((HOST, port), WebHandler)


def serve(port=PORT, open_browser=True):
    server = create_server(port)
    url = f"http://{HOST}:{server.server_port}"
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
