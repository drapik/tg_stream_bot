import os
import json
from pathlib import Path
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

# Реестр пользователей для хранения информации о никнеймах
USER_REGISTRY_FILE = "data/user_registry.json"

def load_user_registry():
    """Загрузить реестр пользователей из файла"""
    try:
        Path(USER_REGISTRY_FILE).parent.mkdir(parents=True, exist_ok=True)
        if Path(USER_REGISTRY_FILE).exists():
            with open(USER_REGISTRY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Конвертируем строковые ключи обратно в int
                return {int(k): v for k, v in data.items()}
    except Exception as e:
        print(f"Ошибка при загрузке реестра пользователей: {e}")
    return {}

def save_user_registry(registry):
    """Сохранить реестр пользователей в файл"""
    try:
        Path(USER_REGISTRY_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(USER_REGISTRY_FILE, 'w', encoding='utf-8') as f:
            # Конвертируем int ключи в строки для JSON
            json_data = {str(k): v for k, v in registry.items()}
            json.dump(json_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении реестра пользователей: {e}")

USER_REGISTRY = load_user_registry()

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
