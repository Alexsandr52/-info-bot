import requests

from config import Config


def is_valid_city(city_name: str) -> bool:
    """Проверяет существование города через OpenWeatherMap API"""
    if not city_name or len(city_name.strip()) < 2:
        return False

    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city_name.strip(),
        "limit": 1,
        "appid": Config.OPENWEATHER_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return len(data) > 0
        return False
    except Exception:
        return False
