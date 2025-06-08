# models/User.py
import logging

# Получаем логгер, который настроен в app.py
logger = logging.getLogger(__name__)

class User:
    def __init__(self, user_data):
        if isinstance(user_data, dict):
            # Если это словарь (например, от check_user_info)
            self.id = user_data.get('id')
            self.is_bot = user_data.get('is_bot')
            self.first_name = user_data.get('first_name')
            self.last_name = user_data.get('last_name')
            self.username = user_data.get('username')
            self.language_code = user_data.get('language_code')
        else:
            # Если это объект message.from_user
            self.id = getattr(user_data, 'id', None)
            self.is_bot = getattr(user_data, 'is_bot', None)
            self.first_name = getattr(user_data, 'first_name', None)
            self.last_name = getattr(user_data, 'last_name', None)
            self.username = getattr(user_data, 'username', None)
            self.language_code = getattr(user_data, 'language_code', None)
        
        # Логируем только после того, как все атрибуты установлены
        logger.info(f"User object created/updated for ID: {self.id}, Username: {self.username}")