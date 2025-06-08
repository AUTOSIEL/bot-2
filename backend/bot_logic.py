import telebot
import os
import json
import yaml
from datetime import datetime
import time
import subprocess
import speech_recognition as sr
import logging # <<< ИЗМЕНЕНИЕ: импортируем стандартный logging

from db import (
    get_or_create_user,
    get_db_connection,
    update_user_info,
    update_user_state,
    update_user_timezone,
    get_user_state,
    save_msg,
    get_user_data,
    save_event,
    save_note,
    save_task,
    get_msg_history_event,
    get_msg_history_note,
    get_last_history,
    update_event,
    update_note,
    update_task,
    delete_event,
    delete_task,
    delete_note,
    get_user_events,
    get_user_task,
    get_user_notes,
    delete_note,
    delete_user_and_data
    
)
# from logger import setup_logger # <<< ИЗМЕНЕНИЕ: этот импорт больше не нужен
from telebot import types
from AiRequests import request_ai
from helpers.get_system_prompt import get_system_prompt
from helpers.get_questions import get_questions
from helpers.smart_greeting import get_greeting


# --- Настройка ---
logger = logging.getLogger(__name__) # <<< ИЗМЕНЕНИЕ: получаем уже настроенный логгер

if not os.path.exists("voices"):
    os.makedirs("voices")

QUESTIONS = get_questions(types=types)

