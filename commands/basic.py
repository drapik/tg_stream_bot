from aiogram import Dispatcher, types
from aiogram.filters import Command
from decorators import role_required
from config import VERSION


@role_required("user")
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я бот для скачивания медиа из социальных сетей.\n"
        "Используй /version чтобы узнать версию бота."
    )


@role_required("user")
async def version_handler(message: types.Message):
    """Обработчик команды /version"""
    await message.answer(f"Версия бота: {VERSION}")


def register_basic_commands(dp: Dispatcher):
    """Регистрация базовых команд"""
    dp.message(Command("start"))(start_handler)
    dp.message(Command("version"))(version_handler)
