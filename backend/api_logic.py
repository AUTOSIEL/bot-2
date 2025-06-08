import openai
import json
import os
from dotenv import load_dotenv
import logging

from functions import get_functions

# Загружаем переменные и настраиваем логгер
load_dotenv()
logger = logging.getLogger(__name__)

# Инициализируем клиента OpenAI со стандартным ключом
# Он автоматически подхватит OPENAI_API_KEY из .env файла
client = openai.OpenAI(
    # organization="org-KnDhFAL5KZ3A2YOCOuPbg6ia", # Этот параметр опционален для стандартных вызовов
    timeout=30.0
)

def request_ai(prompt, user_msg, msg_type, msg_history=None, thread_id=None):
    try:
        messages = [{"role": "system", "content": prompt}]
        if isinstance(msg_history, list):
            messages.extend(msg_history)
        messages.append({"role": "user", "content": user_msg})
        
        functions = get_functions()
        
        # --- СТАНДАРТНЫЙ, ПРАВИЛЬНЫЙ ВЫЗОВ API ---
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Новая, быстрая и дешевая модель
            messages=messages,
            tools=functions,
            tool_choice="auto",
            temperature=0.7,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # --- ОБРАБОТКА ОТВЕТА ---

        # Случай 1: Модель решила вызвать функцию
        if tool_calls:
            tool_call = tool_calls[0].function
            logger.info(f"AI decided to call a function: {tool_call.name}")
            result = {
                "type": 'function_call',
                "name": tool_call.name,
                "args": tool_call.arguments
            }
            return {"result": result}

        # Случай 2: Модель просто ответила текстом
        text_content = response_message.content
        logger.info(f"AI responded with a text message.")
        result = {
            "text": text_content,
            "type": 'message',
            "links": [] # Аннотаций больше не будет
        }
        return {"result": result}

    except Exception as e:
        logger.error(f"Error in request_ai: {e}", exc_info=True)
        # Возвращаем структуру по умолчанию, чтобы бот не падал
        return {
            "result": {
                "text": "Извините, произошла внутренняя ошибка при обращении к AI. Пожалуйста, попробуйте немного позже.",
                "type": "message",
                "links": [],
                "messages": [] 
            }
        }