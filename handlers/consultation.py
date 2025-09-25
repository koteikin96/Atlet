from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import main_keyboard, income_keyboard
from states import MAIN_MENU, CALCULATOR_DEBT, CALCULATOR_INCOME, CONTACT_INFO, CASE_DESCRIPTION, AI_CHAT

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text
    
    if query == '📋 Консультация':
        info_text = (
            "📋 **Консультация по банкротству физических лиц**\n\n"
            "Мы поможем вам:\n"
            "✅ Оценить вашу ситуацию\n"
            "✅ Подготовить документы\n"
            "✅ Пройти процедуру банкротства\n"
            "✅ Списать долги законно\n\n"
            "Используйте кнопки меню для:\n"
            "• 💰 Расчета возможности банкротства\n"
            "• 📞 Связи с юристом\n"
            "• 🤖 Получения быстрых ответов от ИИ"
        )
        await update.message.reply_text(info_text, parse_mode="Markdown")
        return MAIN_MENU
        
    elif query == '💰 Калькулятор долга':
        await update.message.reply_text(
            "💰 **Калькулятор банкротства**\n\n"
            "Давайте оценим вашу ситуацию.\n"
            "Введите общую сумму вашего долга в рублях:\n"
            "(например: 500000)",
            parse_mode="Markdown"
        )
        return CALCULATOR_DEBT
        
    elif query == '📞 Связаться с юристом':
        await update.message.reply_text(
            "📞 **Связь с юристом**\n\n"
            "Для записи на консультацию мне нужны ваши контакты.\n"
            "Введите ваше имя и телефон через запятую:\n\n"
            "Пример: _Иван Иванов, +79991234567_",
            parse_mode="Markdown"
        )
        return CONTACT_INFO
        
    elif query == 'ℹ️ О банкротстве':
        info = (
            "ℹ️ **Банкротство физических лиц**\n\n"
            "**Когда можно объявить себя банкротом:**\n"
            "• Долг от 50 000 руб (через МФЦ)\n"
            "• Долг от 250 000 руб (через суд)\n"
            "• Просрочка платежей более 3 месяцев\n\n"
            "**Что можно списать:**\n"
            "✅ Кредиты и займы\n"
            "✅ Долги по ЖКХ\n"
            "✅ Налоги (кроме текущих)\n"
            "✅ Штрафы и пени\n\n"
            "**Что НЕ спишется:**\n"
            "❌ Алименты\n"
            "❌ Возмещение вреда жизни/здоровью\n"
            "❌ Зарплата работникам\n"
            "❌ Субсидиарная ответственность\n\n"
            "**Последствия:**\n"
            "⚠️ Запрет на кредиты 5 лет\n"
            "⚠️ Запрет управления компаниями 3 года\n"
            "⚠️ Обязанность уведомлять о банкротстве\n\n"
            "Для подробной консультации воспользуйтесь меню."
        )
        await update.message.reply_text(info, parse_mode="Markdown")
        return MAIN_MENU
        
    elif query == '🤖 Вопрос ИИ-юристу':
        await update.message.reply_text(
            "🤖 **ИИ-юрист по банкротству**\n\n"
            "Задайте ваш вопрос, и я постараюсь помочь.\n"
            "У вас есть 10 бесплатных вопросов в день.\n\n"
            "Для выхода используйте /cancel",
            parse_mode="Markdown"
        )
        return AI_CHAT
        
    elif query == '📅 Запись на консультацию':
        # Обработка происходит в calendar.py
        pass
    else:
        await update.message.reply_text(
            "❌ Не понимаю команду. Используйте кнопки меню.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

async def handle_debt_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        debt = int(update.message.text.replace(' ', '').replace(',', ''))
        context.user_data['debt_amount'] = debt
        
        # Даем предварительную оценку
        if debt < 50000:
            assessment = "⚠️ Сумма долга менее 50 000 руб. Банкротство может быть нецелесообразным."
        elif debt < 250000:
            assessment = "✅ Возможно внесудебное банкротство через МФЦ (бесплатно)."
        else:
            assessment = "✅ Рекомендуется судебное банкротство. Процедура займет 6-12 месяцев."
        
        await update.message.reply_text(
            f"💰 Сумма долга: **{debt:,} руб.**\n\n"
            f"{assessment}\n\n"
            f"Теперь укажите ваш среднемесячный доход в рублях:",
            reply_markup=income_keyboard(),
            parse_mode="Markdown"
        )
        return CALCULATOR_INCOME
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректную сумму (только цифры).\n"
            "Пример: 500000"
        )
        return CALCULATOR_DEBT

async def handle_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    income_text = update.message.text
    
    if income_text == '◀️ Назад':
        await update.message.reply_text(
            "Введите сумму вашего долга в рублях:",
            reply_markup=None
        )
        return CALCULATOR_DEBT
    
    # Обработка вариантов ответа
    if income_text in ['Да, могу', 'Нет, не могу']:
        if income_text == 'Да, могу':
            context.user_data['income_amount'] = 'Есть стабильный доход'
            recommendation = (
                "При наличии дохода возможны варианты:\n"
                "• Реструктуризация долгов (рассрочка до 3 лет)\n"
                "• Реализация имущества (если реструктуризация невозможна)"
            )
        else:
            context.user_data['income_amount'] = 'Нет дохода'
            recommendation = (
                "При отсутствии дохода рекомендуется:\n"
                "• Процедура реализации имущества\n"
                "• Полное списание долгов за 4-6 месяцев"
            )
    else:
        try:
            income = int(income_text.replace(' ', '').replace(',', ''))
            context.user_data['income_amount'] = f"{income:,} руб."
            
            debt = context.user_data.get('debt_amount', 0)
            if income > 0 and debt > 0:
                months_to_pay = debt / income
                if months_to_pay > 36:
                    recommendation = "Долг невозможно погасить за 3 года. Рекомендуется банкротство."
                else:
                    recommendation = f"Теоретически долг можно погасить за {int(months_to_pay)} месяцев. Рассмотрите реструктуризацию."
            else:
                recommendation = "Для точной оценки свяжитесь с юристом."
                
        except ValueError:
            context.user_data['income_amount'] = income_text
            recommendation = "Для точной оценки свяжитесь с юристом."
    
    # Итоговый анализ
    debt = context.user_data.get('debt_amount', 0)
    result_text = (
        f"📊 **Результат анализа:**\n\n"
        f"💰 Долг: **{debt:,} руб.**\n"
        f"💵 Доход: **{context.user_data.get('income_amount')}**\n\n"
        f"**Рекомендация:**\n{recommendation}\n\n"
        f"Для получения подробной консультации:\n"
        f"• Нажмите '📞 Связаться с юристом'\n"
        f"• Или '📅 Запись на консультацию'"
    )
    
    await update.message.reply_text(
        result_text,
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )
    return MAIN_MENU
