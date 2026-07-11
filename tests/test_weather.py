from voice_weather.app import build_script
from voice_weather.weather import Weather


SAMPLE = Weather("20", "19", "0", "55", "12", "1013", "Sunny", "10:00")


def test_english_script():
    assert "Weather in Toronto" in build_script("Toronto", "多伦多", SAMPLE, "en")


def test_chinese_script():
    script = build_script("Toronto", "多伦多", SAMPLE, "zh")
    assert "多伦多当前天气" in script
    assert "晴朗" in script
