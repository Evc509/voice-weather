import pytest

from voice_weather import app
from voice_weather.weather import ForecastDay


def test_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["voice-weather", "--version"])
    with pytest.raises(SystemExit) as exc:
        app.main()
    assert exc.value.code == 0
    assert "voice-weather 0.2.0" in capsys.readouterr().out


def test_list_cities(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["voice-weather", "--list-cities"])
    monkeypatch.setattr(app, "load_cities", lambda: [{"city": "Toronto", "zh": "多伦多"}])
    assert app.main() == 0
    assert "Toronto (多伦多)" in capsys.readouterr().out


def test_keyboard_interrupt_is_clean(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["voice-weather"])
    monkeypatch.setattr(app, "interactive", lambda: (_ for _ in ()).throw(KeyboardInterrupt))
    assert app.main() == 130
    assert "已退出" in capsys.readouterr().out


def test_forecast_command(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["voice-weather", "--city", "Toronto", "--forecast", "--days", "7"])
    monkeypatch.setattr(
        app,
        "fetch_forecast",
        lambda city, days: [ForecastDay("2026-07-10", "18", "27", "Clear", "35")],
    )
    assert app.main() == 0
    output = capsys.readouterr().out
    assert "Toronto" in output
    assert "晴朗" in output


def test_interactive_forecast_uses_defaults(monkeypatch, capsys):
    answers = iter(["1", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(
        app,
        "fetch_forecast",
        lambda city, days: [ForecastDay("2026-07-10", "18", "27", "Clear", "35")],
    )
    app.interactive_forecast([{"city": "Toronto", "zh": "多伦多"}])
    output = capsys.readouterr().out
    assert "Toronto 未来 1 天天气预报" in output
    assert "晴朗" in output


def test_interactive_forecast_rejects_bad_days(monkeypatch, capsys):
    answers = iter(["Toronto", "2", "8"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    app.interactive_forecast([])
    assert "天数必须是 1 到 7" in capsys.readouterr().out
