import argparse
from datetime import datetime

from . import __version__
from .cities import load_cities, save_cities
from .config import LOG_FILE
from .speech import SpeechError, speak
from .weather import ForecastDay, Weather, WeatherError, fetch_forecast, fetch_weather

WEATHER_ZH = {
    "sunny": "晴朗",
    "clear": "晴朗",
    "mainly clear": "大致晴朗",
    "partly cloudy": "局部多云",
    "cloudy": "多云",
    "overcast": "阴天",
    "mist": "薄雾",
    "fog": "有雾",
    "light rain": "小雨",
    "moderate rain": "中雨",
    "heavy rain": "大雨",
    "light snow": "小雪",
    "moderate snow": "中雪",
    "heavy snow": "大雪",
    "thundery outbreaks possible": "可能有雷雨",
    "light drizzle": "小毛毛雨",
    "drizzle": "毛毛雨",
    "heavy drizzle": "较强毛毛雨",
    "rime fog": "雾凇",
    "light rain showers": "小阵雨",
    "rain showers": "阵雨",
    "heavy rain showers": "强阵雨",
    "light snow showers": "小阵雪",
    "heavy snow showers": "强阵雪",
    "thunderstorm": "雷暴",
}


def weather_description_zh(description: str) -> str:
    return WEATHER_ZH.get(description.strip().lower(), description)


def build_script(city: str, city_zh: str, weather: Weather, language: str) -> str:
    if language == "zh":
        return (
            f"{city_zh}当前天气为{weather_description_zh(weather.description)}，温度摄氏{weather.temperature_c}度，"
            f"体感{weather.feels_like_c}度，湿度百分之{weather.humidity}，"
            f"降水量{weather.precipitation_mm}毫米，风速每小时{weather.wind_kph}公里，"
            f"气压{weather.pressure_hpa}百帕。"
        )
    return (
        f"Weather in {city}: {weather.description}. Temperature {weather.temperature_c} degrees Celsius, "
        f"feels like {weather.feels_like_c}, humidity {weather.humidity} percent, "
        f"precipitation {weather.precipitation_mm} millimeters, wind {weather.wind_kph} kilometers per hour, "
        f"and pressure {weather.pressure_hpa} hectopascals."
    )


def log_script(text: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {text}\n")


def print_forecast(city: str, forecast: list[ForecastDay], language: str) -> None:
    if language == "zh":
        print(f"\n📅 {city} 未来 {len(forecast)} 天天气预报")
        print("日期         最低/最高   降雨概率  天气")
        for day in forecast:
            description = weather_description_zh(day.description)
            temperatures = f"{day.min_c}°/{day.max_c}°"
            print(f"{day.date}   {temperatures:<10}  {day.rain_chance:>3}%      {description}")
    else:
        print(f"\n📅 {len(forecast)}-day forecast for {city}")
        print("Date         Low/High    Rain   Conditions")
        for day in forecast:
            temperatures = f"{day.min_c}°/{day.max_c}°"
            print(f"{day.date}   {temperatures:<10}  {day.rain_chance:>3}%   {day.description}")


def edit_city(cities: list[dict[str, str]]) -> None:
    raw = input(f"修改编号 (1-{len(cities)}): ").strip()
    if not raw.isdigit() or not 1 <= int(raw) <= len(cities):
        print("❌ 编号无效")
        return
    city = input("英文城市名（可带国家）: ").strip()
    city_zh = input("中文城市名: ").strip()
    if not city or not city_zh:
        print("❌ 城市名不能为空")
        return
    cities[int(raw) - 1] = {"city": city, "zh": city_zh}
    save_cities(cities)
    print("✅ 城市配置已保存")


def interactive() -> int:
    while True:
        cities = load_cities()
        print("\n🎙️ Canada Universal Bilingual Weather Console")
        for index, item in enumerate(cities, 1):
            print(f"{index}. {item['city']} ({item['zh']})")
        print("m. 手动输入   e. 修改城市   q. 退出")
        choice = input("请选择: ").strip().lower()
        if choice == "q":
            return 0
        if choice == "e":
            edit_city(cities)
            continue
        if choice == "m":
            city = input("城市和国家: ").strip()
            if not city:
                print("❌ 城市不能为空")
                continue
            city_zh = input("中文城市名（可留空）: ").strip() or city
        elif choice.isdigit() and 1 <= int(choice) <= len(cities):
            selected = cities[int(choice) - 1]
            city, city_zh = selected["city"], selected["zh"]
        else:
            print("❌ 选择无效")
            continue
        language = input("播报语言 1. 中文  2. English: ").strip()
        if language not in {"1", "2"}:
            print("❌ 语言选择无效")
            continue
        run(city, city_zh, "zh" if language == "1" else "en")


def run(city: str, city_zh: str, language: str, no_speech: bool = False) -> int:
    try:
        weather = fetch_weather(city)
        script = build_script(city, city_zh, weather, language)
        print(f"\n📢 {script}")
        if not no_speech:
            speak(script, language)
        log_script(script)
        return 0
    except (WeatherError, SpeechError) as exc:
        print(f"❌ {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Bilingual voice weather for macOS")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--city", help="City, optionally followed by country")
    parser.add_argument("--city-zh", help="Chinese display name")
    parser.add_argument("--language", choices=["zh", "en"], default="zh")
    parser.add_argument("--no-speech", action="store_true", help="Print without speaking")
    parser.add_argument("--list-cities", action="store_true", help="List configured shortcut cities")
    parser.add_argument("--forecast", action="store_true", help="Show a 1-7 day forecast (requires --city)")
    parser.add_argument("--days", type=int, choices=range(1, 8), default=7, metavar="1-7")
    args = parser.parse_args()
    try:
        if args.list_cities:
            for index, item in enumerate(load_cities(), 1):
                print(f"{index}. {item['city']} ({item['zh']})")
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
        print("\n已退出。")
        return 130
