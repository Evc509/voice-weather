from voice_weather.advice import weather_advice
from voice_weather.weather import Weather


def weather(temp="20", rain="0", wind="10"):
    return Weather(temp, temp, rain, "50", wind, "1013", "Clear", "10:00")


def test_rain_advice_is_localized():
    assert "雨具" in weather_advice(weather(rain="1"), "zh")[0]
    assert "umbrella" in weather_advice(weather(rain="1"), "en")[0]


def test_temperature_and_wind_advice():
    assert len(weather_advice(weather(temp="35", wind="40"), "en")) == 2
