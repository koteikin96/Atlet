from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import main_keyboard
from states import MAIN_MENU

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Привет! Я - бот-юрист по банкротству. Чем могу помочь?", reply_markup=main_keyboard())
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено. Вы вернулись в главное меню.", reply_markup=main_keyboard())
    return MAIN_MENU

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, используйте команду /start для начала работы.", reply_markup=main_keyboard())
    return MAIN_MENU