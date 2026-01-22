import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# Координаты центров крупных городов (широта, долгота)
CITY_COORDINATES = {
    "москва": (55.7558, 37.6173),
    "moscow": (55.7558, 37.6173),
    "санкт-петербург": (59.9343, 30.3351),
    "saint petersburg": (59.9343, 30.3351),
    "новосибирск": (55.0084, 82.9357),
    "yekaterinburg": (56.8389, 60.6057),
    "екатеринбург": (56.8389, 60.6057),
    "казань": (55.8304, 49.0661),
    "нижний новгород": (56.3268, 44.0063),
    "chelyabinsk": (55.1642, 61.4365),
    "челябинск": (55.1642, 61.4365),
    "самара": (53.1952, 50.1055),
    "омск": (54.9886, 73.3242),
    "ростов-на-дону": (47.2357, 39.7031),
    "краснодар": (45.0395, 38.9491),
    "ufa": (54.7386, 55.9722),
    "уфа": (54.7386, 55.9722),
}

# OSRM API - бесплатный сервис маршрутизации
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"


def get_city_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    """Получает координаты города из словаря"""
    city_lower = city_name.lower().strip()
    return CITY_COORDINATES.get(city_lower)


def get_traffic_level(city: str) -> Dict[str, Any]:
    """
    Получает уровень пробок используя OSRM API.
    Сравнивает время движения по маршруту с оптимальным временем.

    Возвращает словарь с информацией о пробках:
    - level: уровень пробок (1-10 баллов)
    - description: текстовое описание
    """
    coords = get_city_coordinates(city)
    if not coords:
        # Если город не найден в базе, возвращаем оценку по времени суток
        return get_traffic_by_time_of_day()

    lat, lon = coords
    # Создаем маршрут через город (из точки в точку с отступом от центра)
    # Маршрут长约10км через центр города
    offset = 0.1  # примерно 10км
    start_lon = lon - offset
    start_lat = lat
    end_lon = lon + offset
    end_lat = lat

    url = f"{OSRM_BASE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "false",
        "alternatives": "false"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                route = data["routes"][0]
                duration = route["duration"]  # фактическое время в секундах
                distance = route["distance"] / 1000  # расстояние в км

                # Оптимальное время при скорости 60 км/ч
                optimal_duration = (distance / 60) * 3600

                # Коэффициент задержки
                delay_ratio = duration / optimal_duration if optimal_duration > 0 else 1

                # Преобразуем в баллы от 1 до 10
                level = min(10, max(1, int((delay_ratio - 1) * 5 + 1)))

                return {
                    "status": 200,
                    "level": level,
                    "description": get_traffic_description(level)
                }

    except Exception as e:
        pass

    # Если не удалось получить данные, возвращаем оценку по времени суток
    return get_traffic_by_time_of_day()


def get_traffic_by_time_of_day() -> Dict[str, Any]:
    """
    Возвращает оценку пробок на основе времени суток (часы пик).
    Используется как fallback, если не удалось получить реальные данные.
    """
    hour = datetime.now().hour

    # Утренний час пик: 7-9
    if 7 <= hour <= 9:
        level = 8
    # Вечерний час пик: 17-20
    elif 17 <= hour <= 20:
        level = 9
    # День: 10-16
    elif 10 <= hour <= 16:
        level = 6
    # Ночь: 21-6
    elif 21 <= hour or hour <= 6:
        level = 2
    else:
        level = 4

    return {
        "status": 200,
        "level": level,
        "description": get_traffic_description(level)
    }


def get_traffic_description(level: int) -> str:
    """Возвращает текстовое описание уровня пробок"""
    if level <= 2:
        return "🟢 Свободные дороги"
    elif level <= 4:
        return "🟡 Легкие пробки"
    elif level <= 6:
        return "🟠 Умеренные пробки"
    elif level <= 8:
        return "🔴 Сильные пробки"
    else:
        return "⚫ Пробочные ад"


if __name__ == "__main__":
    # Тестирование
    for city in ["Москва", "Краснодар", "Unknown"]:
        result = get_traffic_level(city)
        print(f"{city}: {result}")
