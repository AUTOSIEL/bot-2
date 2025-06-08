import os
import json
from datetime import datetime
from db import get_user_events, get_user_notes, get_user_task
import logging

# Получаем уже настроенный в app.py логгер
logger = logging.getLogger(__name__)

def get_system_prompt(user_data, state):
    # Определяем путь к файлу с шаблоном промпта
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file_path = os.path.join(current_dir, 'system_prompt.txt')
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except Exception as e:
        logger.error(f"Не удалось прочитать system_prompt.txt: {e}")
        prompt_template = "Ты — MindMy AI, помоги пользователю {user_name}."

    # 1. Безопасно получаем ID пользователя
    user_id_internal = user_data.get('id') if isinstance(user_data, dict) else None

    # 2. Получаем актуальные данные из БД
    user_events_data = get_user_events(user_id_internal) if user_id_internal else []
    user_tasks_data = get_user_task(user_id_internal) if user_id_internal else []
    user_notes_data = get_user_notes(user_id_internal) if user_id_internal else []
    
    # 3. Форматируем данные анкеты для подстановки в промпт
    user_info = {}
    if isinstance(user_data, dict):
        user_info_str = user_data.get('userInfo', '{}')
        try:
            user_info = json.loads(user_info_str) if user_info_str and isinstance(user_info_str, str) else {}
        except (json.JSONDecodeError, TypeError):
            user_info = {}

    user_profile_formatted = "\n".join([f"- {key.replace('_', ' ').capitalize()}: {value}" for key, value in user_info.items() if value])

    # 4. Готовим остальные данные для подстановки
    events_json = json.dumps(user_events_data, ensure_ascii=False, indent=2, default=str)
    tasks_json = json.dumps(user_tasks_data, ensure_ascii=False, indent=2, default=str)
    notes_json = json.dumps(user_notes_data, ensure_ascii=False, indent=2, default=str)
    
    user_timezone = user_info.get("timezone", "Не указан")
    current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_name_to_format = user_data.get('first_name', 'Пользователь') if isinstance(user_data, dict) else 'Пользователь'

    # 5. Подставляем все данные в шаблон
    try:
        final_prompt = prompt_template.format(
            user_name=user_name_to_format,
            current_datetime=current_datetime_str,
            user_timezone=user_timezone,
            user_profile=user_profile_formatted if user_profile_formatted else "Анкета не заполнена.",
            user_events=events_json,
            user_tasks=tasks_json,
            user_notes=notes_json
        )
    except KeyError as e:
        logger.error(f"Ошибка форматирования промпта: отсутствует ключ {e} в system_prompt.txt.")
        final_prompt = f"Ошибка форматирования промпта. Базовый промпт: Ты — MindMy AI."

    return final_prompt