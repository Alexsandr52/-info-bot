FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем требования и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY bot.py .
COPY config.py .
COPY database.py .
COPY services/ ./services/

# Создаем директорию для логов и базы данных
RUN mkdir -p /app/logs /app/data

# Устанавливаем рабочую директорию
VOLUME ["/app/data"]

CMD ["python", "bot.py"]
