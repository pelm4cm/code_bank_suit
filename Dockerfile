# 1. Используем официальный образ Python
FROM python:3.10.12-slim

# 2. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 3. Копируем файл с зависимостями и устанавливаем их
# Копируем сначала, чтобы кэш Docker сработал, если мы меняем только код
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 4. Копируем все файлы приложения из папки app в рабочую директорию контейнера
COPY ./app /app

# 5. Команда для запуска приложения.
# Используем Uvicorn, стандартный ASGI-сервер для FastAPI.
# Он запустит ваше приложение из app/main.py (объект `app`)
# и сделает его доступным внутри сети Docker на порту 8000.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
