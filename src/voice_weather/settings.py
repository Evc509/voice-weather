import json
from copy import deepcopy
from pathlib import Path
from unicodedata import combining, normalize

from .config import APP_DIR, CITIES_FILE, DEFAULT_CITIES

SETTINGS_FILE = APP_DIR / "settings.json"
MAX_FAVORITES = 20
EXTRA_SEARCH_ALIASES = {
    "滑铁卢": "Waterloo, Ontario, Canada", "滑鐵盧": "Waterloo, Ontario, Canada",
    "東京": "Tokyo, Japan", "大阪": "Osaka, Japan", "京都": "Kyoto, Japan", "横浜": "Yokohama, Japan",
    "名古屋": "Nagoya, Japan", "札幌": "Sapporo, Japan", "福岡": "Fukuoka, Japan", "広島": "Hiroshima, Japan",
    "神戸": "Kobe, Japan", "仙台": "Sendai, Japan", "那覇": "Naha, Japan",
    "上海": "Shanghai, China", "广州": "Guangzhou, China", "廣州": "Guangzhou, China", "深圳": "Shenzhen, China",
    "成都": "Chengdu, China", "杭州": "Hangzhou, China", "南京": "Nanjing, China", "武汉": "Wuhan, China",
    "武漢": "Wuhan, China", "西安": "Xi'an, China", "苏州": "Suzhou, China", "蘇州": "Suzhou, China",
}
WORLD_FAVORITES = [
    {"city":"Toronto, Canada","zh":"多伦多","labels":{"zh":"多伦多","en":"Toronto","fr":"Toronto","es":"Toronto","ja":"トロント"}},
    {"city":"Vancouver, Canada","zh":"温哥华","labels":{"zh":"温哥华","en":"Vancouver","fr":"Vancouver","es":"Vancouver","ja":"バンクーバー"}},
    {"city":"New York, United States","zh":"纽约","labels":{"zh":"纽约","en":"New York","fr":"New York","es":"Nueva York","ja":"ニューヨーク"}},
    {"city":"Mexico City, Mexico","zh":"墨西哥城","labels":{"zh":"墨西哥城","en":"Mexico City","fr":"Mexico","es":"Ciudad de México","ja":"メキシコシティ"}},
    {"city":"São Paulo, Brazil","zh":"圣保罗","labels":{"zh":"圣保罗","en":"São Paulo","fr":"São Paulo","es":"São Paulo","ja":"サンパウロ"}},
    {"city":"London, United Kingdom","zh":"伦敦","labels":{"zh":"伦敦","en":"London","fr":"Londres","es":"Londres","ja":"ロンドン"}},
    {"city":"Paris, France","zh":"巴黎","labels":{"zh":"巴黎","en":"Paris","fr":"Paris","es":"París","ja":"パリ"}},
    {"city":"Cairo, Egypt","zh":"开罗","labels":{"zh":"开罗","en":"Cairo","fr":"Le Caire","es":"El Cairo","ja":"カイロ"}},
    {"city":"Dubai, United Arab Emirates","zh":"迪拜","labels":{"zh":"迪拜","en":"Dubai","fr":"Dubaï","es":"Dubái","ja":"ドバイ"}},
    {"city":"Mumbai, India","zh":"孟买","labels":{"zh":"孟买","en":"Mumbai","fr":"Mumbai","es":"Bombay","ja":"ムンバイ"}},
    {"city":"Singapore","zh":"新加坡","labels":{"zh":"新加坡","en":"Singapore","fr":"Singapour","es":"Singapur","ja":"シンガポール"}},
    {"city":"Beijing, China","zh":"北京","labels":{"zh":"北京","en":"Beijing","fr":"Pékin","es":"Pekín","ja":"北京"}},
    {"city":"Tokyo, Japan","zh":"东京","labels":{"zh":"东京","en":"Tokyo","fr":"Tokyo","es":"Tokio","ja":"東京"}},
    {"city":"Sydney, Australia","zh":"悉尼","labels":{"zh":"悉尼","en":"Sydney","fr":"Sydney","es":"Sídney","ja":"シドニー"}},
]
DEFAULT_SETTINGS = {
    "version": 5,
    "language": "zh",
    "voice_enabled": True,
    "location_consent_asked": False,
    "local_city": None,
    "favorites": WORLD_FAVORITES,
}


