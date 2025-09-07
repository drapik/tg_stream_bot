from aiogram import Dispatcher, types
from aiogram.filters import Command
from decorators import role_required
from config import WHITELIST


@role_required("admin")
async def users_handler(message: types.Message):
    """Показать список пользователей в whitelist"""
    if not WHITELIST:
        await message.answer("🔍 Whitelist пуст")
        return
    
    users_text = "👥 Пользователи в whitelist:\n\n"
    for user_id, role in WHITELIST.items():
        users_text += f"ID: `{user_id}` - Роль: {role}\n"
    
    await message.answer(users_text, parse_mode="Markdown")


def register_admin_commands(dp: Dispatcher):
    """Регистрация админских команд"""
    dp.message(Command("users"))(users_handler)
