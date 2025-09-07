import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from aiogram import Dispatcher
from commands.basic import register_basic_commands
from commands.admin import register_admin_commands
from config import VERSION


class TestBasicCommands:
    """Тесты базовых команд"""

    @pytest.mark.asyncio
    async def test_start_command_response(self, mock_admin_message):
        """Тест: команда /start возвращает корректный ответ"""
        from commands.basic import start_handler
        
        # Мокаем WHITELIST для авторизации админа
        with patch("decorators.auth.WHITELIST", {314009331: "admin"}):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                await start_handler(mock_admin_message)
        
        # Проверяем ответ
        expected_text = (
            "Привет! Я бот для скачивания медиа из социальных сетей.\n"
            "Используй /version чтобы узнать версию бота."
        )
        mock_admin_message.answer.assert_called_once_with(expected_text)

    @pytest.mark.asyncio
    async def test_version_command_returns_correct_version(self, mock_admin_message):
        """Тест: команда /version возвращает правильную версию"""
        from commands.basic import version_handler
        
        # Мокаем WHITELIST для авторизации админа
        with patch("decorators.auth.WHITELIST", {314009331: "admin"}):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                await version_handler(mock_admin_message)
        
        mock_admin_message.answer.assert_called_once_with(f"Версия бота: {VERSION}")

    @pytest.mark.asyncio
    async def test_commands_require_authorization(self, mock_unauthorized_message):
        """Тест: команды требуют авторизации"""
        from commands.basic import start_handler
        
        # Проверяем что неавторизованный пользователь получает отказ
        await start_handler(mock_unauthorized_message)
        
        mock_unauthorized_message.answer.assert_called_once_with("❌ У вас нет доступа к этому боту.")


class TestAdminCommands:
    """Тесты админских команд"""

    @pytest.mark.asyncio
    async def test_users_command_with_empty_whitelist(self, mock_admin_message):
        """Тест: команда /users с пустым whitelist"""
        from commands.admin import users_handler
        
        # Мокаем пустой WHITELIST и авторизацию админа
        with patch("decorators.auth.WHITELIST", {314009331: "admin"}):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                with patch("commands.admin.WHITELIST", {}):
                    await users_handler(mock_admin_message)
        
        mock_admin_message.answer.assert_called_once_with("🔍 Whitelist пуст")

    @pytest.mark.asyncio
    async def test_users_command_with_users(self, mock_admin_message):
        """Тест: команда /users с пользователями в whitelist"""
        from commands.admin import users_handler
        
        # Мокаем WHITELIST с пользователями
        test_whitelist = {
            314009331: "admin",
            987654321: "user"
        }
        
        with patch("decorators.auth.WHITELIST", test_whitelist):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                with patch("commands.admin.WHITELIST", test_whitelist):
                    await users_handler(mock_admin_message)
        
        # Проверяем что ответ содержит информацию о пользователях
        call_args = mock_admin_message.answer.call_args
        assert call_args[1]["parse_mode"] == "Markdown"
        
        response_text = call_args[0][0]
        assert "👥 Пользователи в whitelist:" in response_text
        assert "ID: `314009331` - Роль: admin" in response_text
        assert "ID: `987654321` - Роль: user" in response_text

    @pytest.mark.asyncio
    async def test_admin_commands_require_admin_role(self, mock_user_message):
        """Тест: админские команды требуют роль админа"""
        from commands.admin import users_handler
        
        # Тестируем что пользователь с ролью user не может выполнить админскую команду
        with patch("decorators.auth.WHITELIST", {987654321: "user"}):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                await users_handler(mock_user_message)
        
        mock_user_message.answer.assert_called_once_with("❌ Недостаточно прав. Требуется роль: admin")