def _city_name_keys(city: dict) -> set[str]:
    labels = city.get("labels") if isinstance(city.get("labels"), dict) else {}
    names = [labels.get("en"), labels.get("zh")]
    if not any(names):
        names.extend((city.get("zh"), city.get("city", "").split(",")[0]))
    return {str(name).strip().casefold() for name in names if str(name or "").strip()}


def cities_match(first: dict, second: dict) -> bool:
    """Return True when two records would represent the same visible shortcut."""
    first_id, second_id = first.get("location_id"), second.get("location_id")
    if first_id is not None and second_id is not None and first_id == second_id:
        return True
    try:
        distance = abs(float(first["latitude"]) - float(second["latitude"])) + abs(
            float(first["longitude"]) - float(second["longitude"])
        )
        if distance <= 0.03:
            return True
    except (KeyError, TypeError, ValueError):
        pass
    return bool(_city_name_keys(first) & _city_name_keys(second))


def deduplicate_favorites(favorites: list[dict]) -> list[dict]:
    unique = []
    for city in favorites:
        if isinstance(city, dict) and not any(cities_match(city, existing) for existing in unique):
            unique.append(city)
    return unique


def _alias_key(value: str) -> str:
    decomposed = normalize("NFKD", str(value or "").strip().casefold())
    return "".join(character for character in decomposed if not combining(character) and character.isalnum())


def resolve_city_query(query: str, settings: dict) -> str:
    """Resolve supported localized input to a stable search term without another service."""
    target = _alias_key(query)
    records = []
    if isinstance(settings.get("local_city"), dict):
        records.append(settings["local_city"])
    records.extend(item for item in settings.get("favorites", []) if isinstance(item, dict))
    for alias, canonical in EXTRA_SEARCH_ALIASES.items():
        if _alias_key(alias) == target:
            return canonical
    records.extend((*WORLD_FAVORITES, *DEFAULT_CITIES))
    for record in records:
        canonical = str(record.get("city", "")).strip()
        labels = record.get("labels") if isinstance(record.get("labels"), dict) else {}
        names = [canonical, record.get("zh"), *labels.values()]
        if canonical and any(_alias_key(name) == target for name in names if name):
            return canonical
    return query.strip()


def load_settings(path: Path = SETTINGS_FILE, legacy_path: Path = CITIES_FILE) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") in {2, 3, 4, 5} and isinstance(data.get("favorites"), list):
                if data.get("version") == 2:
                    legacy_names = {item["city"].split(",")[0].strip().lower() for item in DEFAULT_CITIES}
                    current_names = {item.get("city", "").split(",")[0].strip().lower() for item in data["favorites"]}
                    if len(current_names) >= 5 and current_names.issubset(legacy_names):
                        data["favorites"] = deepcopy(WORLD_FAVORITES)
                    data["version"] = 3
                if data.get("version") == 3:
                    world_by_city = {item["city"].casefold(): item for item in WORLD_FAVORITES}
                    data["favorites"] = [deepcopy(world_by_city.get(item.get("city", "").casefold(), item)) for item in data["favorites"]]
                    data["version"] = 4
                if data.get("version") == 4:
                    beijing = next(item for item in WORLD_FAVORITES if item["city"].startswith("Beijing,"))
                    data["favorites"] = [deepcopy(beijing) if item.get("city", "").split(",")[0].strip() == "北京" else item for item in data["favorites"]]
                    data["version"] = 5
                data["favorites"] = deduplicate_favorites(data["favorites"])
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
    cities.extend(
        {**item, "local": False}
        for item in settings.get("favorites", [])
        if not local or not cities_match(local, item)
    )
    return cities
