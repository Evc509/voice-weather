from voice_weather.location import detect_location


class Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"nearest_area": [{
            "areaName": [{"value": "Toronto"}],
            "region": [{"value": "Ontario"}],
            "country": [{"value": "Canada"}],
            "latitude": "43.65",
            "longitude": "-79.38",
        }]}


def test_detect_location(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: Response())
    location = detect_location()
    assert location["city"] == "Toronto, Ontario, Canada"
    assert location["latitude"] == 43.65
