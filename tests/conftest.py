import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat


@pytest.fixture
def mock_admin_message():
    """Мок сообщения от админа"""
    message = AsyncMock(spec=Message)
    message.from_user = User(id=314009331, is_bot=False, first_name="Admin")
    message.chat = Chat(id=314009331, type="private")
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_user_message():
    """Мок сообщения от обычного пользователя"""
    message = AsyncMock(spec=Message)
    message.from_user = User(id=987654321, is_bot=False, first_name="User")
    message.chat = Chat(id=987654321, type="private")
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_unauthorized_message():
    """Мок сообщения от неавторизованного пользователя"""
    message = AsyncMock(spec=Message)
    message.from_user = User(id=999999999, is_bot=False, first_name="Unauthorized")
    message.chat = Chat(id=999999999, type="private")
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_dispatcher():
    """Мок диспетчера"""
    from aiogram import Dispatcher
    mock_dp = MagicMock(spec=Dispatcher)
    # Создаем мок message как вызываемый объект
    mock_dp.message = MagicMock()
    return mock_dp
