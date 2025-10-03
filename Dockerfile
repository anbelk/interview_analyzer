FROM python:3.11-slim

# Устанавливаем ffmpeg и создаём папки один раз
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app/downloads /app/reports

WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY src/ ./src

# Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app

# Запуск бота
CMD ["python", "src/bot.py"]
