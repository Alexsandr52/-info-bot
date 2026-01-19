# Weather Bot

Telegram бот для утренних отчётов о погоде и пробках. Бот отправляет ежедневные уведомления с информацией о погоде для указанного города.

## Возможности

- Активация бота командой `/start`
- Настройка города командой `/set_city <название>`
- Проверка существования города через OpenWeatherMap API
- Автоматическая отправка утренних отчётов по расписанию (каждый день в 7:00)
- Деактивация бота командой `/stop`

## Структура проекта

```
info-bot/
├── bot.py               # Основной код бота
├── database.py          # Работа с SQLite через SQLAlchemy
├── config.py            # Конфигурация и переменные окружения
├── requirements.txt     # Зависимости Python
├── .env                 # Переменные окружения (не в GIT)
├── .gitignore          # Исключения для GIT
├── README.md           # Документация
├── app.db              # База данных SQLite (создаётся автоматически)
├── services/
│   ├── __init__.py
│   └── weather.py      # Проверка городов через OpenWeatherMap
└── logs/               # Логи ошибок (создаётся автоматически)
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd info-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/macOS
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения в файле `.env`:
```
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=sqlite:///app.db
OPENWEATHER_API_KEY=ваш_ключ_от_OpenWeatherMap
```

### Получение токенов

1. **Telegram Bot Token**:
   - Напишите [@BotFather](https://t.me/botfather) в Telegram
   - Создайте нового бота командой `/newbot`
   - Скопируйте полученный токен

2. **OpenWeatherMap API Key**:
   - Зарегистрируйтесь на [openweathermap.org](https://openweathermap.org/api)
   - Получите бесплатный API ключ

## Использование

### Запуск бота

Перед запуском убедитесь, что бд создана или создайте выполнив следующую команду.
```bash
python database.py
```

```bash
python bot.py
```

### Команды бота

- `/start` — Активировать бота и сохранить чат
- `/set_city <город>` — Установить город для погоды (например: `/set_city Москва`)
- `/stop` — Деактивировать бота и остановить рассылку

## База данных

Бот использует SQLite для хранения:
- `chat_id` — Уникальный идентификатор чата
- `chat_type` — Тип чата (private/group/supergroup)
- `city` — Выбранный город пользователя
- `is_active` — Статус активации бота

## Расписание

По умолчанию утренний отчёт отправляется каждый день в 7:00 по московскому времени. Для изменения часового пояса отредактируйте строку в `bot.py`:

```python
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
```

## Требования

- Python 3.9+
- Библиотеки из `requirements.txt`

## Лицензия

MIT License
