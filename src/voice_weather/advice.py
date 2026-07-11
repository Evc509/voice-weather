from .weather import Weather

MESSAGES = {
    "zh": {"umbrella": "可能有降水，建议携带雨具。", "cold": "天气较冷，注意保暖。", "hot": "天气炎热，注意补水和防晒。", "wind": "风力较强，外出请注意。"},
    "en": {"umbrella": "Precipitation is possible; consider taking an umbrella.", "cold": "It is cold; dress warmly.", "hot": "It is hot; stay hydrated and use sun protection.", "wind": "Strong wind is possible; take care outdoors."},
    "fr": {"umbrella": "Des précipitations sont possibles ; prévoyez un parapluie.", "cold": "Il fait froid ; couvrez-vous bien.", "hot": "Il fait chaud ; hydratez-vous et protégez-vous du soleil.", "wind": "Le vent est fort ; soyez prudent dehors."},
    "es": {"umbrella": "Puede llover; considere llevar paraguas.", "cold": "Hace frío; abríguese.", "hot": "Hace calor; hidrátese y protéjase del sol.", "wind": "Hay viento fuerte; tenga cuidado al aire libre."},
    "ja": {"umbrella": "降水の可能性があります。傘をお持ちください。", "cold": "寒いため、暖かい服装をしてください。", "hot": "暑いため、水分補給と日焼け対策をしてください。", "wind": "風が強いため、外出時はご注意ください。"},
}


def weather_advice(weather: Weather, language: str) -> list[str]:
    messages = MESSAGES.get(language, MESSAGES["en"])
    advice = []
    if float(weather.precipitation_mm) > 0:
        advice.append(messages["umbrella"])
    if float(weather.feels_like_c) <= 5:
        advice.append(messages["cold"])
    elif float(weather.feels_like_c) >= 30:
        advice.append(messages["hot"])
    if float(weather.wind_kph) >= 35:
        advice.append(messages["wind"])
    return advice
