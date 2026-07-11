from voice_weather.i18n import LANGUAGES, tr, weather_text


def test_five_languages_are_available():
    assert set(LANGUAGES) == {"zh", "en", "fr", "es", "ja"}


def test_weather_translations():
    assert weather_text("zh", "Clear") == "晴朗"
    assert weather_text("fr", "Clear") == "Dégagé"
    assert weather_text("es", "Clear") == "Despejado"
    assert weather_text("ja", "Clear") == "晴れ"


def test_unknown_key_falls_back_safely():
    assert tr("fr", "temperature")


def test_supported_languages_translate_weather_table_fields():
    for language in ("zh", "en", "fr", "es", "ja"):
        for key in ("temperature", "feels", "humidity", "wind", "pressure", "conditions"):
            assert tr(language, key)
