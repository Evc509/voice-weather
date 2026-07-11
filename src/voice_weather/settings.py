import json
from copy import deepcopy
from pathlib import Path

from .config import APP_DIR, CITIES_FILE, DEFAULT_CITIES

SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULT_SETTINGS = {
    "version": 2,
    "language": "zh",
    "voice_enabled": True,
    "location_consent_asked": False,
    "local_city": None,
    "favorites": DEFAULT_CITIES[1:],
}


def load_settings(path: Path = SETTINGS_FILE, legacy_path: Path = CITIES_FILE) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") == 2 and isinstance(data.get("favorites"), list):
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
