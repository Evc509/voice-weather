"""Native desktop window for Voice Weather on macOS."""

import platform
import threading
from pathlib import Path

from .config import APP_DIR
from .speech import stop_speech
from .web import create_server


class DesktopUnavailableError(RuntimeError):
    """Raised when the optional native desktop runtime is unavailable."""


def _load_webview():
    if platform.system() != "Darwin":
        raise DesktopUnavailableError("The Voice Weather desktop app currently supports macOS only.")
    try:
        import webview
    except ImportError as exc:
        raise DesktopUnavailableError(
            'Desktop support is not installed. Run: python3 -m pip install -e ".[desktop]"'
        ) from exc
    return webview


def run_desktop(webview_module=None):
    """Run the web interface in a native window and own the server lifecycle."""
    webview_module = webview_module or _load_webview()
    server = create_server(0)
    server_thread = threading.Thread(
        target=server.serve_forever,
        name="voice-weather-server",
        daemon=True,
    )
    server_thread.start()

    try:
        url = f"http://127.0.0.1:{server.server_port}"
        storage_path = Path(APP_DIR) / "desktop-data"
        storage_path.mkdir(parents=True, exist_ok=True)
        webview_module.create_window(
            "Voice Weather",
            url,
            width=1180,
            height=780,
            min_size=(860, 600),
            resizable=True,
            background_color="#0b1729",
        )
        webview_module.start(
            gui="cocoa",
            private_mode=False,
            storage_path=str(storage_path),
        )
    finally:
        stop_speech()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
    return 0


def main():
    try:
        return run_desktop()
    except DesktopUnavailableError as exc:
        print(f"voice-weather-desktop: {exc}")
        return 1
