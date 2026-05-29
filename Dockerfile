FROM python:3.12-slim

# Установить ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копировать зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать скрипт
COPY telegram_tts_bot.py .

# Запуск
CMD ["python", "telegram_tts_bot.py"]
