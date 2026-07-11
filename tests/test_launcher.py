from types import SimpleNamespace

from voice_weather import launcher


def test_interactive_macos_opens_window(monkeypatch):
    monkeypatch.setattr("sys.argv", ["voice-weather"])
    monkeypatch.setattr(launcher.platform, "system", lambda: "Darwin")
    captured = {}

    def fake_run(args, check):
        captured["args"] = args
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)
    assert launcher.main() == 0
    assert captured["args"][0] == "osascript"
    assert "clear; exec" in captured["args"][-1]


def test_arguments_stay_in_current_terminal(monkeypatch):
    monkeypatch.setattr("sys.argv", ["voice-weather", "--version"])
    monkeypatch.setattr(launcher, "app_main", lambda: 7)
    assert launcher.main() == 7


def test_non_macos_uses_cli(monkeypatch):
    monkeypatch.setattr("sys.argv", ["voice-weather"])
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    monkeypatch.setattr(launcher, "app_main", lambda: 0)
    assert launcher.main() == 0
