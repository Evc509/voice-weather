import argparse
from datetime import datetime
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .advice import weather_advice
from .config import LOG_FILE
from .i18n import LANGUAGES, tr, weather_text
from .location import LocationError, detect_location
from .settings import display_cities, load_settings, save_settings
from .speech import SpeechError, speak, voice_for
from .weather import ForecastDay, Weather, WeatherError, fetch_forecast, fetch_weather

console = Console()


def build_script(city: str, city_zh: str, weather: Weather, language: str) -> str:
    description = weather_text(language, weather.description)
    values = (city_zh if language == "zh" else city, description, weather.temperature_c, weather.feels_like_c, weather.humidity, weather.wind_kph, weather.pressure_hpa)
    templates = {
        "zh": "{}当前天气{}，温度摄氏{}度，体感{}度，湿度百分之{}，风速每小时{}公里，气压{}百帕。",
        "en": "Weather in {}: {}. Temperature {} degrees Celsius, feels like {}, humidity {} percent, wind {} kilometers per hour, pressure {} hectopascals.",
        "fr": "Météo à {} : {}. Température {} degrés Celsius, ressenti {}, humidité {} pour cent, vent {} kilomètres par heure, pression {} hectopascals.",
        "es": "Tiempo en {}: {}. Temperatura {} grados Celsius, sensación {}, humedad {} por ciento, viento {} kilómetros por hora, presión {} hectopascales.",
        "ja": "{}の天気は{}。気温{}度、体感温度{}度、湿度{}パーセント、風速は時速{}キロ、気圧{}ヘクトパスカルです。",
    }
    return templates.get(language, templates["en"]).format(*values)


