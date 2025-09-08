from aiogram import types
import config


def update_user_registry(user: types.User):
    """Обновить реестр пользователей информацией о пользователе"""
    if user and user.id:
        # Проверяем, изменилось ли что-то
        current_info = config.USER_REGISTRY.get(user.id)
        new_info = {'username': user.username}
        
        if current_info != new_info:
            config.USER_REGISTRY[user.id] = new_info
            # Автоматически сохраняем в файл
            config.save_user_registry(config.USER_REGISTRY)


def format_user_info(user_id: int, role: str) -> str:
    """Форматировать информацию о пользователе"""
    user_info = config.USER_REGISTRY.get(user_id)
    
    if user_info and user_info['username']:
        return f"ID: `{user_id}` - @{user_info['username']} - Роль: {role}"
    
    # Если информации нет или нет username, показываем только ID
    return f"ID: `{user_id}` - Роль: {role} (никнейм отсутствует)"