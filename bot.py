import asyncio
import asyncio
import signal
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, VERSION
from commands import register_admin_commands
from commands.ultimate import register_ultimate_commands

# Настройка логирования
logger.add("logs/bot.log", rotation="10 MB", retention=3, level="INFO")

# Создание объектов бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация команд
register_ultimate_commands(dp)  # Main implementation
register_admin_commands(dp)


async def main():
    """Основная функция запуска бота"""
    logger.info(f"Бот запущен! Версия: {VERSION}")
    
    # Обработчик сигналов для грациозной остановки
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}. Останавливаем бота...")
        sys.exit(0)
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Terminate
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        await bot.session.close()
        logger.info("Бот корректно остановлен")


if __name__ == "__main__":
    asyncio.run(main())