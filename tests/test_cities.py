from voice_weather.cities import load_cities, save_cities


def test_city_round_trip(tmp_path):
    path = tmp_path / "cities.json"
    cities = [{"city": "Toronto", "zh": "多伦多"}]
    save_cities(cities, path)
    assert load_cities(path) == cities

