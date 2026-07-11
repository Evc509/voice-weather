import json
from pathlib import Path

from .config import CITIES_FILE, DEFAULT_CITIES


def load_cities(path: Path = CITIES_FILE) -> list[dict[str, str]]:
    if not path.exists():
        save_cities(DEFAULT_CITIES, path)
        return [item.copy() for item in DEFAULT_CITIES]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(
            isinstance(x, dict) and x.get("city") and x.get("zh") for x in data
        ):
            raise ValueError("invalid city configuration")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"无法读取城市配置 {path}: {exc}") from exc


def save_cities(cities: list[dict[str, str]], path: Path = CITIES_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

