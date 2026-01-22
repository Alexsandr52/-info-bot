import atexit
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import telebot

from config import Config
from database import SessionLocal, Chat, deactivate_chat, is_active_chat, log_exception, save_chat, select, get_city_name, set_reports_enabled, are_reports_enabled
from services.weather import is_valid_city, get_weather
from services.traffic import get_traffic_level

bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработка команды /start - активация бота"""
    chat_id = message.chat.id
    chat_type = message.chat.type

    try:
        if not is_active_chat(chat_id):
            success = save_chat(chat_id, chat_type)
            if success:
                welcome_text = (
                    "👋 Привет! Я информационный бот.\n\n"
                    "📋 Что я умею:\n"
                    "• 🌤 Ежедневная утренняя рассылка с погодой и пробками\n"
                    "• 🌡 Текущая погода по команде /weather\n"
                    "• 🚗 Текущие пробки по команде /traffic\n"
                    "• 🏙 Выбор вашего города: /set_city\n"
                    "• ⏸ Управление рассылкой: /stop и /resume\n\n"
                    "📍 Город по умолчанию: Москва\n"
                    "🕐 Рассылка приходит каждое утро в 7:00 (по Мск)\n\n"
                    "Для изменения города используйте:\n"
                    "/set_city Название"
                )
                bot.send_message(chat_id, welcome_text)
            else:
                bot.send_message(chat_id, "❌ Не удалось сохранить данные. Попробуйте позже.")
        else:
            bot.send_message(
                chat_id,
                "✅ Бот уже активен!\n"
                "Доступные команды:\n"
                "/set_city — изменить город\n"
                "/weather — текущая погода\n"
                "/traffic — текущие пробки\n"
                "/stop — остановить рассылку\n"
                "/resume — возобновить рассылку"
            )

    except Exception as e:
        log_exception(e)
        bot.send_message(chat_id, "⚠️ Что-то пошло не так при активации. Админу отправлен отчёт.")


@bot.message_handler(commands=['set_city'])
def set_city(message):
    """Обработка команды /set_city - изменение города"""
    chat_id = message.chat.id

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(
                chat_id,
                "📌 Укажите город после команды:\n"
                "/set_city Москва\n"
                "/set_city Krasnodar"
            )
            return

        city_name = parts[1].strip()
        if not city_name:
            bot.send_message(chat_id, "❌ Название города не может быть пустым.")
            return

        bot.send_message(chat_id, f"🔍 Ищу город «{city_name}»...")

        if not is_valid_city(city_name):
            bot.send_message(
                chat_id,
                f"❌ Город «{city_name}» не найден.\n"
                "Попробуйте:\n"
                "• Проверить орфографию\n"
                "• Использовать полное название (например: Санкт-Петербург)\n"
                "• Написать на русском или английском"
            )
            return

        from database import update_city
        success = update_city(chat_id, city_name)
        if success:
            bot.send_message(chat_id, f"✅ Отлично! Теперь я буду присылать данные для: {city_name}")
        else:
            bot.send_message(chat_id, "❌ Сначала активируйте бота командой /start")

    except Exception as e:
        log_exception(e)
        bot.send_message(chat_id, "⚠️ Не удалось проверить город. Попробуйте позже.")


@bot.message_handler(commands=['stop'])
def stop_bot(message):
    """Обработка команды /stop - остановка ежедневной рассылки"""
    chat_id = message.chat.id

    if not is_active_chat(chat_id):
        bot.send_message(
            chat_id,
            "❌ Бот не активирован.\n"
            "Сначала активируйте бота командой /start"
        )
        return

    success = set_reports_enabled(chat_id, False)
    if success:
        bot.send_message(
            chat_id,
            "⏸ Ежедневная рассылка остановлена.\n\n"
            "Бот остаётся активным, вы можете:\n"
            "• /weather — узнать текущую погоду\n"
            "• /set_city — изменить город\n"
            "• /resume — возобновить рассылку"
        )
    else:
        bot.send_message(chat_id, "⚠️ Не удалось остановить рассылку. Попробуйте позже.")


@bot.message_handler(commands=['resume'])
def resume_reports(message):
    """Обработка команды /resume - возобновление ежедневной рассылки"""
    chat_id = message.chat.id

    if not is_active_chat(chat_id):
        bot.send_message(
            chat_id,
            "❌ Бот не активирован.\n"
            "Сначала активируйте бота командой /start"
        )
        return

    success = set_reports_enabled(chat_id, True)
    if success:
        bot.send_message(
            chat_id,
            "✅ Ежедневная рассылка возобновлена!\n\n"
            "🕐 Отчёт будет приходить каждое утро в 7:00 (по Мск)\n"
            "Для остановки используйте /stop"
        )
    else:
        bot.send_message(chat_id, "⚠️ Не удалось возобновить рассылку. Попробуйте позже.")


@bot.message_handler(commands=['weather'])
def handle_weather(message):
    chat_id = message.chat.id
    city = get_city_name(chat_id)
    if not city:
        bot.send_message(chat_id, "❌ Сначала активируйте бота командой /start")
    else:
        weather = get_weather(city)
        if weather['status'] == 200:
            bot.send_message(
                chat_id,
                f'🌡 В городе {weather["city"]}: {weather["temp"]}°C\n'
                f'🤔 Ощущается как {weather["feels_like"]}°C\n'
                f'☁️ {weather["description"]}'
            )
        else:
            bot.send_message(chat_id, "❌ Не удалось получить данные о погоде. Попробуйте позже.")


@bot.message_handler(commands=['traffic'])
def handle_traffic(message):
    chat_id = message.chat.id
    city = get_city_name(chat_id)
    if not city:
        bot.send_message(chat_id, "❌ Сначала активируйте бота командой /start")
    else:
        traffic = get_traffic_level(city)
        if traffic['status'] == 200:
            bot.send_message(
                chat_id,
                f'🚗 Пробки в городе {city.capitalize()}\n'
                f'📊 Уровень: {traffic["level"]}/10\n'
                f'📝 {traffic["description"]}'
            )
        else:
            bot.send_message(chat_id, "❌ Не удалось получить данные о пробках. Попробуйте позже.")

def send_daily_report():
    """Отправляет утренний отчёт всем активным чатам с включенной рассылкой"""
    with SessionLocal() as session:
        active_chats = session.execute(
            select(Chat).where(Chat.is_active == True, Chat.reports_enabled == True)
        ).scalars().all()

        for chat in active_chats:
            try:
                # Получаем данные о погоде
                weather_data = get_weather(chat.city)
                weather_text = "❌ Не удалось получить"
                if weather_data['status'] == 200:
                    weather_text = (
                        f"{weather_data['temp']}°C (ощущается как {weather_data['feels_like']}°C)\n"
                        f"   {weather_data['description']}"
                    )

                # Получаем данные о пробках
                traffic_data = get_traffic_level(chat.city)
                traffic_text = "❌ Не удалось получить"
                if traffic_data['status'] == 200:
                    traffic_text = (
                        f"Уровень: {traffic_data['level']}/10\n"
                        f"   {traffic_data['description']}"
                    )

                message = (
                    f"🌤 Утренний отчёт для {chat.city}\n"
                    f"🕗 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"🌡 Погода:\n{weather_text}\n\n"
                    f"🚗 Пробки:\n{traffic_text}\n\n"
                    f"Хорошего дня! ☀"
                )
                bot.send_message(chat.chat_id, message)
            except Exception as e:
                # Если бота кикнули — деактивируем чат
                if "Forbidden" in str(e) or "kicked" in str(e):
                    chat.is_active = False
                    session.commit()


# Настройка планировщика
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
scheduler.add_job(
    send_daily_report,
    trigger=CronTrigger(hour=7, minute=0),
    id='daily_weather_report'
)
scheduler.start()

atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)


if __name__ == '__main__':
    bot.infinity_polling()