def save_user_profile_data(user_id, field, value):
    """Сохраняет одно поле в userInfo пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT userInfo FROM users WHERE talagramID = %s", (user_id,))
        result = cursor.fetchone()
        user_info = json.loads(result["userInfo"]) if result and result["userInfo"] else {}

        user_info[field] = value

        cursor.execute(
            "UPDATE users SET userInfo = %s WHERE talagramID = %s",
            (json.dumps(user_info, ensure_ascii=False), user_id),
        )
        conn.commit()
        logger.info(f"Updated profile for user {user_id}: set {field} = {value}")
    except Exception as e:
        logger.error(f"Error in save_user_profile_data for user {user_id}: {e}", exc_info=True)
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
# <<< КОНЕЦ НОВОЙ ФУНКЦИИ >>>


def save_answer(user_id, field, answer):
    # ... (эта функция у тебя уже есть, ее не трогаем)
    pass

# --- ЗАГРУЗКА ТРИГГЕРОВ ---
TRIGGERS = {}
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    trigger_file_path = os.path.join(current_dir, 'triggers.yaml')
    with open(trigger_file_path, 'r', encoding='utf-8') as f:
        TRIGGERS = yaml.safe_load(f)
    logger.info("Файл с триггерами triggers.yaml успешно загружен.")
except Exception as e:
    logger.error(f"Не удалось загрузить triggers.yaml: {e}")

def save_answer(user_id, field, answer):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # ... (остальной код функции без изменений)
    
    try:
        # Получаем текущие данные пользователя
        cursor.execute("SELECT userInfo FROM users WHERE talagramID = %s", (user_id,))
        result = cursor.fetchone()
        
        if result and result["userInfo"]:
            user_info = json.loads(result["userInfo"])
        else:
            user_info = {}
        
        # Обновляем конкретное поле
        user_info[field] = answer
        
        # Сохраняем обновленные данные обратно в базу
        cursor.execute(
            "UPDATE users SET userInfo = %s WHERE talagramID = %s",
            (json.dumps(user_info), user_id),
        )
        conn.commit()
        logger.info(f"Saved answer for user {user_id}: {field} = {answer}")
    
    except Exception as e:
        logger.error(f"Error saving answer for user {user_id}: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

def initialize_user_info(user_id):
    for field, _, _ in QUESTIONS:
        save_answer(user_id, field, None)

def check_new_user(user):
    is_new_user = get_or_create_user(user)
    return is_new_user

def check_user_info(user):
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT userInfo FROM users WHERE talagramID = %s", (user.id,))
        result = cursor.fetchone()
        
        if result and result["userInfo"]:
            try:
                user_info = json.loads(result["userInfo"])
                if not all(user_info.values()):
                    return {"userInfo": None, "state": get_user_state(user.id)}
                
                return {"userInfo": user_info, "state": get_user_state(user.id)}
            except json.JSONDecodeError:
                return {"userInfo": None, "state": get_user_state(user.id)}
        
        return {"userInfo": None, "state": get_user_state(user.id)}
    
    except Exception as e:
        logger.error(f"Error checking user info for user {user.id}: {e}")
        return {"userInfo": None, "state": None}
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def format_event_response(event_data):
    title = event_data.get('title', '—')
    
    start_date = event_data.get('start_date', 0)
    end_date = event_data.get('end_date', 0)
    notify_date = event_data.get('notify_date', 0)
    notify_before = event_data.get('notify_before', 0)
    event_type = event_data.get('event_type', 'single')

    type_text = 'Однократное 🕐' if event_type == 'single' else 'Регулярное 🔄'

    recurrence = ''
    if event_type == 'recurring' and 'recurrence' in event_data:
        freq = event_data['recurrence'].get('frequency', '—')
        interval = event_data['recurrence'].get('interval', '—')
        recurrence = f"\n🔁 <b>Повторение:</b> {freq}, каждые {interval}"

    message = (
        f"📅 <b>Событие:</b> {title}\n"
        f"⏰ <b>Начало:</b> {start_date}\n"
        f"🏁 <b>Окончание:</b> {end_date}\n"
        f"📅 <b>Когда напомнить:</b> {notify_date}\n"
        f"🔔 <b>Напомнить за:</b> {notify_before} мин\n"
        f"📌 <b>Тип:</b> {type_text}{recurrence}"
    )

    return message

def format_note_response(note_data):
    title = note_data.get('title', '—')
    content = note_data.get('content', '—')

    message = (
        "📌<b>Заметка сохранена</b>\n\n"
        "<b>Название:</b>\n"
        f"{title}\n\n"
        "<b>Содержание:</b>\n"
        f"{content}\n\n"
    )

    return message

def format_task_response(task_data):
    title = task_data.get('title', '—')
    content = task_data.get('content', '—')

    message = (
        "✅<b>Задача сохранена</b>\n\n"
        "<b>Название:</b>\n"
        f"{title}\n\n"
        "<b>Содержание:</b>\n"
        f"{content}\n\n"
    )

    return message

def checkStatusUser(telegramID, bot_instance, message):
    """
    Проверяет статус пользователя. В текущей версии доступ разрешен всем.
    Всегда возвращает False, чтобы никогда не блокировать пользователя.
    """
    try:
        # Пытаемся получить данные, чтобы убедиться, что пользователь существует.
        # Если нет, get_or_create_user в send_welcome его создаст.
        user_data = get_user_data(telegramID)
        if user_data is None:
            # Это нормально для нового пользователя, пропускаем его дальше.
            return False

        # Если у пользователя по какой-то причине статус 0, временно пропускаем.
        # В будущем здесь можно будет реализовать логику бана.
        if user_data.get("status") == 0:
            logger.warning(f"Пользователь {telegramID} имеет статус 0, но доступ разрешен.")
            return False

        return False # Пропускаем всех остальных

    except Exception as e:
        logger.error(f"Критическая ошибка в checkStatusUser для {telegramID}: {e}", exc_info=True)
        # В случае ошибки лучше заблокировать пользователя, чтобы избежать проблем.
        bot_instance.send_message(message.chat.id, "Произошла временная ошибка при проверке вашего доступа.")
        return True
# Регистрация обработчиков
def handle_contextual_trigger(bot, message, trigger):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        if not user_data: return

        logger.info(f"Сработал триггер '{trigger.get('name')}' для user_id: {user_id}")
        bot.send_chat_action(message.chat.id, 'typing')

        # 1. Собираем всю рабочую память
        all_events = get_user_events(user_data.get("id"))
        all_tasks = get_user_task(user_data.get("id"))
        all_notes = get_user_notes(user_data.get("id"))

        # 2. Формируем специальный промпт для AI
        special_prompt = f"""
        {trigger.get('response_prompt')}

        Вот полные данные из рабочей памяти пользователя:
        - События: {json.dumps(all_events, ensure_ascii=False, default=str)}
        - Задачи: {json.dumps(all_tasks, ensure_ascii=False, default=str)}
        - Заметки: {json.dumps(all_notes, ensure_ascii=False, default=str)}

        Твоя задача: проанализируй все эти данные, выбери только самое релевантное для текущего контекста и сформулируй единый, полезный и проактивный ответ в HTML-формате.
        """
        
        # 3. Вызываем AI только для форматирования и синтеза ответа
        ai_response = request_ai(special_prompt, message.text, "context_formatter")
        
        if ai_response and ai_response.get("result") and ai_response["result"].get("text"):
            text_to_reply = ai_response["result"]["text"]
            bot.reply_to(message, text_to_reply, parse_mode='HTML')
            save_msg(user_data.get("id"), text_to_reply, True, None, None, None)
        else:
            bot.reply_to(message, "Понял тебя. Сейчас обработаю.")

    except Exception as e:
        logger.error(f"Ошибка в handle_contextual_trigger: {e}", exc_info=True)
        bot.reply_to(message, "Что-то пошло не так при обработке твоего запроса.")

def register_handlers(bot):

    def ask_next_question(user_id):
        try:
            state = get_user_state(user_id)
            if not state: return
            current_question = state.get("current_question", 0)
            if current_question >= len(QUESTIONS):
                complete_user_info_collection(user_id)
                return
            field, question_text, reply_markup = QUESTIONS[current_question]
            bot.send_message(state["chat_id"], question_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error sending question to user {user_id}: {e}", exc_info=True)
            update_user_state(user_id, None)

    def complete_user_info_collection(user_id):
        try:
            # Этап 4: Первое действие и постановка на рельсы
            bot.send_message(user_id, "Готово! Все настройки сохранены.")
            time.sleep(1)
            bot.send_message(user_id, "Давайте сразу попробуем. Какая первая мысль или задача, которую нужно записать, чтобы не забыть?\n\nНапишите что угодно, например: <i>«Напомнить завтра в 11:00 проверить аналитику»</i> или просто <i>«идея для нового проекта»</i>.", parse_mode="HTML")
            update_user_state(user_id, {'ai_request': True}) # Переводим в обычный режим
        except Exception as e:
            logger.error(f"Error in complete_user_info_collection for user {user_id}: {e}", exc_info=True)

    def add_event_func(user):
        update_user_state(user.id, {'ai_request': True})
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data="cancel"))
        bot.send_message(user.id, "Напишите подробнее, какое событие вы хотите запланировать...", parse_mode="HTML", reply_markup=markup)

    def add_note_func(user):
        update_user_state(user.id, {'ai_request': True})
        bot.send_message(user.id, "✍️ Напишите текст вашей заметки...")
        
    def handle_registered_user(message, user_info):
        # ... (здесь твой код handle_registered_user без изменений)
        pass

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        try:
            user = message.from_user
            get_or_create_user(user)
            logger.info(f"Processing /start for user: ID={user.id}, Username={user.username}")
            
            # Этап 1: "Рукопожатие"
            bot.send_message(message.chat.id, 
                "Привет! Я — MindMy AI, ваш персональный AI-ассистент, созданный, чтобы стать вашим «вторым мозгом».\n\n"
                "Я помогаю управлять задачами, помнить всё важное и фокусироваться на главном."
            )
            time.sleep(0.5)
            bot.send_message(message.chat.id, "Для начала, как я могу к вам обращаться?")
            
            update_user_state(user.id, {'onboarding_step': 'awaiting_name'})
        except Exception as e:
            logger.error(f"Критическая ошибка в send_welcome: {e}", exc_info=True)
            bot.send_message(message.chat.id, "⚠️ Произошла серьезная ошибка. Пожалуйста, попробуйте перезапустить меня командой /start.")

    @bot.message_handler(commands=['reset'])
    def reset_user_handler(message):
        try:
            user_id = message.from_user.id
            markup = types.InlineKeyboardMarkup()
            confirm_button = types.InlineKeyboardButton("Да, полностью стереть мой профиль", callback_data="confirm_reset_yes")
            cancel_button = types.InlineKeyboardButton("Нет, отмена", callback_data="confirm_reset_no")
            markup.add(confirm_button, cancel_button)
            
            bot.reply_to(message, "⚠️ **ВНИМАНИЕ!**\n\nВы уверены, что хотите полностью стереть свой профиль и всю связанную с ним историю?\n\n**Это действие необратимо.**", reply_markup=markup, parse_mode="HTML")
        
        except Exception as e:
            logger.error(f"Ошибка в reset_user_handler: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка при вызове команды сброса.")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        try:
            user = message.from_user
            user_id = user.id
            state = get_user_state(user_id)

            if checkStatusUser(user_id, bot, message): return

            # --- Логика Онбординга ---
            if state and 'onboarding_step' in state:
                step = state['onboarding_step']

                if step == 'awaiting_name':
                    save_user_profile_data(user_id, 'name', message.text)
                    bot.send_message(user_id, f"Приятно познакомиться, {message.text}!")
                    time.sleep(0.5)
                    bot.send_message(user_id, "Теперь важный момент: чтобы я мог корректно работать с часовыми поясами и напоминаниями, подскажите, пожалуйста, ваш город.")
                    update_user_state(user_id, {'onboarding_step': 'awaiting_city'})
                    return

                elif step == 'awaiting_city':
                    bot.send_chat_action(user_id, 'typing')
                    ai_response = request_ai(f"Определи часовой пояс в формате IANA для города: {message.text}. Ответь только названием таймзоны.", message.text, "timezone_detector")
                    timezone = ai_response.get("result", {}).get("text", "Error").strip()

                    if "Error" in timezone or "/" not in timezone:
                        bot.send_message(user_id, "Не удалось определить часовой пояс. Попробуйте ввести другой известный город.")
                        return

                    save_user_profile_data(user_id, 'timezone', timezone)
                    update_user_timezone(user_id, timezone)
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Да, всё верно", callback_data="confirm_city"))
                    markup.add(types.InlineKeyboardButton("Изменить город", callback_data="change_city"))
                    bot.send_message(user_id, f"Отлично! Я установил ваш часовой пояс на <b>{timezone}</b>. Теперь все напоминания будут точными.\n\nВсё верно?", reply_markup=markup, parse_mode="HTML")
                    update_user_state(user_id, {'onboarding_step': 'awaiting_city_confirmation'})
                    return

                elif step == 'awaiting_role':
                    save_user_profile_data(user_id, 'role_description', message.text)
                    bot.send_message(user_id, "Принято. Теперь второй вопрос: с какими инструментами вы работаете чаще всего? (Notion, Jira, Figma и т.д.)")
                    update_user_state(user_id, {'onboarding_step': 'awaiting_tools'})
                    return

                elif step == 'awaiting_tools':
                    save_user_profile_data(user_id, 'tools', message.text)
                    bot.send_message(user_id, "Понял. И последний вопрос: есть ли у вас «золотые часы» для работы, когда меня лучше не беспокоить?")
                    update_user_state(user_id, {'onboarding_step': 'awaiting_focus_hours'})
                    return

                elif step == 'awaiting_focus_hours':
                    save_user_profile_data(user_id, 'focus_hours', message.text)
                    complete_user_info_collection(user_id)
                    return
                
            # --- Старая логика для зарегистрированных пользователей ---
            user_info_check = check_user_info(user)
            if user_info_check and user_info_check.get("userInfo"):
                handle_registered_user(message, user_info_check.get("userInfo"))
            else:
                 send_welcome(message)

        except Exception as e:
            logger.error(f"Критическая ошибка в handle_all_messages: {e}", exc_info=True)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        try:
            user_id = call.from_user.id
            
            if call.data == "confirm_city":
                bot.edit_message_text("Отлично, с базовой настройкой закончили!", call.message.chat.id, call.message.message_id)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Да, давайте настроим", callback_data="start_advanced_onboarding"))
                markup.add(types.InlineKeyboardButton("Пропустить, начну пользоваться", callback_data="skip_advanced_onboarding"))
                bot.send_message(call.message.chat.id, "Мы можем остановиться на этом. Но если вы уделите ещё 60 секунд, я смогу стать гораздо эффективнее. Хотите немного настроить меня под себя?", reply_markup=markup)
                update_user_state(user_id, {'onboarding_step': 'awaiting_advanced_choice'})

            elif call.data == "change_city":
                 bot.edit_message_text("Хорошо, введите ваш город еще раз.", call.message.chat.id, call.message.message_id)
                 update_user_state(user_id, {'onboarding_step': 'awaiting_city'})
            
            elif call.data == "start_advanced_onboarding":
                bot.edit_message_text("Супер! Кратко, чтобы я лучше понимал ваши приоритеты:", call.message.chat.id, call.message.message_id)
                time.sleep(0.5)
                bot.send_message(user_id, "1. Ваша основная роль? (Например: маркетолог, продакт-менеджер, разработчик).")
                update_user_state(user_id, {'onboarding_step': 'awaiting_role'})

            elif call.data == "skip_advanced_onboarding":
                bot.edit_message_text("Понял вас. Пропускаем углубленную настройку.", call.message.chat.id, call.message.message_id)
                complete_user_info_collection(user_id)
            
            elif call.data == "confirm_reset_yes":
                if delete_user_and_data(user_id):
                    bot.edit_message_text("✅ Ваш профиль и все данные были полностью удалены. Начните диалог с команды /start, чтобы создать новый профиль.", call.message.chat.id, call.message.message_id)
                else:
                    bot.edit_message_text("⚠️ Произошла ошибка при удалении вашего профиля.", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)

            elif call.data == "confirm_reset_no":
                bot.edit_message_text("Действие отменено.", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)
            
            # ... (остальные твои callback-обработчики)
        
        except Exception as e:
            logger.error(f"Ошибка в handle_query: {e}", exc_info=True)
            bot.answer_callback_query(call.id, text="Произошла ошибка")

    def complete_user_info_collection(bot, user_id):
        update_user_state(user_id, None)
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Запланировать событие", callback_data="add_event"))
            markup.add(types.InlineKeyboardButton("Создать заметку", callback_data="add_note"))
            markup.add(types.InlineKeyboardButton("Создать задачу", callback_data="add_task"))
            web_app = types.WebAppInfo("https://mindmyai.ru/")
            markup.add(types.InlineKeyboardButton("Открыть приложение", web_app=web_app))
            bot.send_message(
                user_id,
                "🎉 Спасибо! Вся информация сохранена. \n\n" \
                "Вот что я могу для вас сделать:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Error sending completion message to user {user_id}: {e}")
        logger.info(f"User info completed for user ID: {user_id}")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        try:
            user = message.from_user
            user_id = user.id
            if checkStatusUser(user_id, bot, message): return
            
            logger.info(f"Message from {user_id} ({user.username}): {message.text}")
            
            # --- ЛОГИКА ДИСПЕТЧЕРА ТРИГГЕРОВ ---
            user_message_lower = message.text.lower()
            triggered = False
            if 'triggers' in TRIGGERS:
                for trigger in TRIGGERS.get('triggers', []):
                    for pattern in trigger.get('patterns', []):
                        if pattern in user_message_lower:
                            # Вызываем универсальный обработчик
                            handle_contextual_trigger(bot, message, trigger)
                            triggered = True
                            break
                    if triggered: break
            
            # Если ни один триггер не сработал, идем по старой логике
            if not triggered:
                user_info_check = check_user_info(user)
                if user_info_check is None:
                    bot.send_message(message.chat.id, "⚠️ Произошла ошибка при получении данных вашего профиля.")
                    return

                state = user_info_check.get("state")
                user_info = user_info_check.get("userInfo")

                if state and state.get("ai_request") is None:
                    handle_questionnaire_flow(bot, message, user_id, state)
                    return

                if user_info is None:
                    suggest_questionnaire_start(message, user)
                    return
                
                # Передаем управление в обычный обработчик с AI
                handle_registered_user(message, user_info)

        except Exception as e:
            logger.error(f"Критическая ошибка в handle_all_messages для user {message.from_user.id}: {e}", exc_info=True)

    def suggest_questionnaire_start(bot, message, user):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Заполнить анкету", callback_data="start_questionnaire"))
        
        bot.send_message(
            chat_id=message.chat.id,
            text=f"{user.first_name}, я вижу, что вы еще не заполнили анкету. Это поможет мне лучше вам помогать!",
            reply_markup=markup,
        )

    def handle_questionnaire_flow(bot, message, user_id, state):
        current_question = state.get("current_question", 0)
        if current_question < len(QUESTIONS):
            field, _, reply_markup = QUESTIONS[current_question]
            save_answer(user_id, field, message.text)

            if current_question == 6:
                ai_response = request_ai("Пришли в ответ только timezone в формате IANA на 2025 год по запросу пользователя. Не используй устаревшие или некорректные варианты вроде Europe/Yekaterinburg.Примеры правильных ответов: Asia/Yekaterinburg, Europe/Moscow, America/New_York.", message.text, "default")
                if ai_response and "result" in ai_response:
                    result = ai_response['result']['text']
                    update_user_timezone(user_id, result)
            
            if reply_markup:
                bot.send_message(message.chat.id, "Ответ принят!", reply_markup=types.ReplyKeyboardRemove())
            
            new_state = {
                "current_question": current_question + 1,
                "chat_id": message.chat.id,
            }
            update_user_state(user_id, new_state)
            ask_next_question(bot, user_id)

    def handle_registered_user(message, user_info):
        talagramID = message.from_user.id
        if checkStatusUser(talagramID, bot, message):
            return
        user_data = get_user_data(talagramID)
        name = user_info.get("name", message.from_user.first_name)
        state = get_user_state(talagramID)
        if state is None:
            state = {}
            update_user_state(talagramID, state)
        system_prompt = get_system_prompt(user_data, state)
        checkAiRequest = state.get("ai_request", None)
        if checkAiRequest:
            history_records = get_last_history(user_data["id"])
            history_records_arr = []
            if history_records:
                for record in history_records:
                    history_records_arr.append({
                        "role": "assistant" if record["is_bot"] else "user",
                        "content": record["msg"]
                    })
                
            msg_history = history_records_arr
            save_msg(user_data["id"], message.text, False, None, None, None)
        
            ai_response = request_ai(system_prompt, message.text, "default", msg_history=msg_history)
            if ai_response and "result" in ai_response:
                try:
                    if ai_response['result']['type'] == 'function_call':
                        if ai_response['result']['name'] == 'create_event':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['reminders']:
                                event_data = save_event(user_data["id"])
                                update_success = update_event(event_data["id"], event)
                                if update_success:
                                         bot.reply_to(message, format_event_response(event), parse_mode="HTML")
                                         save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, event_data["id"], None, None)
                                else:
                                    bot.reply_to(message, "⚠️ Ошибка при обновлении события.")
                        elif ai_response['result']['name'] == 'update_event':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['reminders']:
                                update_success = update_event(event.get('id'), event)
                                if update_success:
                                         bot.reply_to(message, f"Напоминание обновлено: \n\n{format_event_response(event)}", parse_mode="HTML")
                                         save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, event.get('id'), None, None)
                                else:
                                    bot.reply_to(message, "⚠️ Ошибка при обновлении события.")
                        elif ai_response['result']['name'] == 'remove_event':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['reminders']:
                                update_success = delete_event(event.get('id'))
                                bot.reply_to(message, "❌ Напоминание было удалено.", parse_mode="HTML")
                                save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, event.get('id'), None, None)
                        elif ai_response['result']['name'] == 'create_task':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['tasks']:
                                task_data = save_task(user_data["id"])
                                update_success = update_task(task_id=task_data["id"], task_data=event)
                                if update_success:
                                    bot.reply_to(message, format_task_response(event), parse_mode="HTML")
                                    save_msg(user_data["id"], json.dumps(result_data, ensure_ascii=False), True, None, task_data["id"], None)
                                else:
                                    bot.reply_to(message, "⚠️ Ошибка при обновлении задачи.")
                        elif ai_response['result']['name'] == 'update_task':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['tasks']:
                                update_success = update_task(task_id=event.get('id'), task_data=event)
                                if update_success:
                                    bot.reply_to(message, f"Задача обновлена: \n\n{format_task_response(event)}", parse_mode="HTML")
                                    save_msg(user_data["id"], json.dumps(result_data, ensure_ascii=False), True, None, event.get('id'), None)
                                else:
                                    bot.reply_to(message, "⚠️ Ошибка при обновлении задачи.")
                        elif ai_response['result']['name'] == 'remove_task':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['tasks']:
                                update_success = delete_task(event.get('id'))
                                bot.reply_to(message, "❌ Задача была удалена.", parse_mode="HTML")
                                save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, event.get('id'), None, None)
                        elif ai_response['result']['name'] == 'create_note':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['notes']:
                                note_data = save_note(user_data["id"])
                                update_success = update_note(note_id=note_data["id"], note_data=event)
                                if update_success:
                                    bot.reply_to(message, format_note_response(event), parse_mode="HTML")
                                    save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, None, None, note_data["id"])
                                else:
                                    bot.reply_to(message, "⚠️ Ошибка при обновлении заметки.")
                        elif ai_response['result']['name'] == 'update_note':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['notes']:
                                update_success = update_note(note_id=event.get('id'), note_data=event)
                                if update_success:
                                    bot.reply_to(message, format_note_response(event), parse_mode="HTML")
                                    save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, None, None, event.get('id'))
                                else:
                                    bot.reply_to(message, "⚠️ Ошибка при обновлении заметки.")
                        elif ai_response['result']['name'] == 'remove_note':
                            result_data = json.loads(ai_response['result']['args'])
                            for event in result_data['notes']:
                                update_success = delete_note(event.get('id'))
                                bot.reply_to(message, "❌ Заметка была удалена.", parse_mode="HTML")
                                save_msg(user_data["id"], json.dumps(event, ensure_ascii=False), True, event.get('id'), None, None)
                    else:
                        save_msg(user_data["id"], f"{ai_response['result']['text']}", True, None, None, None)
                        bot.reply_to(message, ai_response['result']['text'], parse_mode=None)
                except json.JSONDecodeError:
                    bot.reply_to(message, f"{ai_response['result']}")
                    save_msg(user_data["id"], f"{ai_response['result']}", True, None, None, None)
            else:
                bot.reply_to(message, "⚠️ Не удалось сформировать ответ. Попробуйте позже.")
                save_msg(user_data["id"], "⚠️ Не удалось сформировать ответ. Попробуйте позже.", True, None, None, None)
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Запланировать событие", callback_data="add_event"))
            markup.add(types.InlineKeyboardButton("Создать заметку", callback_data="add_note"))
            markup.add(types.InlineKeyboardButton("Создать задачу", callback_data="add_task"))
            web_app = types.WebAppInfo("https://mindmyai.ru/")
            markup.add(types.InlineKeyboardButton("Открыть приложение", web_app=web_app))
            bot.reply_to(
                message,
                f"{name}, чем могу помочь?",
                reply_markup=markup,
            )
            save_msg(user_data["id"], f"{name}, чем могу помочь?", True, None, None, None)
            update_user_state(talagramID, {'ai_request': True})

    @bot.callback_query_handler(func=lambda call: call.data == "start_questionnaire")
    def start_questionnaire(call):
        user = call.from_user
        initialize_user_info(user.id)
        update_user_state(user.id, {"current_question": 0, "chat_id": call.message.chat.id})
        ask_next_question(bot, user.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"{user.first_name}, начинаем заполнение анкеты!",
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("rm_evnt_"))
    def handle_delete_event(call):
        try:
            event_id = int(call.data.split("_")[2])
            user = call.from_user

            delete_event(event_id)
            bot.answer_callback_query(call.id, text="Напоминание удалено")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Это напоминание было удалено."
            )

        except Exception as e:
            bot.answer_callback_query(call.id, text="Ошибка при удалении")
            logger.error(f"Error remove event {event_id} to user {user.id}: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel"))
    def cancel(call):
        try:
            user = call.from_user
            update_user_state(user.id, {'ai_request': True})
            bot.answer_callback_query(call.id, text="Действие отменено")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Дейтсвие отменено, можете продолжить общение"
            )

        except Exception as e:
            bot.answer_callback_query(call.id, text="Ошибка при отмене")
            logger.error(f"Error cancel action to user {user.id}: {e}")

    @bot.callback_query_handler(func=lambda call: call.data == "add_event")
    def add_event(call):
        bot.answer_callback_query(call.id)
        user = call.from_user
        add_event_func(user)

    def add_event_func(user):
        user_data = get_user_data(user.id)
        update_user_state(user.id, {'ai_request': True})
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data="cancel"))
        bot.send_message(
            user.id,
            "Напишите подробнее, какое событие вы хотите запланировать?\n"
            "Укажите следующее:\n\n"
            
            "📅 <b>Дата</b> события: когда должно произойти событие?\n"
            "🕗 <b>Время</b>: во сколько?\n"
            "🔔 <b>Напоминание</b>: за сколько минут/часов/дней вас предупредить?\n"
            "🔁 <b>Периодичность</b>: это разовое событие или повторяющееся? "
            "Если повторяется — уточните, как часто (например, ежедневно, каждые 10 минут, раз в неделю и т.п.)\n\n"
            
            "Пример:\n"
            "Завтра в 15:00 у меня встреча с командой. Напомни за 15 минут. Это одноразовое событие.",
            parse_mode="HTML",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data == "add_note")
    def add_note(call):
        bot.answer_callback_query(call.id)
        user = call.from_user
        add_event_func(user)

    def add_note_func(user):
        user_data = get_user_data(user.id)
        update_user_state(user.id, {'ai_request': True})
        bot.send_message(
            user.id,
            "✍️ Напишите текст вашей заметки. "
            "Можете указать заголовок, содержание, теги или что-то ещё — как вам удобно.\n\n"
            "Пример:\n"
            "Заголовок: Список покупок\n"
            "Содержание:\n"
            "Обои\n"
            "Клей\n"
            "Плитка\n"
            "Теги: #ремонт"
        )

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        user_id = call.from_user.id
        state = get_user_state(user_id)
        
        if state and 'current_question' in state:
            current_question = state['current_question']
            field, _, _ = QUESTIONS[current_question]

            save_answer(user_id, field, call.data)

            new_state = {
                "current_question": current_question + 1,
                "chat_id": call.message.chat.id,
            }
            update_user_state(user_id, new_state)
            ask_next_question(bot, user_id)

            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )

    def convert_ogg_to_wav(input_path, output_path):
        command = ['ffmpeg', '-i', input_path, output_path]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def recognize_speech(wav_path):
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language="ru-RU")
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Ошибка распознавания речи: {e}")
            return None

    @bot.message_handler(content_types=['voice'])
    def handle_voice_message(message):
        user = message.from_user
        if checkStatusUser(user.id, bot, message):
            return
        user_id = user.id
        logger.info(f"Voice message from {user_id} ({user.username})")
        ogg_path = wav_path = None
        try:
            file_info = bot.get_file(message.voice.file_id)
            file_path = file_info.file_path
            file = bot.download_file(file_path)

            ogg_path = f"voices/{user_id}_{int(time.time())}.ogg"
            with open(ogg_path, 'wb') as f:
                f.write(file)

            wav_path = ogg_path.replace('.ogg', '.wav')
            convert_ogg_to_wav(ogg_path, wav_path)

            text = recognize_speech(wav_path)

            state = get_user_state(user_id)
            if state is None:
                update_user_state(user_id, {'ai_request': True})

            
            if text:
                logger.info(f"Распознанный текст от {user_id}: {text}")
                message.text = text
                handle_all_messages(message)
            else:
                bot.send_message(message.chat.id, "Не удалось распознать голосовое сообщение. Попробуйте ещё раз.")

        except Exception as e:
            logger.exception(f"Ошибка обработки голосового сообщения от {user_id}: {e}")
            bot.send_message(message.chat.id, "⚠️ Произошла ошибка при обработке голосового сообщения.")

        finally:
            for path in [ogg_path, wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                        logger.info(f"Удалён временный файл: {path}")
                    except Exception as del_err:
                        logger.warning(f"Не удалось удалить файл {path}: {del_err}")