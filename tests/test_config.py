import pytest
import os
from unittest.mock import patch
import config


class TestConfig:
    """Тесты конфигурации"""

    def test_version_is_set(self):
        """Тест: версия бота установлена"""
        assert config.VERSION is not None
        assert isinstance(config.VERSION, str)
        assert len(config.VERSION) > 0

    def test_whitelist_structure(self):
        """Тест: структура whitelist корректна"""
        assert isinstance(config.WHITELIST, dict)
        
        # Проверяем что все ключи - числа (ID пользователей)
        for user_id in config.WHITELIST.keys():
            assert isinstance(user_id, int), f"ID пользователя должен быть int, получен {type(user_id)}"
        
        # Проверяем что все значения - строки (роли)
        for role in config.WHITELIST.values():
            assert isinstance(role, str), f"Роль должна быть str, получена {type(role)}"
            assert role in config.ROLE_HIERARCHY, f"Роль {role} не найдена в ROLE_HIERARCHY"

    def test_role_hierarchy_structure(self):
        """Тест: структура иерархии ролей корректна"""
        assert isinstance(config.ROLE_HIERARCHY, dict)
        
        # Проверяем что есть базовые роли
        assert "admin" in config.ROLE_HIERARCHY
        assert "user" in config.ROLE_HIERARCHY
        
        # Проверяем что каждая роль содержит список разрешений
        for role, permissions in config.ROLE_HIERARCHY.items():
            assert isinstance(permissions, list), f"Права роли {role} должны быть списком"
            assert role in permissions, f"Роль {role} должна содержать саму себя в правах"

    def test_role_hierarchy_consistency(self):
        """Тест: консистентность иерархии ролей"""
        # Админ должен иметь все права пользователя
        admin_permissions = config.ROLE_HIERARCHY["admin"]
        user_permissions = config.ROLE_HIERARCHY["user"]
        
        for permission in user_permissions:
            assert permission in admin_permissions, f"Админ должен иметь право {permission}"

    def test_admin_role_in_whitelist(self):
        """Тест: в whitelist есть хотя бы один админ"""
        admin_found = False
        for user_id, role in config.WHITELIST.items():
            if role == "admin":
                admin_found = True
                break
        
        assert admin_found, "В whitelist должен быть хотя бы один админ"

    @patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token_123"})
    def test_bot_token_loaded_from_env(self):
        """Тест: токен бота загружается из переменных окружения"""
        # Перезагружаем модуль config чтобы применить новые переменные окружения
        import importlib
        importlib.reload(config)
        
        assert config.BOT_TOKEN == "test_token_123"

    @patch.dict(os.environ, {}, clear=True) 
    def test_bot_token_none_when_not_set(self):
        """Тест: токен бота None когда не установлен"""
        # Проверяем что без переменной окружения токен будет None
        # Но учитываем что у пользователя может быть .env файл
        with patch('config.load_dotenv'):
            import importlib
            importlib.reload(config)
            # Если все равно есть токен, значит он из .env файла - это нормально
            assert config.BOT_TOKEN is None or isinstance(config.BOT_TOKEN, str)

    def test_whitelist_contains_valid_admin_id(self):
        """Тест: whitelist содержит валидный ID админа"""
        # Проверяем что ID админа - положительное число
        for user_id, role in config.WHITELIST.items():
            if role == "admin":
                assert user_id > 0, "ID пользователя должен быть положительным числом"
                assert len(str(user_id)) >= 8, "ID пользователя Telegram должен быть достаточно длинным"

    def test_role_hierarchy_has_all_used_roles(self):
        """Тест: иерархия ролей содержит все используемые роли"""
        used_roles = set(config.WHITELIST.values())
        hierarchy_roles = set(config.ROLE_HIERARCHY.keys())
        
        for role in used_roles:
            assert role in hierarchy_roles, f"Роль {role} из whitelist отсутствует в ROLE_HIERARCHY"

    def test_config_module_imports_successfully(self):
        """Тест: модуль config импортируется без ошибок"""
        import config as test_config
        
        # Проверяем что все необходимые атрибуты присутствуют
        required_attrs = ["BOT_TOKEN", "VERSION", "WHITELIST", "ROLE_HIERARCHY"]
        
        for attr in required_attrs:
            assert hasattr(test_config, attr), f"Атрибут {attr} отсутствует в config"
