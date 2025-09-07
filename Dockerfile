FROM python:3.12.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директорию для логов
RUN mkdir -p logs

# Создаем пользователя для запуска приложения (безопасность)
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Команда по умолчанию
CMD ["python", "bot.py"]
