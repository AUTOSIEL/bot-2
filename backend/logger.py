import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Создаем папку для логов, если ее не существует
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Устанавливаем базовую конфигурацию для корневого логгера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d in %(funcName)s]',
        handlers=[
            RotatingFileHandler('logs/bot.log', maxBytes=5000000, backupCount=5, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True # Принудительно перенастраиваем логгер
    )