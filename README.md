# Voice Weather

A macOS bilingual weather console that fetches current conditions and reads them aloud in Mandarin or English.

## Features

- Mandarin and English speech using the built-in macOS `say` command
- Configurable shortcut cities
- Temperature, feels-like temperature, humidity, precipitation, wind and pressure
- Interactive menu and command-line mode
- Personal configuration and logs stored under `~/.voice-weather/`

## Requirements

- macOS
- Python 3.9 or newer

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/voice-weather.git
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

One-shot mode:

```bash
voice-weather --city "Toronto" --city-zh "多伦多" --language zh
voice-weather --city "Tokyo, Japan" --language en --no-speech
```

You can also run it with `python -m voice_weather`.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## Privacy

City preferences and logs remain outside the repository in `~/.voice-weather/`.

## License

MIT
