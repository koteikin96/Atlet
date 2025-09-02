from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_keyboard
from ai_client import ask_ai_lawyer, save_ai_chat
from states import MAIN_MENU

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user_id = update.message.from_user.id
    await update.message.reply_chat_action(action='typing')
    answer = await ask_ai_lawyer(question)
    save_ai_chat(user_id, question, answer)
    await update.message.reply_text(f"🤖 Ответ DeepSeek AI:\n\n{answer}", reply_markup=main_keyboard())
    return MAIN_MENU
