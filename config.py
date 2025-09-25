# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения или .env файле")

# ID администраторов (можно несколько через запятую)
admin_ids_raw = os.getenv("ADMIN_IDS", "")
if admin_ids_raw:
    # Удаляем пробелы и разделяем по запятой
    ADMIN_IDS = [id.strip() for id in admin_ids_raw.split(",") if id.strip()]
else:
    ADMIN_IDS = []

print(f"📋 Загружены администраторы: {ADMIN_IDS}")

# ID юриста для уведомлений
LAWYER_CHAT_ID = os.getenv("LAWYER_CHAT_ID", ADMIN_IDS[0] if ADMIN_IDS else None)

# Для DeepSeek/OpenAI
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Дополнительные настройки
MAX_DAILY_AI_REQUESTS = int(os.getenv("MAX_DAILY_AI_REQUESTS", "10"))
CONSULTATION_DURATION_MINUTES = int(os.getenv("CONSULTATION_DURATION_MINUTES", "30"))

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    result = str(user_id) in ADMIN_IDS
    print(f"🔍 Проверка админа: user_id={user_id}, type={type(user_id)}, ADMIN_IDS={ADMIN_IDS}, result={result}")
    return result
