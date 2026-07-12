"""PyInstaller entry point for the macOS application bundle."""

from voice_weather.desktop import main


if __name__ == "__main__":
    raise SystemExit(main())
