import os
import telebot
from telebot import types
import json
import pytz
from datetime import datetime, timedelta
from db import (
    get_users,
    get_user_events,
    update_event_notifyDate,
    update_event_status
)
from logger import setup_logger

logger = setup_logger()

TOKEN = "7948034303:AAFwvjyXLEdRtSVHusnQ7aLjnXQ5PhL1AEI"
bot = telebot.TeleBot(TOKEN)

users = get_users()
for user in users:
    try:
        user_id = user["id"]
        user_timezone = user["timezone"]
        user_events = get_user_events(user_id)
        if user_events:
            for event in user_events:
                try:
                    user_tz = pytz.timezone(user_timezone)
                    notify_date = event["notify_date"]
                    if isinstance(notify_date, str):
                        notify_date_naive = datetime.strptime(notify_date, "%Y-%m-%d %H:%M:%S")
                    else:
                        notify_date_naive = notify_date
                    notify_date_aware = user_tz.localize(notify_date_naive)
                    now_aware = datetime.now(pytz.utc).astimezone(user_tz)
                    if now_aware >= notify_date_aware:
                        next_notif = ""
                        if event["event_type"] == 'recurring':
                            try:
                                recurrence = json.loads(event["recurrence"])
                                interval = recurrence.get("interval")
                                frequency = recurrence.get("frequency")
                                if not isinstance(interval, int) or interval <= 0:
                                    raise ValueError(f"Некорректное значение interval: {interval}")

                                if frequency == "every_n_minutes":
                                    now_plus = now_aware + timedelta(minutes=interval)
                                elif frequency == "daily":
                                    now_plus = now_aware + timedelta(days=1)
                                elif frequency == "weekly":
                                    now_plus = now_aware + timedelta(weeks=1)
                                elif frequency == "monthly":
                                    year = now_aware.year
                                    month = now_aware.month + 1
                                    if month > 12:
                                        month = 1
                                        year += 1
                                    try:
                                        now_plus = now_aware.replace(year=year, month=month)
                                    except ValueError:
                                        now_plus = now_aware.replace(year=year, month=month, day=1)
                                elif frequency == "yearly":
                                    try:
                                        now_plus = now_aware.replace(year=now_aware.year + 1)
                                    except ValueError:
                                        now_plus = now_aware.replace(year=now_aware.year + 1, day=28)
                                else:
                                    raise ValueError(f"Неизвестная частота: {frequency}")
                                
                                update_event_notifyDate(event_id=event["id"],  notify_date=now_plus.isoformat())
                                next_notif = f"⏰ Следующее напоминание: {now_plus.strftime('%d.%m.%Y %H:%M')}"
                            except json.JSONDecodeError as e:
                                logger.error(f"Ошибка разбора recurrence JSON: {e}")
                            except Exception as e:
                                logger.error(f"Ошибка при обработке recurring события: {e}")
                        else:
                            update_event_status(event_id=event["id"], status=1)
                        event_title = event["title"]
                        message = (
                            f"📅 Напоминаю вам о событии\n"
                            f"<b>{event_title}</b>\n\n"
                            f"{next_notif}"
                        )
                        reply_markup = types.InlineKeyboardMarkup()
                        event_id = event["id"]
                        remove_event_data = f"rm_evnt_{event_id}"
                        reply_markup.add(types.InlineKeyboardButton("Удалить напоминание", callback_data=remove_event_data))
                        bot.send_message(
                            user["talagramID"], 
                            message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        print("Еще не время.")
                except Exception as e:
                    logger.error(f"Failed to parse user ID:{user_id} event \n {e}")
    except Exception as e:
        logger.error(f"Failed to parse user ID:{user_id}")

