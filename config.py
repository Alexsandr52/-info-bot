import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурационные данные приложения"""
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
