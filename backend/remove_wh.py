import os
import telebot
from dotenv import load_dotenv

# Загружаем переменные из .env, который должен быть в той же папке backend/
load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("Ошибка: Переменная TOKEN не найдена.")
    print("Пожалуйста, убедитесь, что в файле .env в этой же папке (backend/) есть строка вида: TOKEN=ваш_телеграм_токен")
else:
    print(f"Используется токен, начинающийся на: {TOKEN[:10]}...") # Показываем часть токена для проверки
    bot = telebot.TeleBot(TOKEN)
    try:
        print("Пытаюсь удалить вебхук...")
        result = bot.remove_webhook()
        if result:
            print("Команда remove_webhook выполнена успешно.")
        else:
            print("Команда remove_webhook вернула False (возможно, вебхук уже был снят или не был установлен).")

        # Проверяем информацию о вебхуке после попытки удаления
        webhook_info = bot.get_webhook_info()
        if not webhook_info.url: # Если URL пустой, значит вебхука нет
            print(f"Вебхук успешно удален или не был установлен. Текущая информация: url='{webhook_info.url}', has_custom_certificate={webhook_info.has_custom_certificate}, pending_update_count={webhook_info.pending_update_count}")
        else:
            print(f"ВНИМАНИЕ: Не удалось полностью удалить вебхук, или он был установлен кем-то еще. Текущая информация: url='{webhook_info.url}'")

    except Exception as e:
        print(f"Произошла ошибка при работе с вебхуком: {e}")
        print("Убедитесь, что токен бота правильный и у бота есть доступ к сети.")