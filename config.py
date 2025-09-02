import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LAWYER_CHAT_ID = os.getenv("LAWYER_CHAT_ID")

# Для DeepSeek/OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # ключ DeepSeek
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
