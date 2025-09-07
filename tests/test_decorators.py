import pytest
from unittest.mock import patch, AsyncMock
from decorators.auth import role_required


class TestRoleRequired:
    """Тесты декоратора role_required"""

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_command(self, mock_admin_message):
        """Тест: админ может выполнять админские команды"""
        
        @role_required("admin")
        async def admin_command(message):
            await message.answer("Admin command executed")
        
        # Выполняем команду
        with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
            await admin_command(mock_admin_message)
        
        # Проверяем что команда выполнилась
        mock_admin_message.answer.assert_called_once_with("Admin command executed")

    @pytest.mark.asyncio
    async def test_admin_can_access_user_command(self, mock_admin_message):
        """Тест: админ может выполнять пользовательские команды (иерархия ролей)"""
        
        @role_required("user")
        async def user_command(message):
            await message.answer("User command executed")
        
        with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
            await user_command(mock_admin_message)
        mock_admin_message.answer.assert_called_once_with("User command executed")

    @pytest.mark.asyncio
    async def test_user_cannot_access_admin_command(self, mock_user_message):
        """Тест: обычный пользователь не может выполнять админские команды"""
        
        @role_required("admin")
        async def admin_command(message):
            await message.answer("Admin command executed")
        
        with patch("decorators.auth.WHITELIST", {987654321: "user"}):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                await admin_command(mock_user_message)
        
        # Проверяем что отправлено сообщение об отказе в доступе
        mock_user_message.answer.assert_called_once_with("❌ Недостаточно прав. Требуется роль: admin")

    @pytest.mark.asyncio
    async def test_user_can_access_user_command(self, mock_user_message):
        """Тест: пользователь может выполнять пользовательские команды"""
        
        @role_required("user")
        async def user_command(message):
            await message.answer("User command executed")
        
        with patch("decorators.auth.WHITELIST", {987654321: "user"}):
            with patch("decorators.auth.ROLE_HIERARCHY", {"user": ["user"], "admin": ["admin", "user"]}):
                await user_command(mock_user_message)
        
        mock_user_message.answer.assert_called_once_with("User command executed")

    @pytest.mark.asyncio
    async def test_unauthorized_user_blocked(self, mock_unauthorized_message):
        """Тест: неавторизованный пользователь заблокирован"""
        
        @role_required("user")
        async def user_command(message):
            await message.answer("User command executed")
        
        await user_command(mock_unauthorized_message)
        
        # Проверяем что отправлено сообщение об отказе в доступе
        mock_unauthorized_message.answer.assert_called_once_with("❌ У вас нет доступа к этому боту.")

    @pytest.mark.asyncio
    async def test_user_not_in_whitelist(self, mock_unauthorized_message):
        """Тест: пользователь не в whitelist не может выполнять команды"""
        
        @role_required("user")
        async def user_command(message):
            await message.answer("User command executed")
        
        with patch("config.WHITELIST", {}):
            await user_command(mock_unauthorized_message)
        
        mock_unauthorized_message.answer.assert_called_once_with("❌ У вас нет доступа к этому боту.")

    @pytest.mark.asyncio
    async def test_role_hierarchy_consistency(self):
        """Тест: проверка консистентности иерархии ролей"""
        from config import ROLE_HIERARCHY
        
        # Админ должен иметь права пользователя
        assert "user" in ROLE_HIERARCHY["admin"]
        assert "admin" in ROLE_HIERARCHY["admin"]
        
        # Пользователь должен иметь только свои права
        assert "user" in ROLE_HIERARCHY["user"]
        assert "admin" not in ROLE_HIERARCHY["user"]