def log_script(text: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {text}\n")


def menu_title(settings: dict) -> None:
    language = settings["language"]
    location = settings.get("local_city")
    subtitle = location["city"] if location else tr(language, "location_off")
    console.print(Panel.fit(f"[bold cyan]🌤 Voice Weather v{__version__}[/]\n{tr(language, 'title')}\n[dim]📍 {subtitle} · {LANGUAGES[language]}[/]", border_style="cyan"))


def show_cities(settings: dict) -> list[dict]:
    language = settings["language"]
    cities = display_cities(settings)
    table = Table(title=tr(language, "select_city"), border_style="blue")
    table.add_column("#", justify="right", style="cyan")
    table.add_column(tr(language, "cities"))
    for index, city in enumerate(cities, 1):
        marker = "📍 " if city.get("local") else "⭐ "
        label = city.get("zh") if language == "zh" and city.get("zh") else city["city"]
        table.add_row(str(index), marker + label)
    console.print(table)
    return cities


def choose_city(settings: dict) -> Optional[Tuple[str, str]]:
    language = settings["language"]
    cities = show_cities(settings)
    console.print(f"[M] {tr(language, 'manual')}   [0] {tr(language, 'back')}")
    raw = input(f"{tr(language, 'choose')}: ").strip().lower()
    if raw == "0":
        return None
    if raw == "m":
        city = input(f"{tr(language, 'city_prompt')}: ").strip()
        return (city, city) if city else None
    if raw.isdigit() and 1 <= int(raw) <= len(cities):
        selected = cities[int(raw) - 1]
        if selected.get("unset"):
            console.print(f"[yellow]{tr(language, 'location_off')}[/]")
            return None
        return selected["city"], selected.get("zh", selected["city"])
    console.print(f"[red]{tr(language, 'invalid')}[/]")
    return None


def print_current(city: str, weather: Weather, language: str) -> None:
    table = Table(title=f"🌤 {city}", border_style="green", show_header=False)
    table.add_column(style="bold")
    table.add_column(justify="right")
    table.add_row(tr(language, "conditions"), weather_text(language, weather.description))
    table.add_row(tr(language, "temperature"), f"{weather.temperature_c} °C")
    table.add_row(tr(language, "feels"), f"{weather.feels_like_c} °C")
    table.add_row(tr(language, "humidity"), f"{weather.humidity}%")
    table.add_row(tr(language, "wind"), f"{weather.wind_kph} km/h")
    table.add_row(tr(language, "pressure"), f"{weather.pressure_hpa} hPa")
    console.print(table)


def print_forecast(city: str, forecast: list[ForecastDay], language: str) -> None:
    table = Table(title=f"📅 {city} · {len(forecast)} days", border_style="magenta")
    table.add_column(tr(language, "date"))
    table.add_column(tr(language, "low_high"), justify="right")
    table.add_column(tr(language, "rain"), justify="right")
    table.add_column(tr(language, "conditions"))
    for day in forecast:
        table.add_row(day.date, f"{day.min_c}° / {day.max_c}°", f"{day.rain_chance}%", weather_text(language, day.description))
    console.print(table)


def forecast_summary(city: str, forecast: list[ForecastDay], language: str) -> str:
    hottest = max(int(day.max_c) for day in forecast)
    wettest = max(int(day.rain_chance) for day in forecast)
    templates = {
        "zh": "{}未来{}天最高温度{}度，最大降雨概率百分之{}。",
        "en": "The next {} days in {} will reach {} degrees, with a maximum rain chance of {} percent.",
        "fr": "Les {} prochains jours à {} atteindront {} degrés, avec un risque maximal de pluie de {} pour cent.",
        "es": "Los próximos {} días en {} alcanzarán {} grados, con una probabilidad máxima de lluvia del {} por ciento.",
        "ja": "{}の今後{}日間の最高気温は{}度、最大降水確率は{}パーセントです。",
    }
    if language in {"zh", "ja"}:
        return templates[language].format(city, len(forecast), hottest, wettest)
    return templates.get(language, templates["en"]).format(len(forecast), city, hottest, wettest)


def run(city: str, city_zh: str, language: str, no_speech: bool = False, voice_enabled: bool = True) -> int:
    try:
        weather = fetch_weather(city)
        print_current(city, weather, language)
        script = build_script(city, city_zh, weather, language)
        console.print(Panel(script, title="🔊", border_style="green"))
        advice = weather_advice(weather, language)
        if advice:
            console.print(Panel("\n".join(f"• {item}" for item in advice), title="💡", border_style="yellow"))
            script = f"{script} {' '.join(advice)}"
        if voice_enabled and not no_speech:
            speak(script, language)
        log_script(script)
        return 0
    except (WeatherError, SpeechError) as exc:
        console.print(f"[red]❌ {exc}[/]")
        return 1


def select_language(settings: dict) -> None:
    for index, (code, name) in enumerate(LANGUAGES.items(), 1):
        voice = voice_for(code) or "text only"
        console.print(f"[{index}] {name} [dim]({voice})[/]")
    raw = input("Language: ").strip()
    codes = list(LANGUAGES)
    if raw.isdigit() and 1 <= int(raw) <= len(codes):
        settings["language"] = codes[int(raw) - 1]
        save_settings(settings)


def refresh_location(settings: dict) -> None:
    language = settings["language"]
    consent = input(f"{tr(language, 'location_consent')} [y/N]: ").strip().lower()
    settings["location_consent_asked"] = True
    if consent == "y":
        try:
            settings["local_city"] = detect_location()
            console.print(f"[green]📍 {settings['local_city']['city']}[/]")
        except LocationError as exc:
            console.print(f"[red]{exc}[/]")
    save_settings(settings)


def settings_menu(settings: dict) -> None:
    language = settings["language"]
    console.print(f"[1] {tr(language, 'change_language')}\n[2] {tr(language, 'toggle_voice')}\n[3] {tr(language, 'refresh_location')}\n[0] {tr(language, 'back')}")
    raw = input(f"{tr(language, 'choose')}: ").strip()
    if raw == "1":
        select_language(settings)
    elif raw == "2":
        settings["voice_enabled"] = not settings.get("voice_enabled", True)
        save_settings(settings)
    elif raw == "3":
        refresh_location(settings)


def manage_favorites(settings: dict) -> None:
    language = settings["language"]
    favorites = settings.get("favorites", [])
    table = Table(title=tr(language, "favorites"), border_style="blue")
    table.add_column("#", justify="right")
    table.add_column(tr(language, "cities"))
    for index, city in enumerate(favorites, 1):
        table.add_row(str(index), city["city"])
    console.print(table)
    console.print(f"[A] {tr(language, 'add')}   [D] {tr(language, 'delete')}   [0] {tr(language, 'back')}")
    raw = input(f"{tr(language, 'choose')}: ").strip().lower()
    if raw == "a":
        city = input(f"{tr(language, 'city_prompt')}: ").strip()
        if city and all(item.get("city", "").lower() != city.lower() for item in favorites):
            favorites.append({"city": city, "zh": city})
            save_settings(settings)
    elif raw == "d":
        number = input("#: ").strip()
        if number.isdigit() and 1 <= int(number) <= len(favorites):
            favorites.pop(int(number) - 1)
            save_settings(settings)


def interactive() -> int:
    settings = load_settings()
    if not settings.get("location_consent_asked"):
        refresh_location(settings)
    while True:
        language = settings["language"]
        menu_title(settings)
        console.print(f"[1] 🎙️ {tr(language, 'current')}\n[2] 📅 {tr(language, 'forecast')}\n[3] 🏙️ {tr(language, 'cities')}\n[4] 🌐 {tr(language, 'language')}\n[5] ⚙️ {tr(language, 'settings')}\n[0] {tr(language, 'quit')}")
        choice = input(f"{tr(language, 'choose')}: ").strip()
        if choice == "0":
            console.print(tr(language, "goodbye"))
            return 0
        if choice == "1":
            selected = choose_city(settings)
            if selected:
                run(*selected, language, voice_enabled=settings.get("voice_enabled", True))
        elif choice == "2":
            selected = choose_city(settings)
            if selected:
                raw_days = input(f"{tr(language, 'days')} [7]: ").strip() or "7"
                if raw_days.isdigit() and 1 <= int(raw_days) <= 7:
                    forecast = fetch_forecast(selected[0], int(raw_days))
                    print_forecast(selected[0], forecast, language)
                    summary = forecast_summary(selected[0], forecast, language)
                    console.print(Panel(summary, title="🔊", border_style="green"))
                    if settings.get("voice_enabled", True):
                        try:
                            speak(summary, language)
                        except SpeechError as exc:
                            console.print(f"[yellow]{exc}[/]")
        elif choice == "3":
            manage_favorites(settings)
        elif choice == "4":
            select_language(settings)
        elif choice == "5":
            settings_menu(settings)
        else:
            console.print(f"[red]{tr(language, 'invalid')}[/]")


def main() -> int:
    parser = argparse.ArgumentParser(description="Multilingual voice weather for macOS")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--city")
    parser.add_argument("--city-zh")
    parser.add_argument("--language", choices=list(LANGUAGES), default="zh")
    parser.add_argument("--no-speech", action="store_true")
    parser.add_argument("--list-cities", action="store_true")
    parser.add_argument("--forecast", action="store_true")
    parser.add_argument("--days", type=int, choices=range(1, 8), default=7)
    args = parser.parse_args()
    try:
        if args.list_cities:
            settings = load_settings()
            for index, city in enumerate(display_cities(settings), 1):
                print(f"{index}. {city['city']}")
            return 0
        if args.forecast:
            if not args.city:
                parser.error("--forecast requires --city")
            print_forecast(args.city, fetch_forecast(args.city, args.days), args.language)
            return 0
        if args.city:
            return run(args.city, args.city_zh or args.city, args.language, args.no_speech)
        return interactive()
    except (KeyboardInterrupt, EOFError):
        console.print("\nBye.")
        return 130
    except WeatherError as exc:
        console.print(f"[red]❌ {exc}[/]")
        return 1
