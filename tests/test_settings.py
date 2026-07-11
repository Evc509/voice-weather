import json

from voice_weather.settings import display_cities, load_settings, save_settings


def test_migrates_legacy_cities(tmp_path):
    settings_path = tmp_path / "settings.json"
    legacy_path = tmp_path / "cities.json"
    legacy_path.write_text(json.dumps([{"city": "Paris", "zh": "巴黎"}]), encoding="utf-8")
    data = load_settings(settings_path, legacy_path)
    assert data["version"] == 2
    assert data["favorites"][0]["city"] == "Paris"


def test_settings_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    data = {"version": 2, "language": "ja", "voice_enabled": False, "favorites": []}
    save_settings(data, path)
    assert load_settings(path, tmp_path / "missing.json")["language"] == "ja"


def test_local_location_is_always_first():
    data = {"local_city": {"city": "Tokyo", "zh": "东京"}, "favorites": [{"city": "Paris", "zh": "巴黎"}]}
    cities = display_cities(data)
    assert cities[0]["city"] == "Tokyo"
    assert cities[0]["local"] is True


def test_local_city_is_removed_from_duplicate_favorites():
    data = {"local_city": {"city": "Waterloo, Ontario, Canada", "zh": "Waterloo"}, "favorites": [{"city": "Waterloo", "zh": "滑铁卢"}, {"city": "Toronto", "zh": "多伦多"}]}
    assert [item["city"] for item in display_cities(data)] == ["Waterloo, Ontario, Canada", "Toronto"]
