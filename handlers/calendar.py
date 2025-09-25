import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import create_calendar, main_keyboard, create_time_slots_keyboard_with_status
from db import get_lawyer_schedule, get_appointments_for_date, save_appointment, get_client_data, save_client_data, get_booked_times_for_date, check_appointment_time_available
from states import CALENDAR_MAIN, CALENDAR_SELECT_TIME, MAIN_MENU, CONTACT_INFO
from config import LAWYER_CHAT_ID, ADMIN_IDS

async def cancel_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет процесс записи и возвращает в главное меню."""
    query = update.callback_query
    await query.answer("Запись отменена")
    
    await query.edit_message_text(
        "❌ Запись на консультацию отменена.\n\n"
        "Выберите действие из меню ниже:",
    )
    
    await query.message.reply_text(
        "Главное меню:",
        reply_markup=main_keyboard()
    )
    
    context.user_data.clear()
    return MAIN_MENU

async def back_to_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возвращает к выбору даты."""
    query = update.callback_query
    await query.answer()
    
    current_date = datetime.date.today()
    await query.edit_message_text(
        "📅 Выберите дату для консультации:",
        reply_markup=create_calendar(current_date.year, current_date.month)
    )
    
    return CALENDAR_MAIN

async def start_booking_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запускает процесс бронирования консультации с проверкой данных клиента."""
    user_id = update.effective_user.id
    
    # Проверяем, есть ли расписание юриста
    schedule = get_lawyer_schedule()
    if not schedule:
        await update.message.reply_text(
            "⚠️ К сожалению, расписание юриста еще не настроено. "
            "Пожалуйста, попробуйте позже или свяжитесь с нами напрямую.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    
    # Проверяем, есть ли данные клиента
    client_data = get_client_data(user_id)
    
    if not client_data or not client_data.get('full_name') or not client_data.get('phone'):
        # Если данных нет, запрашиваем их
        await update.message.reply_text(
            "📝 **Для записи на консультацию нужны ваши данные**\n\n"
            "Пожалуйста, введите ваше ФИО и телефон через запятую:\n"
            "Пример: _Иванов Иван Иванович, +79991234567_\n\n"
            "Для отмены введите /cancel",
            parse_mode="Markdown"
        )
        context.user_data['booking_in_progress'] = True
        return CONTACT_INFO
    else:
        # Если данные есть, показываем их и предлагаем календарь
        await update.message.reply_text(
            f"✅ **Ваши данные:**\n"
            f"👤 {client_data['full_name']}\n"
            f"📱 {client_data['phone']}\n\n"
            f"Если данные неверны, сначала обновите их через '📞 Связаться с юристом'\n\n"
            f"📅 Выберите дату для консультации:",
            reply_markup=create_calendar(datetime.date.today().year, datetime.date.today().month),
            parse_mode="Markdown"
        )
        context.user_data['client_data'] = client_data
        return CALENDAR_MAIN

async def handle_calendar_nav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает навигацию по календарю (кнопки << и >>)."""
    query = update.callback_query
    await query.answer()
    
    try:
        _, year, month = query.data.split('_')
        year = int(year)
        month = int(month)
        
        # Ограничиваем выбор датами не более чем на 3 месяца вперед
        max_date = datetime.date.today() + datetime.timedelta(days=90)
        selected_date = datetime.date(year, month, 1)
        
        if selected_date > max_date:
            await query.answer("Запись возможна не более чем на 3 месяца вперед", show_alert=True)
            return CALENDAR_MAIN
        
        await query.edit_message_text(
            f"📅 Выберите дату для консультации:",
            reply_markup=create_calendar(year, month)
        )
    except Exception as e:
        print(f"Ошибка в handle_calendar_nav: {e}")
        await query.answer("Произошла ошибка. Попробуйте еще раз.")
    
    return CALENDAR_MAIN

