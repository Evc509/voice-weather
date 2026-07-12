import pytest

from voice_weather import desktop


class FakeServer:
    server_port = 54321

    def __init__(self):
        self.served = False
        self.shutdown_called = False
        self.closed = False

    def serve_forever(self):
        self.served = True

    def shutdown(self):
        self.shutdown_called = True

    def server_close(self):
        self.closed = True


class FakeWebview:
    def __init__(self):
        self.window_args = None
        self.start_args = None

    def create_window(self, *args, **kwargs):
        self.window_args = (args, kwargs)

    def start(self, **kwargs):
        self.start_args = kwargs


def test_desktop_window_owns_server_lifecycle(monkeypatch, tmp_path):
    server = FakeServer()
    fake_webview = FakeWebview()
    monkeypatch.setattr(desktop, "create_server", lambda port: server)
    monkeypatch.setattr(desktop, "APP_DIR", tmp_path)
    monkeypatch.setattr(desktop, "stop_speech", lambda: None)

    assert desktop.run_desktop(fake_webview) == 0
    assert server.served
    assert server.shutdown_called
    assert server.closed
    assert fake_webview.window_args[0][1] == "http://127.0.0.1:54321"
    assert fake_webview.start_args["gui"] == "cocoa"
    assert fake_webview.start_args["private_mode"] is False


def test_desktop_cleanup_runs_when_window_creation_fails(monkeypatch, tmp_path):
    server = FakeServer()
    fake_webview = FakeWebview()
    fake_webview.create_window = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("window failed"))
    monkeypatch.setattr(desktop, "create_server", lambda port: server)
    monkeypatch.setattr(desktop, "APP_DIR", tmp_path)
    monkeypatch.setattr(desktop, "stop_speech", lambda: None)

    with pytest.raises(RuntimeError, match="window failed"):
        desktop.run_desktop(fake_webview)

    assert server.shutdown_called
    assert server.closed
