import logging
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from handlers.start import start, cancel
from handlers.consultation import handle_main_menu, handle_debt_amount, handle_income
from handlers.contact import handle_contact_info, handle_case_description
from handlers.ai_chat import handle_ai_chat
from db import init_db
from states import MAIN_MENU, CALCULATOR_DEBT, CALCULATOR_INCOME, CONTACT_INFO, CASE_DESCRIPTION, AI_CHAT

# ===== Настройка логирования =====
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== Инициализация базы данных =====
init_db()

# ===== Создание приложения =====
from config import BOT_TOKEN
application = Application.builder().token(BOT_TOKEN).build()

# ===== ConversationHandler для диалогов =====
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
        CALCULATOR_DEBT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_amount)],
        CALCULATOR_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income)],
        CONTACT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_info)],
        CASE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_case_description)],
        AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    name="conversation_handler",
    persistent=False
)

application.add_handler(conv_handler)

# ===== Глобальный обработчик AI-чат для сообщений вне диалога =====
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat))

# ===== Запуск бота =====
print("🤖 AI-бот запущен...")
application.run_polling()
