from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from keyboards import main_keyboard
from states import MAIN_MENU, CALCULATOR_DEBT, CALCULATOR_INCOME, CONTACT_INFO, AI_CHAT

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ["📋 Консультация", "💰 Калькулятор долга"]:
        await update.message.reply_text("Введите общую сумму ваших долгов (в рублях):", reply_markup=ReplyKeyboardRemove())
        return CALCULATOR_DEBT
    elif text == "📞 Связаться с юристом":
        await update.message.reply_text("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
        return CONTACT_INFO
    elif text == "🤖 Вопрос ИИ-юристу":
        await update.message.reply_text("Задайте ваш вопрос ИИ-юристу:\nПримеры:\n• Какие документы нужны для банкротства?\n• Сколько стоит процедура?\n• Что будет с моей квартирой?", reply_markup=ReplyKeyboardRemove())
        return AI_CHAT
    elif text == "ℹ️ О банкротстве":
        await update.message.reply_text("📋 Информация о банкротстве\n🤖 Возможности AI: мгновенный анализ, ответы на вопросы, оценка шансов", reply_markup=main_keyboard())
        return MAIN_MENU

async def handle_debt_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        debt_amount = float(update.message.text.replace(' ', '').replace(',', '.'))
        context.user_data['debt_amount'] = debt_amount
        await update.message.reply_text("Теперь введите ваш среднемесячный доход (в рублях):")
        return CALCULATOR_INCOME
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную сумму цифрами.")
        return CALCULATOR_DEBT

async def handle_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        income = float(update.message.text.replace(' ', '').replace(',', '.'))
        context.user_data['income_amount'] = income
        debt = context.user_data.get('debt_amount', 0)
        ratio = debt / (income * 12) if income > 0 else float('inf')
        if ratio > 5:
            situation = "критическая"
            recommendation = "Немедленное банкротство необходимо"
        elif 3 <= ratio <= 5:
            situation = "тяжелая"
            recommendation = "Банкротство рекомендуется"
        else:
            situation = "управляемая"
            recommendation = "Рассмотреть реструктуризацию долгов"
        analysis = f"📈 Предварительный анализ:\nДолг: {debt:.0f} руб.\nДоход: {income:.0f} руб.\nСитуация: {situation}\nРекомендация: {recommendation}"
        await update.message.reply_text(analysis, reply_markup=main_keyboard())
        return MAIN_MENU
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную сумму цифрами.")
        return CALCULATOR_INCOME
