# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем Chrome и необходимые зависимости для Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Открываем порт 80 (как у вас в app.py)
EXPOSE 80

# Запускаем приложение (меняем запуск Flask для продакшена через Gunicorn)
RUN pip install gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:80", "--timeout", "120", "app:app"]