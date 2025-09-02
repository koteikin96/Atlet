from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_keyboard
from states import MAIN_MENU, CASE_DESCRIPTION

async def handle_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    context.user_data['user_id'] = update.message.from_user.id
    context.user_data['username'] = update.message.from_user.username or "нет username"
    await update.message.reply_text("Введите ваш номер телефона:", reply_markup=main_keyboard())
    return CASE_DESCRIPTION

async def handle_case_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'phone' not in context.user_data:
        context.user_data['phone'] = update.message.text
        await update.message.reply_text("Опишите вашу ситуацию для AI-анализа:", reply_markup=main_keyboard())
        return CASE_DESCRIPTION
    else:
        context.user_data['case_description'] = update.message.text
        await update.message.reply_text("Спасибо! Ваши данные сохранены.", reply_markup=main_keyboard())
        return MAIN_MENU
