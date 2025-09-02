import os
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI

# ===== Загрузка .env =====
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not DEEPSEEK_API_KEY:
    raise ValueError("Не найден DEEPSEEK_API_KEY в окружении. Проверьте .env")

# ===== Инициализация клиента =====
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# ===== База данных =====
DB_NAME = "bankruptcy_bot.db"

# ===== Кеширование ответов =====
def get_cached_answer(question: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS ai_cache (question TEXT PRIMARY KEY, answer TEXT)")
    cur.execute("SELECT answer FROM ai_cache WHERE question = ?", (question,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def save_cache(question: str, answer: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO ai_cache (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()
    conn.close()

# ===== Функция запроса к DeepSeek =====
async def ask_ai_lawyer(question: str, context: str = "") -> str:
    cached = get_cached_answer(question)
    if cached:
        return cached  # возвращаем только текст

    prompt = f"""
Контекст: {context}

Вопрос клиента: {question}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты - опытный юрист по банкротству."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        answer = response.choices[0].message.content.strip()
        save_cache(question, answer)
        return answer
    except Exception as e:
        return f"Ошибка DeepSeek AI: {e}"

# ===== Сохранение истории чата =====
def save_ai_chat(user_id: int, question: str, answer: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute(
        "INSERT INTO ai_chat_history (user_id, question, answer) VALUES (?, ?, ?)",
        (user_id, question, answer)
    )
    conn.commit()
    conn.close()
