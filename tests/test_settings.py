import json

from voice_weather.config import DEFAULT_CITIES
from voice_weather.settings import MAX_FAVORITES, WORLD_FAVORITES, cities_match, display_cities, load_settings, save_settings


def test_migrates_legacy_cities(tmp_path):
    settings_path = tmp_path / "settings.json"
    legacy_path = tmp_path / "cities.json"
    legacy_path.write_text(json.dumps([{"city": "Paris", "zh": "巴黎"}]), encoding="utf-8")
    data = load_settings(settings_path, legacy_path)
    assert data["version"] == 5
    assert data["favorites"][0]["city"] == "Paris"


def test_settings_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    data = {"version": 5, "language": "ja", "voice_enabled": False, "favorites": []}
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


def test_old_default_list_is_replaced_by_world_regions(tmp_path):
    path = tmp_path / "settings.json"
    save_settings({"version": 2, "language": "zh", "favorites": DEFAULT_CITIES}, path)
    data = load_settings(path, tmp_path / "missing.json")
    assert data["version"] == 5
    assert data["favorites"] == WORLD_FAVORITES


def test_v3_world_cities_gain_all_language_labels(tmp_path):
    path = tmp_path / "settings.json"
    save_settings({"version": 3, "language": "fr", "favorites": [{"city": "London, United Kingdom", "zh": "伦敦"}]}, path)
    data = load_settings(path, tmp_path / "missing.json")
    assert data["version"] == 5
    assert data["favorites"][0]["labels"]["fr"] == "Londres"


def test_corrupt_beijing_country_label_is_repaired(tmp_path):
    path = tmp_path / "settings.json"
    save_settings({"version": 4, "language": "zh", "favorites": [{"city": "北京, 北京市, 中国", "labels": {"zh": "中国"}}]}, path)
    data = load_settings(path, tmp_path / "missing.json")
    assert data["version"] == 5
    assert data["favorites"][0]["labels"]["zh"] == "北京"
    assert data["favorites"][0]["labels"]["fr"] == "Pékin"


def test_same_visible_city_name_is_treated_as_duplicate():
    capital = {"city": "Beijing, China", "labels": {"zh": "北京", "en": "Beijing"}, "latitude": 39.90, "longitude": 116.40}
    namesake = {"city": "Beijing, Chongqing, China", "labels": {"zh": "北京", "en": "Beijing"}, "latitude": 30.72, "longitude": 108.67}
    assert cities_match(capital, namesake)


def test_load_settings_removes_duplicate_names_without_deleting_legacy_cities(tmp_path):
    path = tmp_path / "settings.json"
    favorites = [
        {"city": f"City {index}", "labels": {"en": f"City {index}", "zh": f"城市 {index}"}}
        for index in range(MAX_FAVORITES + 2)
    ]
    favorites.insert(1, {"city": "Other Beijing", "labels": {"en": "City 0", "zh": "另一个北京"}})
    save_settings({"version": 5, "language": "en", "favorites": favorites}, path)

    data = load_settings(path, tmp_path / "missing.json")
    assert len(data["favorites"]) == MAX_FAVORITES + 2
    assert sum(item["labels"]["en"] == "City 0" for item in data["favorites"]) == 1
