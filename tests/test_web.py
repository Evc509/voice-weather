import json
import threading
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import pytest

from voice_weather import web
from voice_weather.weather import Weather


def run_server(monkeypatch):
    monkeypatch.setattr(web, "load_settings", lambda: {
        "language": "en", "voice_enabled": True,
        "local_city": {"city": "Toronto", "zh": "多伦多"},
        "favorites": [],
    })
    monkeypatch.setattr(web, "voice_for", lambda language: "Samantha")
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://{web.HOST}:{server.server_port}"


def test_home_page(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        body = urlopen(base, timeout=2).read().decode()
        assert "Voice Weather" in body
        assert "/static/app.js?v=320-final" in body
    finally:
        server.shutdown()


def test_static_assets_disable_browser_cache(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        response = urlopen(base + "/static/app.js?v=320-final", timeout=2)
        assert response.headers["Cache-Control"] == "no-store"
    finally:
        server.shutdown()


def test_frontend_guards_weather_and_speech_against_stale_city_requests():
    script = web.STATIC_ROOT.joinpath("app.js").read_text(encoding="utf-8")
    assert "activeController.abort()" in script
    assert "currentSnapshot=null" in script
    assert "requestNumber!==loadNumber" in script
    assert "snapshot.city!==currentCity" in script


def test_state_api(monkeypatch):
    server, base = run_server(monkeypatch)
    try:
        data = json.loads(urlopen(base + "/api/state", timeout=2).read())
        assert data["version"] == "3.2.0"
        assert data["cities"][0]["city"] == "Toronto"
        assert data["voice"] == "Samantha"
        assert data["max_favorites"] == 20
    finally:
        server.shutdown()


def test_server_is_localhost_only():
    assert web.HOST == "127.0.0.1"


def test_created_server_uses_literal_localhost_name():
    server = web.create_server(0)
    try:
        assert isinstance(server, web.LocalThreadingHTTPServer)
        assert server.server_name == web.HOST
    finally:
        server.server_close()


def test_city_add_api(monkeypatch):
    settings = {"version": 5, "language": "en", "voice_enabled": True, "local_city": None, "favorites": []}
    monkeypatch.setattr(web, "load_settings", lambda: settings)
    monkeypatch.setattr(web, "save_settings", lambda data: None)
    monkeypatch.setattr(web, "city_metadata", lambda location_id: {
        "city": "Paris, Île-de-France, France",
        "labels": {"zh": "巴黎", "en": "Paris", "fr": "Paris", "es": "París", "ja": "パリ"},
        "latitude": 48.85,
        "longitude": 2.35,
        "location_id": location_id,
    })
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = json.dumps({"action": "add", "location_id": 2988507}).encode()
        request = Request(f"http://{web.HOST}:{server.server_port}/api/cities", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        data = json.loads(urlopen(request, timeout=2).read())
        assert data["favorites"][0]["city"] == "Paris, Île-de-France, France"
        assert data["favorites"][0]["labels"]["fr"] == "Paris"
        assert data["favorites"][0]["location_id"] == 2988507
    finally:
        server.shutdown()


def test_web_speech_uses_selected_language(monkeypatch):
    sample = Weather("20", "19", "0", "55", "12", "1013", "Clear", "10:00")
    monkeypatch.setattr(web, "fetch_weather", lambda city: sample)
    text = web.build_web_speech("Paris, France", "Paris", "fr")
    assert "Météo à Paris" in text
    assert "degrés Celsius" in text


def test_web_speech_uses_displayed_snapshot_without_refetching(monkeypatch):
    sample = Weather("11", "9", "0", "62", "15", "1009", "Partly cloudy", "10:30")
    monkeypatch.setattr(web, "fetch_weather", lambda city: (_ for _ in ()).throw(AssertionError("refetched")))
    text = web.build_web_speech("Waterloo, Ontario, Canada", "滑铁卢", "zh", sample)
    assert "滑铁卢当前天气局部多云" in text
    assert "温度摄氏11度" in text


def test_repairs_legacy_localized_city_with_location_id(monkeypatch):
    city = {
        "city": "多伦多, 安大略, 加拿大",
        "labels": {"zh": "多伦多"},
        "latitude": 43.70643,
        "longitude": -79.39864,
    }
    monkeypatch.setattr(web, "search_cities", lambda *args: [{
        "location_id": 6167865, "latitude": 43.70643, "longitude": -79.39864,
    }])
    monkeypatch.setattr(web, "city_metadata", lambda location_id: {
        "city": "Toronto, Ontario, Canada",
        "labels": {"zh": "多伦多", "en": "Toronto", "fr": "Toronto", "es": "Toronto", "ja": "トロント"},
        "latitude": 43.70643,
        "longitude": -79.39864,
        "location_id": location_id,
    })

    assert web.repair_city_entry(city, "zh") is True
    assert city["city"] == "Toronto, Ontario, Canada"
    assert city["labels"]["en"] == "Toronto"


def test_city_add_rejects_duplicate_id_before_metadata_lookup(monkeypatch):
    settings = {"version": 5, "language": "zh", "favorites": [{"city": "Beijing", "location_id": 1816670}]}
    monkeypatch.setattr(web, "load_settings", lambda: settings)
    monkeypatch.setattr(web, "city_metadata", lambda location_id: (_ for _ in ()).throw(AssertionError("unnecessary lookup")))
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = json.dumps({"action": "add", "location_id": 1816670}).encode()
        request = Request(f"http://{web.HOST}:{server.server_port}/api/cities", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with pytest.raises(HTTPError) as exc_info:
            urlopen(request, timeout=2)
        assert exc_info.value.code == 409
        assert "已经" in exc_info.value.read().decode()
    finally:
        server.shutdown()


def test_city_search_marks_same_visible_name_as_already_added(monkeypatch):
    monkeypatch.setattr(web, "load_settings", lambda: {
        "version": 5,
        "language": "zh",
        "favorites": [{"city": "Beijing, China", "labels": {"zh": "北京", "en": "Beijing"}}],
    })
    monkeypatch.setattr(web, "search_cities", lambda *args: [{
        "location_id": 8404324,
        "name": "北京",
        "region": "重庆",
        "country": "中国",
        "latitude": 30.72,
        "longitude": 108.67,
    }])
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        data = json.loads(urlopen(f"http://{web.HOST}:{server.server_port}/api/cities/search?q={quote('北京')}&language=zh", timeout=2).read())
        assert data["results"][0]["duplicate"] is True
        assert data["max_favorites"] == web.MAX_FAVORITES
    finally:
        server.shutdown()


def test_city_search_retries_localized_alias_when_direct_search_is_empty(monkeypatch):
    calls = []

    def fake_search(term, language):
        calls.append((term, language))
        if term == "Tokyo":
            return [{
                "location_id": 1850147, "name": "東京", "region": "東京都", "country": "日本",
                "latitude": 35.6895, "longitude": 139.6917,
            }]
        return []

    monkeypatch.setattr(web, "load_settings", lambda: {"version": 5, "language": "ja", "favorites": []})
    monkeypatch.setattr(web, "search_cities", fake_search)
    monkeypatch.setattr(web, "city_result_by_id", lambda location_id, language: {
        "location_id": location_id, "name": "東京都", "region": "東京都", "country": "日本",
        "latitude": 35.6895, "longitude": 139.6917,
    })
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        data = json.loads(urlopen(f"http://{web.HOST}:{server.server_port}/api/cities/search?q={quote('東京')}&language=ja", timeout=2).read())
        assert calls == [("東京", "ja"), ("Tokyo", "en")]
        assert data["results"][0]["location_id"] == 1850147
    finally:
        server.shutdown()


def test_alias_ranking_removes_wrong_name_and_prefers_region_country():
    results = [
        {"name": "Austin", "region": "Texas", "country": "United States", "canonical": "Austin, Texas, United States"},
        {"name": "Waterloo", "region": "Iowa", "country": "United States", "canonical": "Waterloo, Iowa, United States"},
        {"name": "Waterloo", "region": "Ontario", "country": "Canada", "canonical": "Waterloo, Ontario, Canada"},
    ]
    ranked = web.rank_alias_results(results, "Waterloo, Ontario, Canada")
    assert [item["canonical"] for item in ranked] == [
        "Waterloo, Ontario, Canada",
        "Waterloo, Iowa, United States",
    ]


def test_city_add_rejects_same_visible_name_at_different_coordinates(monkeypatch):
    settings = {"version": 5, "language": "en", "favorites": [{
        "city": "Beijing, Beijing Municipality, China",
        "labels": {"en": "Beijing", "zh": "北京"},
        "latitude": 39.9075,
        "longitude": 116.39723,
    }]}
    monkeypatch.setattr(web, "load_settings", lambda: settings)
    monkeypatch.setattr(web, "city_metadata", lambda location_id: {
        "city": "Beijing, Chongqing Municipality, China",
        "labels": {"en": "Beijing", "zh": "北京", "fr": "Beijing", "es": "Beijing", "ja": "Beijing"},
        "latitude": 30.72608,
        "longitude": 108.67483,
        "location_id": location_id,
    })
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = json.dumps({"action": "add", "location_id": 8404324}).encode()
        request = Request(f"http://{web.HOST}:{server.server_port}/api/cities", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with pytest.raises(HTTPError) as exc_info:
            urlopen(request, timeout=2)
        assert exc_info.value.code == 409
        assert "already" in exc_info.value.read().decode()
    finally:
        server.shutdown()


def test_city_add_enforces_resource_limit_before_metadata_lookup(monkeypatch):
    settings = {
        "version": 5,
        "language": "en",
        "favorites": [{"city": f"City {index}"} for index in range(web.MAX_FAVORITES)],
    }
    monkeypatch.setattr(web, "load_settings", lambda: settings)
    monkeypatch.setattr(web, "city_metadata", lambda location_id: (_ for _ in ()).throw(AssertionError("unnecessary lookup")))
    server = web.ThreadingHTTPServer((web.HOST, 0), web.WebHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = json.dumps({"action": "add", "location_id": 999}).encode()
        request = Request(f"http://{web.HOST}:{server.server_port}/api/cities", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with pytest.raises(HTTPError) as exc_info:
            urlopen(request, timeout=2)
        assert exc_info.value.code == 409
        assert "20" in exc_info.value.read().decode()
    finally:
        server.shutdown()
