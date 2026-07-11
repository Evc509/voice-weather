from voice_weather.cities import load_cities, reset_cities, save_cities
from voice_weather.config import DEFAULT_CITIES


def test_city_round_trip(tmp_path):
    path = tmp_path / "cities.json"
    cities = [{"city": "Toronto", "zh": "多伦多"}]
    save_cities(cities, path)
    assert load_cities(path) == cities


def test_invalid_config_is_backed_up_and_recovered(tmp_path):
    path = tmp_path / "cities.json"
    path.write_text("not-json", encoding="utf-8")
    assert load_cities(path) == DEFAULT_CITIES
    assert list(tmp_path.glob("cities.invalid-*.json"))


def test_reset_cities_restores_defaults(tmp_path):
    path = tmp_path / "cities.json"
    save_cities([{"city": "Paris", "zh": "巴黎"}], path)
    assert reset_cities(path) == DEFAULT_CITIES
    assert load_cities(path) == DEFAULT_CITIES
