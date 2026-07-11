import json
from copy import deepcopy
from pathlib import Path

from .config import APP_DIR, CITIES_FILE, DEFAULT_CITIES

SETTINGS_FILE = APP_DIR / "settings.json"
WORLD_FAVORITES = [
    {"city": "Toronto, Canada", "zh": "多伦多"},
    {"city": "Vancouver, Canada", "zh": "温哥华"},
    {"city": "New York, United States", "zh": "纽约"},
    {"city": "Mexico City, Mexico", "zh": "墨西哥城"},
    {"city": "São Paulo, Brazil", "zh": "圣保罗"},
    {"city": "London, United Kingdom", "zh": "伦敦"},
    {"city": "Paris, France", "zh": "巴黎"},
    {"city": "Cairo, Egypt", "zh": "开罗"},
    {"city": "Dubai, United Arab Emirates", "zh": "迪拜"},
    {"city": "Mumbai, India", "zh": "孟买"},
    {"city": "Singapore", "zh": "新加坡"},
    {"city": "Tokyo, Japan", "zh": "东京"},
    {"city": "Sydney, Australia", "zh": "悉尼"},
]
DEFAULT_SETTINGS = {
    "version": 3,
    "language": "zh",
    "voice_enabled": True,
    "location_consent_asked": False,
    "local_city": None,
    "favorites": WORLD_FAVORITES,
}


def load_settings(path: Path = SETTINGS_FILE, legacy_path: Path = CITIES_FILE) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") in {2, 3} and isinstance(data.get("favorites"), list):
                if data.get("version") == 2:
                    legacy_names = {item["city"].split(",")[0].strip().lower() for item in DEFAULT_CITIES}
                    current_names = {item.get("city", "").split(",")[0].strip().lower() for item in data["favorites"]}
                    if len(current_names) >= 5 and current_names.issubset(legacy_names):
                        data["favorites"] = deepcopy(WORLD_FAVORITES)
                    data["version"] = 3
                    save_settings(data, path)
                return data
        except (OSError, ValueError, AttributeError):
            pass
    settings = deepcopy(DEFAULT_SETTINGS)
    if legacy_path.exists():
        try:
            legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
            if isinstance(legacy, list) and legacy:
                settings["favorites"] = legacy
        except (OSError, ValueError):
            pass
    save_settings(settings, path)
    return settings


def save_settings(settings: dict, path: Path = SETTINGS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_cities(settings: dict) -> list[dict]:
    local = settings.get("local_city")
    cities = []
    if local:
        cities.append({**local, "local": True})
    else:
        cities.append({"city": "Set current location", "zh": "设置当前位置", "local": True, "unset": True})
    local_name = local["city"].split(",")[0].strip().lower() if local else ""
    cities.extend(
        {**item, "local": False}
        for item in settings.get("favorites", [])
        if item.get("city", "").split(",")[0].strip().lower() != local_name
    )
    return cities
