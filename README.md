# Voice Weather

[![Tests](https://github.com/Evc509/voice-weather/actions/workflows/tests.yml/badge.svg)](https://github.com/Evc509/voice-weather/actions/workflows/tests.yml)

A friendly multilingual macOS weather console with current conditions, seven-day forecasts and native voice playback.

## Features

- Chinese, English, French, Spanish and Japanese text and speech
- Automatic selection from installed macOS `say` voices
- Rich color panels and aligned weather tables
- Optional city-level IP location in the first shortcut position
- Configurable shortcut cities
- Temperature, feels-like temperature, humidity, precipitation, wind and pressure
- Bilingual 1–7 day forecasts with daily highs, lows and rain probability
- Interactive menu and command-line mode
- Personal configuration and logs stored under `~/.voice-weather/`

## Requirements

- macOS
- Python 3.9 or newer

## Installation

```bash
git clone https://github.com/Evc509/voice-weather.git
cd voice-weather
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Usage

Interactive mode:

```bash
voice-weather
```

The numbered interactive menu separates current weather, forecasts, city management and city listing. Every city-selection screen starts at `[1]`, supports manual entry, and provides a clear return option.

One-shot mode:

```bash
voice-weather --city "Toronto" --city-zh "多伦多" --language zh
voice-weather --city "Tokyo, Japan" --language en --no-speech
```

Forecast mode:

```bash
voice-weather --city "Toronto" --forecast --days 7 --language zh
voice-weather --city "Tokyo, Japan" --forecast --days 7 --language en
```

Forecasts default to seven days. Current conditions and forecasts are provided by [Open-Meteo](https://open-meteo.com/).

Supported interface and announcement languages are `zh`, `en`, `fr`, `es`, and `ja`. The interactive language screen shows the matching voice installed on the current Mac; if no suitable voice is installed, weather text remains available.

Inspect the installation and configured shortcuts:

```bash
voice-weather --version
voice-weather --list-cities
```

You can also run it with `python -m voice_weather`.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

Every push and pull request is also tested automatically on Python 3.9–3.12 with GitHub Actions.

## Privacy

City preferences and logs remain outside the repository in `~/.voice-weather/`. On first launch, location lookup is opt-in; if approved, wttr.in receives your network request and returns only city-level IP location data. You can decline and use manual cities instead.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

MIT
