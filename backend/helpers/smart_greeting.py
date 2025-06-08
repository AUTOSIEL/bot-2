# helpers/smart_greeting.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_greeting(user_data):
    """
    Генерирует умное, контекстное приветствие.
    """
    try:
        # Получаем имя пользователя из данных, которые нам передали
        user_name = user_data.get('first_name', 'Пользователь')

        # 1. Приветствие по времени суток
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = f"Доброе утро, {user_name}! ☀️"
        elif 12 <= hour < 18:
            time_greeting = f"Добрый день, {user_name}! ☕️"
        else:
            time_greeting = f"Добрый вечер, {user_name}! 🌙"

        # 2. Добавляем проактивное предложение
        # В будущем здесь будет анализ задач/событий на сегодня
        proactive_suggestion = "Готов помочь. <b>Что планируем сегодня — задачи, встречи, привычки?</b>"

        return f"{time_greeting}\n\n{proactive_suggestion}"

    except Exception as e:
        logger.error(f"Ошибка в get_greeting: {e}", exc_info=True)
        # Возвращаем стандартное приветствие в случае любой ошибки
        return f"С возвращением, {user_data.get('first_name', 'Пользователь')}!"