import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
    

def get_weather(city: str) -> dict:
    """Получает погоду и записывает данные в result."""
    if not city or not isinstance(city, str):
        return {
            'status': 500,
            'exception': 'Invalid city parameter'
        }

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city.strip(),
        "appid": Config.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() 

        data = response.json()
        return {
            'status': 200,
            'city': data["name"],
            'temp': data["main"]["temp"],
            'feels_like': data["main"]["feels_like"],
            'description': data["weather"][0]["description"].capitalize()
        }


    except Exception as e:
        return {
            'status': 500,
            'exception': e
        }
    
if __name__ == "__main__":
    print(get_weather('Krasnodar'))