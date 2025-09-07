from functools import wraps
from aiogram import types
from config import WHITELIST, ROLE_HIERARCHY


def role_required(required_role: str):
    """Декоратор для проверки роли пользователя"""
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs):
            user_id = message.from_user.id
            
            # Проверяем наличие пользователя в whitelist
            if user_id not in WHITELIST:
                await message.answer("❌ У вас нет доступа к этому боту.")
                return
            
            user_role = WHITELIST[user_id]
            
            # Проверяем права доступа
            if required_role not in ROLE_HIERARCHY.get(user_role, []):
                await message.answer(f"❌ Недостаточно прав. Требуется роль: {required_role}")
                return
            
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator
