from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_keyboard
from states import MAIN_MENU

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    welcome_text = f"""
👋 Здравствуйте, {user.first_name}!

Я - ваш цифровой помощник по вопросам банкротства.

🤖 Возможности:
• AI-анализ вашей ситуации
• Мгновенные ответы на вопросы
• Экспертная оценка шансов на банкротство

Выберите нужный вариант:
    """
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог прерван. Если потребуется помощь - нажмите /start", reply_markup=main_keyboard())
    return -1
