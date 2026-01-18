import atexit
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import telebot

from config import Config
from database import SessionLocal, Chat, deactivate_chat, is_active_chat, log_exception, save_chat, select
from services.weather import is_valid_city

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
                bot.send_message(
                    chat_id,
                    "✅ Бот успешно активирован!\n"
                    "Город по умолчанию: Москва.\n"
                    "Изменить город: /set_city Название"
                )
            else:
                bot.send_message(chat_id, "❌ Не удалось сохранить данные. Попробуйте позже.")
        else:
            bot.send_message(
                chat_id,
                "✅ Бот уже активен!\n"
                "Используйте /set_city, чтобы изменить город."
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
    """Обработка команды /stop - деактивация бота"""
    chat_id = message.chat.id
    success = deactivate_chat(chat_id)
    if success:
        bot.send_message(
            chat_id,
            "🔕 Бот деактивирован. Рассылка отключена.\n"
            "Чтобы возобновить — отправьте /start"
        )
    else:
        bot.send_message(chat_id, "⚠️ Не удалось отключить бота. Возможно, он уже неактивен.")


def send_daily_report():
    """Отправляет утренний отчёт всем активным чатам"""
    with SessionLocal() as session:
        active_chats = session.execute(
            select(Chat).where(Chat.is_active == True)
        ).scalars().all()

        for chat in active_chats:
            try:
                message = (
                    f"🌤 Утренний отчёт для {chat.city}\n"
                    f"🕗 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"🌡 Погода: [заглушка]\n"
                    f"🚗 Пробки: [заглушка]"
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
