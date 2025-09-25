#!/usr/bin/env python3
"""
Скрипт первоначальной настройки бота
"""

import os
import sqlite3
from dotenv import load_dotenv

def setup():
    print("🚀 Настройка бота по банкротству")
    print("-" * 40)
    
    # Проверяем .env файл
    if not os.path.exists('.env'):
        print("⚠️ Файл .env не найден. Создаю...")
        
        bot_token = input("Введите токен бота: ").strip()
        lawyer_id = input("Введите Telegram ID юриста: ").strip()
        deepseek_key = input("Введите API ключ DeepSeek (или Enter для пропуска): ").strip()
        
        with open('.env', 'w') as f:
            f.write(f"BOT_TOKEN={bot_token}\n")
            f.write(f"LAWYER_CHAT_ID={lawyer_id}\n")
            if deepseek_key:
                f.write(f"DEEPSEEK_API_KEY={deepseek_key}\n")
            f.write("DEEPSEEK_BASE_URL=https://api.deepseek.com\n")
            f.write("MAX_DAILY_AI_REQUESTS=10\n")
            f.write("CONSULTATION_DURATION_MINUTES=30\n")
        
        print("✅ Файл .env создан")
    else:
        print("✅ Файл .env найден")
    
    # Инициализируем БД
    from db import init_db
    init_db()
    print("✅ База данных инициализирована")
    
    # Проверяем зависимости
    try:
        import telegram
        import openai
        import pytz
        import dotenv
        print("✅ Все зависимости установлены")
    except ImportError as e:
        print(f"❌ Не хватает зависимостей: {e}")
        print("Выполните: pip install -r requirements.txt")
        return False
    
    print("-" * 40)
    print("✅ Настройка завершена!")
    print("Запустите бота командой: python main.py")
    return True

if __name__ == "__main__":
    setup()