from pathlib import Path

APP_DIR = Path.home() / ".voice-weather"
CITIES_FILE = APP_DIR / "cities.json"
LOG_FILE = APP_DIR / "weather.log"

DEFAULT_CITIES = [
    {"city": "Toronto", "zh": "多伦多"},
    {"city": "Waterloo", "zh": "滑铁卢"},
    {"city": "Windsor", "zh": "温莎"},
    {"city": "New York", "zh": "纽约"},
    {"city": "Tokyo, Japan", "zh": "东京"},
    {"city": "Beijing, China", "zh": "北京"},
    {"city": "Taipei, Taiwan", "zh": "台北"},
]

