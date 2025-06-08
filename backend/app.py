import os
import telebot
from dotenv import load_dotenv
import logging
from logger import setup_logger

# 1. Настраиваем логгер в самом начале, до всех остальных импортов
setup_logger()

# 2. Теперь импортируем наш основной модуль логики
import bot_logic

# Получаем настроенный логгер
logger = logging.getLogger(__name__)

def main():
    """Основная функция для запуска бота."""
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    
    if not TOKEN:
        logger.critical("Токен бота (TOKEN) не найден в .env файле! Бот не может быть запущен.")
        return

    logger.info(f"Используется токен, начинающийся на: {TOKEN[:10]}...")
    
    try:
        bot = telebot.TeleBot(TOKEN)
        bot_logic.register_handlers(bot)
        logger.info("Обработчики команд успешно зарегистрированы.")
    except Exception as e:
        logger.critical(f"Ошибка при инициализации TeleBot или регистрации обработчиков: {e}", exc_info=True)
        return

    logger.info("Попытка снять существующий вебхук...")
    try:
        if bot.get_webhook_info().url:
            bot.remove_webhook()
            logger.info("Вебхук успешно снят.")
        else:
            logger.info("Вебхук не был установлен.")
    except Exception as e:
        logger.error(f"Ошибка при снятии вебхука: {e}", exc_info=True)

    logger.info("Бот запускается в режиме polling...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logger.critical(f"Критическая ошибка в работе polling: {e}", exc_info=True)
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    main()