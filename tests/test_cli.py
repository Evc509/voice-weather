import pytest

from voice_weather import app
from voice_weather.settings import DEFAULT_SETTINGS
from voice_weather.weather import ForecastDay


def settings(local=None, language="zh"):
    return {
        **DEFAULT_SETTINGS,
        "language": language,
        "location_consent_asked": True,
        "local_city": local,
        "favorites": [{"city": "Toronto", "zh": "多伦多"}],
    }


def test_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["voice-weather", "--version"])
    with pytest.raises(SystemExit) as exc:
        app.main()
    assert exc.value.code == 0
    assert "voice-weather 2.0.1" in capsys.readouterr().out


def test_local_city_is_first(monkeypatch, capsys):
    local = {"city": "Ottawa, Ontario, Canada", "zh": "Ottawa"}
    monkeypatch.setattr("builtins.input", lambda prompt="": "0")
    assert app.choose_city(settings(local)) is None
    output = capsys.readouterr().out
    assert "Ottawa" in output
    assert output.index("Ottawa") < output.index("多伦多")


def test_unset_location_still_reserves_first_slot(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "0")
    app.choose_city(settings())
    assert "设置当前位置" in capsys.readouterr().out


def test_manual_city(monkeypatch):
    answers = iter(["m", "Paris, France"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert app.choose_city(settings()) == ("Paris, France", "Paris, France")


def test_forecast_command(monkeypatch):
    monkeypatch.setattr("sys.argv", ["voice-weather", "--city", "Toronto", "--forecast", "--days", "7", "--language", "fr"])
    monkeypatch.setattr(app, "fetch_forecast", lambda city, days: [ForecastDay("2026-07-10", "18", "27", "Clear", "35")])
    assert app.main() == 0


def test_all_languages_build_native_scripts():
    weather = app.Weather("20", "19", "0", "55", "12", "1013", "Clear", "10:00")
    for language in ("zh", "en", "fr", "es", "ja"):
        assert "20" in app.build_script("Toronto", "多伦多", weather, language)


def test_forecast_summary_supports_all_languages():
    forecast = [ForecastDay("2026-07-10", "18", "27", "Clear", "35")]
    for language in ("zh", "en", "fr", "es", "ja"):
        summary = app.forecast_summary("Toronto", forecast, language)
        assert "27" in summary and "35" in summary


def test_keyboard_interrupt_is_clean(monkeypatch):
    monkeypatch.setattr("sys.argv", ["voice-weather"])
    monkeypatch.setattr(app, "interactive", lambda: (_ for _ in ()).throw(KeyboardInterrupt))
    assert app.main() == 130
