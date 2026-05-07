# Используем официальный образ Python
FROM python:3.10-slim

# Обновляем пакеты и устанавливаем wget, шрифты и сам Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fonts-liberation \
    fonts-dejavu-core \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Копируем весь остальной код проекта
COPY . .

# Команда для запуска приложения (Render сам подставит нужный порт через переменную среды $PORT)
CMD gunicorn -b 0.0.0.0:${PORT:-10000} --timeout 120 app:app