async def handle_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор дня в календаре и показывает доступное время."""
    query = update.callback_query
    await query.answer()
    
    try:
        date_str = query.data.replace('calendar_day_', '')
        selected_date = datetime.date.fromisoformat(date_str)
        
        # Проверяем, что дата не в прошлом
        if selected_date < datetime.date.today():
            await query.answer("Нельзя выбрать прошедшую дату", show_alert=True)
            return CALENDAR_MAIN
        
        context.user_data['selected_date'] = date_str
        
        weekday_map = {
            0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 
            3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
        }
        
        selected_weekday = weekday_map.get(selected_date.weekday())
        
        # Получаем расписание юриста
        schedule = get_lawyer_schedule()
        
        working_hours = None
        for entry in schedule:
            if entry[0] == selected_weekday:
                working_hours = (entry[1], entry[2])
                break
        
        if not working_hours:
            await query.answer(
                f"В {selected_weekday.lower()} юрист не работает. Выберите другой день.",
                show_alert=True
            )
            return CALENDAR_MAIN
        
        # Генерация всех слотов времени
        start_hour, start_minute = map(int, working_hours[0].split(':'))
        end_hour, end_minute = map(int, working_hours[1].split(':'))
        
        start = datetime.datetime.combine(selected_date, datetime.time(start_hour, start_minute))
        end = datetime.datetime.combine(selected_date, datetime.time(end_hour, end_minute))
        
        # Если выбран сегодняшний день, начинаем с текущего времени + 1 час
        if selected_date == datetime.date.today():
            min_start = datetime.datetime.now() + datetime.timedelta(hours=1)
            if min_start > start:
                minutes = min_start.minute
                if minutes < 30:
                    min_start = min_start.replace(minute=30, second=0, microsecond=0)
                else:
                    min_start = (min_start + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                start = max(start, min_start)
        
        # Получаем список занятых времен
        booked_times = get_booked_times_for_date(selected_date)
        
        # Генерируем все слоты (и свободные, и занятые)
        all_slots = []
        current = start
        while current < end:
            all_slots.append(current.strftime('%H:%M'))
            current += datetime.timedelta(minutes=30)
        
        if not all_slots:
            await query.edit_message_text(
                f"❌ На {selected_date.strftime('%d.%m.%Y')} нет доступного времени.\n"
                f"Пожалуйста, выберите другую дату.",
                reply_markup=create_calendar(selected_date.year, selected_date.month)
            )
            return CALENDAR_MAIN
        
        # Подсчитываем свободные слоты
        free_slots_count = len([s for s in all_slots if s not in booked_times])
        
        status_text = (
            f"🕐 **Выберите время на {selected_date.strftime('%d.%m.%Y')}**\n"
            f"📊 Свободно: {free_slots_count} из {len(all_slots)} слотов\n\n"
            f"✅ - свободное время\n"
            f"❌ - занятое время"
        )
        
        # Показываем первые 12 слотов для удобства
        displayed_slots = all_slots[:12] if len(all_slots) > 12 else all_slots
        
        await query.edit_message_text(
            status_text,
            reply_markup=create_time_slots_keyboard_with_status(displayed_slots, booked_times),
            parse_mode="Markdown"
        )
        
        return CALENDAR_SELECT_TIME
        
    except Exception as e:
        print(f"Ошибка в handle_day_selection: {e}")
        await query.answer("Произошла ошибка при выборе даты. Попробуйте еще раз.")
        return CALENDAR_MAIN

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор времени и сохраняет запись."""
    query = update.callback_query
    
    # Проверяем, не нажали ли на занятое время
    if query.data.startswith('occupied_'):
        await query.answer("Это время уже занято. Выберите другое.", show_alert=True)
        return CALENDAR_SELECT_TIME
    
    await query.answer()
    
    try:
        time_str = query.data.replace('time_slot_', '')
        date_str = context.user_data.get('selected_date')
        
        if not date_str:
            await query.answer("Ошибка: дата не выбрана. Начните заново.", show_alert=True)
            await query.message.reply_text(
                "Произошла ошибка. Вы вернулись в главное меню.",
                reply_markup=main_keyboard()
            )
            return MAIN_MENU
        
        # Двойная проверка доступности времени
        selected_date = datetime.date.fromisoformat(date_str)
        if not check_appointment_time_available(selected_date, time_str):
            await query.answer("Это время уже занято. Выберите другое.", show_alert=True)
            return CALENDAR_SELECT_TIME
        
        appointment_datetime_str = f"{date_str}T{time_str}:00"
        appointment_datetime = datetime.datetime.fromisoformat(appointment_datetime_str)
        
        user = update.effective_user
        user_id = user.id
        username = user.username or "no_username"
        
        # Получаем данные клиента
        client_data = context.user_data.get('client_data') or get_client_data(user_id)
        
        if not client_data:
            await query.answer("Ошибка: данные клиента не найдены", show_alert=True)
            return MAIN_MENU
        
        full_name = client_data.get('full_name', user.full_name)
        phone = client_data.get('phone', 'Не указан')
        
        # Сохраняем запись в базу данных
        save_appointment(user_id, username, full_name, phone, appointment_datetime_str)
        
        # Форматируем красивое сообщение для пользователя
        formatted_date = appointment_datetime.strftime('%d.%m.%Y')
        formatted_time = appointment_datetime.strftime('%H:%M')
        weekday_ru = {
            0: 'понедельник', 1: 'вторник', 2: 'среда', 
            3: 'четверг', 4: 'пятница', 5: 'суббота', 6: 'воскресенье'
        }
        weekday = weekday_ru[appointment_datetime.weekday()]
        
        # Добавляем информацию о клиенте в подтверждение
        success_message = (
            f"✅ **Вы успешно записались на консультацию!**\n\n"
            f"👤 **Ваши данные:**\n"
            f"• ФИО: {full_name}\n"
            f"• Телефон: {phone}\n\n"
            f"📅 **Дата:** {formatted_date} ({weekday})\n"
            f"🕐 **Время:** {formatted_time}\n"
            f"⏱ **Длительность:** 30 минут\n\n"
        )
        
        # Если есть информация о долге, добавляем её
        if client_data.get('debt_amount'):
            success_message += f"💰 **Сумма долга:** {client_data['debt_amount']:,} руб.\n"
        if client_data.get('case_description'):
            success_message += f"📝 **Ситуация:** {client_data['case_description'][:100]}...\n"
        
        success_message += (
            "\n💡 За день до консультации вы получите напоминание.\n"
            "Если вам нужно отменить или перенести запись, свяжитесь с нами.\n\n"
            "Вы можете продолжить работу с ботом, используя меню ниже."
        )
        
        await query.edit_message_text(success_message, parse_mode="Markdown")
        
        # Отправляем клавиатуру для продолжения работы
        await query.message.reply_text(
            "Чем еще я могу вам помочь?",
            reply_markup=main_keyboard()
        )
        
        # Уведомляем всех админов
        lawyer_message = (
            f"📢 **Новая запись на консультацию!**\n\n"
            f"👤 **Клиент:** {full_name}\n"
            f"📱 **Username:** @{username}\n"
            f"📱 **Телефон:** {phone}\n"
            f"📅 **Дата и время:** {formatted_date} в {formatted_time}\n"
        )
        
        if client_data.get('debt_amount'):
            lawyer_message += f"💰 **Долг:** {client_data['debt_amount']:,} руб.\n"
        if client_data.get('case_description'):
            lawyer_message += f"📝 **Ситуация:** {client_data['case_description'][:200]}...\n"
        
        lawyer_message += f"\n🔗 **Ссылка на профиль:** [Открыть](tg://user?id={user_id})"
        
        # Отправляем всем админам
        if hasattr(ADMIN_IDS, '__iter__'):
            for admin_id in ADMIN_IDS:
                if admin_id:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=lawyer_message,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        
        # Очищаем временные данные
        context.user_data.pop('selected_date', None)
        context.user_data.pop('client_data', None)
        
        return MAIN_MENU
        
    except Exception as e:
        print(f"Ошибка в handle_time_selection: {e}")
        await query.answer("Произошла ошибка при сохранении записи. Попробуйте еще раз.")
        await query.message.reply_text(
            "Произошла ошибка. Попробуйте еще раз.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
