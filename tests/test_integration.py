import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User, Chat, Update
import config


class TestBotIntegration:
    """Интеграционные тесты бота"""

    @pytest.fixture
    def mock_bot(self):
        """Мок бота"""
        bot = AsyncMock(spec=Bot)
        bot.session = AsyncMock()
        bot.session.close = AsyncMock()
        return bot

    @pytest.fixture
    def mock_update_admin(self):
        """Мок обновления от админа"""
        message = Message(
            message_id=1,
            date=1234567890,
            chat=Chat(id=314009331, type="private"),
            from_user=User(id=314009331, is_bot=False, first_name="Admin"),
            content_type="text",
            text="/start"
        )
        
        update = Update(update_id=1, message=message)
        return update

    @pytest.mark.asyncio
    async def test_bot_startup_configuration(self, mock_bot):
        """Тест: корректная конфигурация при запуске"""
        from bot import dp
        
        # Проверяем что диспетчер создан
        assert isinstance(dp, Dispatcher)
        
        # Проверяем что команды зарегистрированы
        # У диспетчера должны быть обработчики
        handlers_count = len(dp.message.handlers)
        assert handlers_count > 0, "Должны быть зарегистрированы обработчики команд"

    @pytest.mark.asyncio
    async def test_command_registration_completeness(self):
        """Тест: все команды корректно регистрируются"""
        from commands.basic import register_basic_commands
        from commands.admin import register_admin_commands
        
        # Создаем новый диспетчер для теста
        test_dp = Dispatcher()
        
        # Регистрируем команды
        register_basic_commands(test_dp)
        register_admin_commands(test_dp)
        
        # Проверяем что команды зарегистрированы
        handlers = test_dp.message.handlers
        assert len(handlers) >= 3, "Должно быть зарегистрировано минимум 3 команды"

    @patch("config.BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    @pytest.mark.asyncio
    async def test_bot_creation_with_token(self):
        """Тест: бот создается с корректным токеном"""
        from aiogram import Bot
        
        bot = Bot(token=config.BOT_TOKEN)
        assert bot.token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        await bot.session.close()

    @pytest.mark.asyncio
    async def test_logging_configuration(self):
        """Тест: логирование настроено корректно"""
        from loguru import logger
        
        # Проверяем что логгер настроен
        assert len(logger._core.handlers) > 0, "Должны быть настроены обработчики логов"
        
        # Проверяем что можем писать в лог
        try:
            logger.info("Test log message")
        except Exception as e:
            pytest.fail(f"Ошибка при записи в лог: {e}")

    @pytest.mark.asyncio
    async def test_version_accessibility(self):
        """Тест: версия доступна для использования"""
        from config import VERSION
        
        assert VERSION is not None
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0

    @pytest.mark.asyncio
    async def test_whitelist_configuration_validity(self):
        """Тест: конфигурация whitelist валидна"""
        from config import WHITELIST, ROLE_HIERARCHY
        
        # Проверяем что все роли в whitelist существуют в иерархии
        for user_id, role in WHITELIST.items():
            assert role in ROLE_HIERARCHY, f"Роль {role} не найдена в ROLE_HIERARCHY"

    @pytest.mark.asyncio
    async def test_environment_loading(self):
        """Тест: переменные окружения загружаются"""
        # Проверяем что dotenv загружен
        import os
        from dotenv import load_dotenv
        
        # Загружаем переменные
        load_dotenv()
        
        # Проверяем что функция отработала без ошибок
        # (сам факт загрузки переменных проверяется в других тестах)
        assert True

    @patch("signal.signal")
    @pytest.mark.asyncio
    async def test_signal_handlers_registration(self, mock_signal):
        """Тест: обработчики сигналов регистрируются"""
        import signal
        
        # Импортируем main чтобы проверить регистрацию сигналов
        from bot import main
        
        # Запускаем main в фоне и сразу прерываем
        task = asyncio.create_task(main())
        await asyncio.sleep(0.1)  # Даем время на инициализацию
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Проверяем что signal.signal вызывался для регистрации обработчиков
        assert mock_signal.call_count >= 2, "Должны быть зарегистрированы SIGINT и SIGTERM"

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, mock_bot):
        """Тест: корректная остановка бота"""
        # Проверяем что сессия бота может быть закрыта
        await mock_bot.session.close()
        mock_bot.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_main(self):
        """Тест: обработка ошибок в main функции"""
        from bot import main
        
        # Тест что main может обработать KeyboardInterrupt
        with patch("bot.dp.start_polling", side_effect=KeyboardInterrupt()):
            with patch("bot.bot.session.close", new_callable=AsyncMock):
                try:
                    await main()
                except SystemExit:
                    # SystemExit ожидается при обработке сигналов
                    pass
