import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VERSION = "1.0.0"

# Проверяем обязательные переменные
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")

# Настройки админов (можно добавить через переменные окружения)
ADMIN_IDS = [
    int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id.strip()
]

# Система ролей и доступа
WHITELIST = {
    # user_id: role
    314009331: "admin",  # для тестов
    987654321: "user",    # для тестов
    491956927: "admin"
}

ROLE_HIERARCHY = {
    "admin": ["admin", "moderator", "user"],
    "moderator": ["moderator", "user"], 
    "user": ["user"]
}

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
