import mysql.connector
import os
import json
import logging
from logger import setup_logger
from datetime import datetime
from models.User import User

logger = logging.getLogger(__name__)

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="mindmyai",
        password="lI2wJ2tK7p",
        database="mindmyai"
    )
    return connection

def get_or_create_user(user):
    user = User(user)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT talagramID FROM users WHERE talagramID = %s", (user.id,))
    existing_user = cursor.fetchone()

    if existing_user:
        query = """
        UPDATE users
        SET username = %s, first_name = %s, last_name = %s
        WHERE talagramID = %s
        """
        cursor.execute(query, (
            user.username,
            user.first_name,
            user.last_name,
            user.id
        ))
        is_new_user = False
    else:
        query = """
        INSERT INTO users (talagramID, username, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            user.id,
            user.username,
            user.first_name,
            user.last_name
        ))
        is_new_user = True

    conn.commit()
    cursor.close()
    conn.close()

    return is_new_user

def update_user_info(user_id, user_info):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        UPDATE users
        SET userInfo = %s
        WHERE id = %s
        """
        cursor.execute(query, (json.dumps(user_info), user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Updated info for user {user_id}: {user_info}")
        return user_info
    except Exception as e:
        logger.error(f"Error updating info for user {user_id}: {e}")
        raise Exception(f"Ошибка при обновлении userInfo: {e}")
    
def update_user_state(user_id, state):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if state is None:
            cursor.execute("UPDATE users SET state = NULL WHERE talagramID = %s", (user_id,))
        else:
            cursor.execute(
                "UPDATE users SET state = %s WHERE talagramID = %s",
                (json.dumps(state), user_id),
            )
        conn.commit()
        logger.info(f"Updated state for user {user_id}: {state}")
    
    except Exception as e:
        logger.error(f"Error updating state for user {user_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_user_timezone(user_id, timezone):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET timezone = %s WHERE talagramID = %s",
            (timezone, user_id),
        )
        conn.commit()
        logger.info(f"Updated timezone for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error updating state for user {user_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_event_notifyDate(event_id, notify_date):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE events SET notify_date = %s WHERE id = %s",
            (notify_date, event_id),
        )
        conn.commit()
        logger.info(f"Updated notify date for event {event_id}: {notify_date}")
    
    except Exception as e:
        logger.error(f"Error updating notify date for event {event_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_event_status(event_id, status):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE events SET status = %s WHERE id = %s",
            (status, event_id),
        )
        conn.commit()
        logger.info(f"Updated status for event {event_id}: {status}")
    
    except Exception as e:
        logger.error(f"Error updating status for event {event_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_event(event_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM events WHERE id = %s",
            (event_id,),
        )
        conn.commit()
        logger.info(f"Remove event {event_id}")
    
    except Exception as e:
        logger.error(f"Error removed event {event_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_note(note_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notes WHERE id = %s",
            (note_id,),
        )
        conn.commit()
        logger.info(f"Remove note {note_id}")
    
    except Exception as e:
        logger.error(f"Error removed note {note_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_task(task_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM task WHERE id = %s",
            (task_id,),
        )
        conn.commit()
        logger.info(f"Remove task {task_id}")
    
    except Exception as e:
        logger.error(f"Error removed task {task_id}: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_state(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT state 
            FROM users 
            WHERE talagramID = %s
        """, (user_id,))
        result = cursor.fetchone()
        if result and result["state"]:
            try:
                return json.loads(result["state"])
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON state for user {user_id}. State: {result['state']}")
                return None
        return None
    except Exception as e:
        logger.error(f"Error getting user state for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_data(talagramID):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM users 
            WHERE talagramID = %s
        """, (talagramID,))
        result = cursor.fetchone()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting user data for user {talagramID}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_users():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE status = 1")
        result = cursor.fetchall()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_events(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM events 
            WHERE user_id = %s AND status = 0
        """, (user_id,))
        result = cursor.fetchall()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting events for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_notes(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM notes 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchall()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting notes for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_task(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM task 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchall()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting notes for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_event(event_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM events 
            WHERE id = %s
        """, (event_id,))
        result = cursor.fetchone()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_note(note_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM notes 
            WHERE id = %s
        """, (note_id,))
        result = cursor.fetchone()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting note {note_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_task(task_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM task 
            WHERE id = %s
        """, (task_id,))
        result = cursor.fetchone()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_msg_history_event(user_id, event_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM history_msgs 
            WHERE user_id = %s AND event_id = %s
        """, (user_id, event_id))
        result = cursor.fetchall()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting event msgs history for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_msg_history_note(user_id, note_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM history_msgs 
            WHERE user_id = %s AND note_id = %s
        """, (user_id, note_id))
        result = cursor.fetchall()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting note msgs history for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_msg(user_id, msg, is_bot, event_id, task_id, note_id = None):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        INSERT INTO history_msgs (user_id, is_bot, msg, event_id, task_id, note_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            user_id,
            is_bot,
            msg,
            event_id,
            task_id,
            note_id
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error save msg for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_last_history(user_id, limit=100):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM history_msgs 
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        result = cursor.fetchall()
        return result[::-1] if result else None

    except Exception as e:
        logger.error(f"Error getting msg history for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_event(user_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        INSERT INTO events (user_id)
        VALUES (%s)
        """
        cursor.execute(query, (user_id,))
        conn.commit()

        cursor.execute("""
            SELECT id
            FROM events
            WHERE id = LAST_INSERT_ID()
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info(f"Event saved and retrieved for user {user_id}: {result}")
            return result
        return None
    except Exception as e:
        logger.error(f"Error save event for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_note(user_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        INSERT INTO notes (user_id)
        VALUES (%s)
        """
        cursor.execute(query, (user_id,))
        conn.commit()

        cursor.execute("""
            SELECT id
            FROM notes
            WHERE id = LAST_INSERT_ID()
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info(f"Note saved and retrieved for user {user_id}: {result}")
            return result
        return None
    except Exception as e:
        logger.error(f"Error save note for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_task(user_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        INSERT INTO task (user_id)
        VALUES (%s)
        """
        cursor.execute(query, (user_id,))
        conn.commit()

        cursor.execute("""
            SELECT id
            FROM task
            WHERE id = LAST_INSERT_ID()
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info(f"Note saved and retrieved for user {user_id}: {result}")
            return result
        return None
    except Exception as e:
        logger.error(f"Error save task for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_event(event_id, event_data):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE events
            SET title = %s,
                start_date = FROM_UNIXTIME(%s),
                end_date = FROM_UNIXTIME(%s),
                notify_before = %s,
                notify_date = FROM_UNIXTIME(%s),
                event_type = %s,
                recurrence = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        recurrence_json = json.dumps(event_data.get('recurrence')) if event_data.get('recurrence') else None
        
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # Пробуем сначала ISO формат (2025-05-20T10:00:00.000Z)
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    return int(dt.timestamp())
                except ValueError:
                    # Если не сработало, пробуем ожидаемый формат (DD.MM.YYYY HH:MM)
                    dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
                    return int(dt.timestamp())
            except ValueError as e:
                logger.error(f"Invalid date format: {date_str}. Expected either 'DD.MM.YYYY HH:MM' or ISO format")
                raise

        start_date_sec = parse_date(event_data.get('start_date'))
        end_date_sec = parse_date(event_data.get('end_date'))
        notify_date_sec = parse_date(event_data.get('notify_date'))

        cursor.execute(sql, (
            event_data.get('title'),
            start_date_sec,  # Передаём секунды, а не миллисекунды
            end_date_sec,
            event_data.get('notify_before'),
            notify_date_sec,
            event_data.get('event_type'),
            recurrence_json,
            event_id
        ))
        conn.commit()
        return True
    except Exception as error:
        logger.error(f"Error updating event {event_id}: {error}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_note(note_id, note_data):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE notes
            SET title = %s,
                content = %s
            WHERE id = %s
        """

        cursor.execute(sql, (
            note_data.get('title'),
            note_data.get('content'),
            note_id
        ))
        conn.commit()
        return True
    except Exception as error:
        logger.error(f"Error updating note {note_id}: {error}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_task(task_id, task_data):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE task
            SET title = %s,
                content = %s,
                status = %s
            WHERE id = %s
        """
        status = 0
        if task_data.get('status'):
            status = task_data.get('status')
        cursor.execute(sql, (
            task_data.get('title'),
            task_data.get('content'),
            status,
            task_id
        ))
        conn.commit()
        return True
    except Exception as error:
        logger.error(f"Error updating task {task_id}: {error}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_user_admin(user):
    conn = None
    cursor = None
    try:
        user_id = user.get("id")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM users 
            WHERE id = %s
        """, (user_id,))
        result = cursor.fetchone()
        if result and result["role"] == 1:
            return True
        return None
    except Exception as e:
        logger.error(f"Error getting role for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_users():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * 
            FROM users
        """)
        result = cursor.fetchall()
        return result if result else None

    except Exception as e:
        logger.error(f"Error getting users : {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_user(user_info, admin):
    if not check_user_admin(admin):
        return False
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_info.get('id'),))
        if not cursor.fetchone():
            return False

        update_fields = []
        update_values = []

        fields_to_update = [
            'userinfo', 'timezone', 'role', 'status', 'tariff',
            'talagramID', 'username', 'first_name', 'last_name', 'state'
        ]
        
        for field in fields_to_update:
            if field in user_info:
                update_fields.append(f"{field} = %s")
                update_values.append(user_info[field])

        if 'date_pay_tariff' in user_info:
            update_fields.append("date_pay_tariff = %s")
            update_values.append(user_info['date_pay_tariff'])

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        if update_fields:
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            update_values.append(user_info['id'])
            cursor.execute(query, update_values)
            conn.commit()
            return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def delete_user_and_data(telegram_id):
    """
    Полностью удаляет пользователя и все связанные с ним данные (события, заметки, задачи, историю)
    из базы данных благодаря каскадному удалению (ON DELETE CASCADE).
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Просто удаляем запись из таблицы users. Остальное удалится автоматически,
        # если внешние ключи были созданы с ON DELETE CASCADE.
        cursor.execute("DELETE FROM users WHERE talagramID = %s", (telegram_id,))
        conn.commit()
        
        # Проверяем, была ли запись удалена
        if cursor.rowcount > 0:
            logger.info(f"Пользователь с talagramID {telegram_id} и все его данные были полностью удалены.")
            return True
        else:
            logger.warning(f"Попытка удаления пользователя с talagramID {telegram_id}, но он не найден в базе.")
            # Возвращаем True даже если не найден, т.к. цель (отсутствие юзера) достигнута
            return True
    except Exception as e:
        logger.error(f"Ошибка при полном удалении пользователя {telegram_id}: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()