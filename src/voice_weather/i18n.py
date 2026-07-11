LANGUAGES = {
    "zh": "简体中文",
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "ja": "日本語",
}

TEXT = {
    "zh": {
        "title": "多语言语音天气", "current": "当前天气与语音播报", "forecast": "七天天气预报",
        "cities": "管理快捷城市", "language": "语言与语音", "settings": "设置", "quit": "退出",
        "choose": "请选择", "back": "返回", "manual": "手动输入其他城市", "local": "当前地区",
        "select_city": "选择城市", "city_prompt": "请输入城市和国家", "days": "预报天数 1-7",
        "loading": "正在获取天气…", "goodbye": "再见！", "invalid": "选择无效",
        "temperature": "温度", "feels": "体感", "humidity": "湿度", "rain": "降雨概率",
        "wind": "风速", "pressure": "气压", "date": "日期", "low_high": "最低/最高", "conditions": "天气",
        "voice": "语音", "enabled": "开启", "disabled": "关闭", "change_language": "更改界面语言",
        "toggle_voice": "开启/关闭语音", "refresh_location": "刷新当前位置", "location_consent": "是否允许通过网络 IP 获取城市级位置？",
        "location_off": "尚未设置当前位置", "saved": "设置已保存", "favorites": "收藏城市", "add": "新增城市", "delete": "删除城市",
    },
    "en": {
        "title": "Multilingual Voice Weather", "current": "Current weather & voice", "forecast": "Seven-day forecast",
        "cities": "Manage favorite cities", "language": "Language & voice", "settings": "Settings", "quit": "Quit",
        "choose": "Choose", "back": "Back", "manual": "Enter another city", "local": "Current location",
        "select_city": "Select city", "city_prompt": "Enter city and country", "days": "Forecast days 1-7",
        "loading": "Loading weather…", "goodbye": "Goodbye!", "invalid": "Invalid choice",
        "temperature": "Temperature", "feels": "Feels like", "humidity": "Humidity", "rain": "Rain",
        "wind": "Wind", "pressure": "Pressure", "date": "Date", "low_high": "Low/High", "conditions": "Conditions",
        "voice": "Voice", "enabled": "On", "disabled": "Off", "change_language": "Change interface language",
        "toggle_voice": "Toggle voice", "refresh_location": "Refresh current location", "location_consent": "Allow city-level location lookup using your network IP?",
        "location_off": "Current location is not set", "saved": "Settings saved", "favorites": "Favorite cities", "add": "Add city", "delete": "Delete city",
    },
}

# Complete UI fallbacks keep every language usable while translated weather and speech remain native.
for code in ("fr", "es", "ja"):
    TEXT[code] = dict(TEXT["en"])

TEXT["fr"].update({"title": "Météo vocale multilingue", "current": "Météo actuelle et voix", "forecast": "Prévisions sur sept jours", "quit": "Quitter", "choose": "Choisissez", "back": "Retour", "loading": "Chargement de la météo…", "goodbye": "Au revoir !", "temperature": "Température", "humidity": "Humidité", "conditions": "Conditions"})
TEXT["es"].update({"title": "Tiempo por voz multilingüe", "current": "Tiempo actual y voz", "forecast": "Pronóstico de siete días", "quit": "Salir", "choose": "Elija", "back": "Volver", "loading": "Cargando el tiempo…", "goodbye": "¡Adiós!", "temperature": "Temperatura", "humidity": "Humedad", "conditions": "Condiciones"})
TEXT["ja"].update({"title": "多言語音声天気", "current": "現在の天気と音声", "forecast": "7日間予報", "quit": "終了", "choose": "選択", "back": "戻る", "loading": "天気を取得中…", "goodbye": "さようなら！", "temperature": "気温", "humidity": "湿度", "conditions": "天気"})

TEXT["fr"].update({"cities": "Gérer les villes favorites", "language": "Langue et voix", "settings": "Réglages", "select_city": "Choisir une ville", "manual": "Saisir une autre ville", "local": "Position actuelle", "city_prompt": "Ville et pays", "days": "Jours de prévision 1-7", "feels": "Ressenti", "rain": "Pluie", "wind": "Vent", "pressure": "Pression", "date": "Date", "low_high": "Min/Max", "voice": "Voix", "favorites": "Villes favorites", "add": "Ajouter une ville", "delete": "Supprimer une ville"})
TEXT["es"].update({"cities": "Administrar ciudades favoritas", "language": "Idioma y voz", "settings": "Ajustes", "select_city": "Elegir ciudad", "manual": "Introducir otra ciudad", "local": "Ubicación actual", "city_prompt": "Ciudad y país", "days": "Días de pronóstico 1-7", "feels": "Sensación", "rain": "Lluvia", "wind": "Viento", "pressure": "Presión", "date": "Fecha", "low_high": "Mín/Máx", "voice": "Voz", "favorites": "Ciudades favoritas", "add": "Añadir ciudad", "delete": "Eliminar ciudad"})
TEXT["ja"].update({"cities": "お気に入り都市の管理", "language": "言語と音声", "settings": "設定", "select_city": "都市を選択", "manual": "別の都市を入力", "local": "現在地", "city_prompt": "都市と国", "days": "予報日数 1-7", "feels": "体感温度", "rain": "降水確率", "wind": "風速", "pressure": "気圧", "date": "日付", "low_high": "最低/最高", "voice": "音声", "favorites": "お気に入り都市", "add": "都市を追加", "delete": "都市を削除"})

WEATHER = {
    "zh": {"Clear": "晴朗", "Mainly clear": "大致晴朗", "Partly cloudy": "局部多云", "Overcast": "阴天", "Fog": "有雾", "Light drizzle": "小毛毛雨", "Drizzle": "毛毛雨", "Heavy drizzle": "较强毛毛雨", "Light rain": "小雨", "Moderate rain": "中雨", "Heavy rain": "大雨", "Light snow": "小雪", "Moderate snow": "中雪", "Heavy snow": "大雪", "Thunderstorm": "雷暴"},
    "fr": {"Clear": "Dégagé", "Mainly clear": "Plutôt dégagé", "Partly cloudy": "Partiellement nuageux", "Overcast": "Couvert", "Fog": "Brouillard", "Light rain": "Pluie légère", "Moderate rain": "Pluie modérée", "Heavy rain": "Forte pluie", "Light snow": "Neige légère", "Thunderstorm": "Orage"},
    "es": {"Clear": "Despejado", "Mainly clear": "Mayormente despejado", "Partly cloudy": "Parcialmente nublado", "Overcast": "Cubierto", "Fog": "Niebla", "Light rain": "Lluvia ligera", "Moderate rain": "Lluvia moderada", "Heavy rain": "Lluvia fuerte", "Light snow": "Nieve ligera", "Thunderstorm": "Tormenta"},
    "ja": {"Clear": "晴れ", "Mainly clear": "おおむね晴れ", "Partly cloudy": "一部曇り", "Overcast": "曇り", "Fog": "霧", "Light rain": "小雨", "Moderate rain": "雨", "Heavy rain": "大雨", "Light snow": "小雪", "Thunderstorm": "雷雨"},
}


def tr(language: str, key: str) -> str:
    return TEXT.get(language, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def weather_text(language: str, description: str) -> str:
    if language == "en":
        return description
    if description == "Sunny":
        description = "Clear"
    return WEATHER.get(language, {}).get(description, description)
