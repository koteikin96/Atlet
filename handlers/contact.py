# handlers/contact.py
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_keyboard
from db import save_request, save_client_data, get_client_data
from ai_client import analyze_bankruptcy_case  # Исправленный импорт
from states import CASE_DESCRIPTION, MAIN_MENU, CALENDAR_MAIN
from config import LAWYER_CHAT_ID, ADMIN_IDS
import datetime

async def handle_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод контактной информации."""
    text = update.message.text.strip()
    
    # Проверяем, идет ли процесс записи на консультацию
    is_booking = context.user_data.get('booking_in_progress', False)
    
    # Парсим ФИО и телефон
    parts = text.split(',')
    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Неверный формат. Пожалуйста, введите данные через запятую.\n"
            "Пример: Иванов Иван Иванович, +79991234567"
        )
        return CONTACT_INFO
    
    full_name = parts[0].strip()
    phone = parts[1].strip()
    
    # Валидация телефона (простая проверка)
    phone_digits = ''.join(filter(str.isdigit, phone))
    if len(phone_digits) < 10:
        await update.message.reply_text(
            "❌ Неверный формат телефона. Укажите номер с кодом.\n"
            "Пример: +79991234567"
        )
        return CONTACT_INFO
    
    # Сохраняем данные
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    
    context.user_data['full_name'] = full_name
    context.user_data['phone'] = phone
    
    # Сохраняем в базу данных
    save_client_data(user_id, {
        'username': username,
        'full_name': full_name,
        'phone': phone
    })
    
    if is_booking:
        # Если это процесс записи, переходим к выбору даты
        context.user_data['client_data'] = {
            'full_name': full_name,
            'phone': phone
        }
        context.user_data['booking_in_progress'] = False
        
        from keyboards import create_calendar
        current_date = datetime.date.today()
        
        await update.message.reply_text(
            f"✅ Данные сохранены!\n\n"
            f"👤 {full_name}\n"
            f"📱 {phone}\n\n"
            f"📅 Теперь выберите дату для консультации:",
            reply_markup=create_calendar(current_date.year, current_date.month)
        )
        return CALENDAR_MAIN
    else:
        # Обычная заявка на консультацию
        await update.message.reply_text(
            "✅ Контактные данные сохранены.\n\n"
            "Теперь опишите вашу ситуацию:\n"
            "• Какие долги у вас есть? (банки, МФО, ЖКХ и т.д.)\n"
            "• Есть ли имущество?\n"
            "• Есть ли судебные приставы?\n"
            "• Что вас больше всего беспокоит?\n\n"
            "Чем подробнее опишете, тем точнее будет консультация."
        )
        return CASE_DESCRIPTION

async def handle_case_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает описание ситуации клиента."""
    description = update.message.text
    
    # Получаем сохраненные данные
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    full_name = context.user_data.get('full_name', 'Не указано')
    phone = context.user_data.get('phone', 'Не указан')
    debt_amount = context.user_data.get('debt_amount', 0)
    income = context.user_data.get('income', 0)
    
    # Сохраняем описание
    context.user_data['case_description'] = description
    
    # Обновляем данные клиента
    save_client_data(user_id, {
        'case_description': description,
        'debt_amount': debt_amount,
        'income': income
    })
    
    # Анализируем кейс с помощью ИИ
    processing_msg = await update.message.reply_text("🤖 Анализирую вашу ситуацию...")
    
    try:
        ai_analysis = await analyze_bankruptcy_case(debt_amount, income, description)
    except Exception as e:
        ai_analysis = f"Анализ временно недоступен: {str(e)}"
    
    await processing_msg.delete()
    
    # Сохраняем заявку в базу данных
    from db import save_request
    request_id = save_request(
        user_id=user_id,
        username=username,
        full_name=full_name,
        phone=phone,
        debt_amount=debt_amount,
        income=income,
        case_description=description,
        ai_analysis=ai_analysis
    )
    
    # Отправляем клиенту результат
    await update.message.reply_text(
        f"✅ **Ваша заявка #{request_id} принята!**\n\n"
        f"📊 **Предварительный анализ:**\n{ai_analysis[:1000]}...\n\n"
        f"📞 Наш юрист свяжется с вами в ближайшее время по телефону {phone}\n\n"
        f"Вы также можете записаться на консультацию через меню '📅 Запись на консультацию'",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )
    
    # Отправляем уведомление юристу
    lawyer_message = (
        f"🆕 **Новая заявка #{request_id}**\n\n"
        f"👤 **Клиент:** {full_name}\n"
        f"📱 **Телефон:** `{phone}`\n"
        f"💬 **Username:** @{username}\n"
        f"💰 **Сумма долга:** {debt_amount:,} руб\n"
        f"💵 **Доход:** {income:,} руб\n\n"
        f"📝 **Ситуация:**\n{description[:500]}...\n\n"
        f"🤖 **ИИ-анализ:**\n{ai_analysis[:500]}...\n\n"
        f"🔗 [Открыть профиль](tg://user?id={user_id})"
    )
    
    # Отправляем всем администраторам
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=lawyer_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    # Очищаем временные данные
    context.user_data.clear()
    
    return MAIN_MENU
