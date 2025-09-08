from aiogram import Dispatcher, types
from aiogram.filters import Command
from decorators import role_required
from config import VERSION, WHITELIST


@role_required("user")
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я бот для скачивания медиа из социальных сетей.\n"
        "Используй /help чтобы увидеть все доступные команды."
    )


@role_required("user")
async def version_handler(message: types.Message):
    """Обработчик команды /version"""
    await message.answer(f"Версия бота: {VERSION}")


@role_required("user")
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    user_id = message.from_user.id
    user_role = WHITELIST.get(user_id, "user")
    
    help_text = "🤖 **Доступные команды:**\n\n"
    
    # Базовые команды для всех пользователей
    help_text += "📋 **Основные команды:**\n"
    help_text += "/start - Запуск бота и приветствие\n"
    help_text += "/help - Показать это сообщение\n"
    help_text += "/version - Версия бота\n\n"
    
    # Админские команды только для админов
    if user_role == "admin":
        help_text += "🛡️ **Админские команды:**\n"
        help_text += "/users - Список пользователей в whitelist\n\n"
    
    help_text += "ℹ️ Ваша роль: **" + user_role + "**"
    
    await message.answer(help_text, parse_mode="Markdown")


def register_basic_commands(dp: Dispatcher):
    """Регистрация базовых команд"""
    dp.message(Command("start"))(start_handler)
    dp.message(Command("version"))(version_handler)
    dp.message(Command("help"))(help_handler)
