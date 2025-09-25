import datetime
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    """Главная клавиатура бота."""
    keyboard = [
        [KeyboardButton("📋 Консультация"), KeyboardButton("💰 Калькулятор долга")],
        [KeyboardButton("📞 Связаться с юристом"), KeyboardButton("ℹ️ О банкротстве")],
        [KeyboardButton("🤖 Вопрос ИИ-юристу"), KeyboardButton("📅 Запись на консультацию")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_keyboard():
    """Клавиатура админ-панели."""
    keyboard = [
        [KeyboardButton("📋 Просмотреть заявки")],
        [KeyboardButton("📝 Задать расписание")],
        [KeyboardButton("🏠 В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def income_keyboard():
    """Клавиатура для выбора типа дохода."""
    keyboard = [
        [KeyboardButton("Официальный доход")],
        [KeyboardButton("Неофициальный доход")],
        [KeyboardButton("Не работаю")],
        [KeyboardButton("Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def requests_keyboard(requests):
    """Создает inline-клавиатуру со списком заявок."""
    keyboard = []
    
    status_emoji = {
        'new': '🆕',
        'in_progress': '⏳',
        'completed': '✅',
        'rejected': '❌'
    }
    
    for req in requests[:10]:  # Показываем только первые 10 заявок
        request_id = req[0]
        client_name = req[3]
        status = req[9]
        emoji = status_emoji.get(status, '❓')
        
        button_text = f"{emoji} #{request_id}: {client_name[:20]}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_request_{request_id}")])
    
    return InlineKeyboardMarkup(keyboard)

def request_status_keyboard(request_id):
    """Создает inline-клавиатуру для изменения статуса заявки."""
    keyboard = [
        [InlineKeyboardButton("⏳ В работе", callback_data=f"status_in_progress_{request_id}")],
        [InlineKeyboardButton("✅ Завершена", callback_data=f"status_completed_{request_id}")],
        [InlineKeyboardButton("❌ Отклонена", callback_data=f"status_rejected_{request_id}")],
        [InlineKeyboardButton("🔄 Вернуться к списку", callback_data="back_to_requests")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_calendar(year, month):
    """Создает inline-клавиатуру с календарем."""
    keyboard = []
    
    # Заголовок с месяцем и годом
    months = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    header = [InlineKeyboardButton(f"{months[month]} {year}", callback_data="ignore")]
    keyboard.append(header)
    
    # Дни недели
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in weekdays])
    
    # Дни месяца
    import calendar as cal
    month_calendar = cal.monthcalendar(year, month)
    today = datetime.date.today()
    
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                date = datetime.date(year, month, day)
                if date < today:
                    # Прошедшие даты неактивны
                    row.append(InlineKeyboardButton(f"✖️{day}", callback_data="ignore"))
                elif date == today:
                    # Сегодня выделяем
                    row.append(InlineKeyboardButton(f"📍{day}", callback_data=f"calendar_day_{date.isoformat()}"))
                else:
                    # Будущие даты активны
                    row.append(InlineKeyboardButton(str(day), callback_data=f"calendar_day_{date.isoformat()}"))
        keyboard.append(row)
    
    # Навигация по месяцам
    nav_row = []
    if month > 1:
        nav_row.append(InlineKeyboardButton("<<", callback_data=f"calendar_nav_{year}_{month-1}"))
    else:
        nav_row.append(InlineKeyboardButton("<<", callback_data=f"calendar_nav_{year-1}_12"))
    
    if month < 12:
        nav_row.append(InlineKeyboardButton(">>", callback_data=f"calendar_nav_{year}_{month+1}"))
    else:
        nav_row.append(InlineKeyboardButton(">>", callback_data=f"calendar_nav_{year+1}_1"))
    
    keyboard.append(nav_row)
    
    # ДОБАВЛЯЕМ КНОПКУ ОТМЕНЫ
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel_calendar")])
    
    return InlineKeyboardMarkup(keyboard)

def create_time_slots_keyboard(slots):
    """Создает клавиатуру с временными слотами."""
    keyboard = []
    for slot in slots:
        keyboard.append([InlineKeyboardButton(slot, callback_data=f"time_slot_{slot}")])
    
    # Добавляем кнопки навигации
    keyboard.append([InlineKeyboardButton("⬅️ Назад к календарю", callback_data="back_to_calendar")])
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel_calendar")])
    
    return InlineKeyboardMarkup(keyboard)

def create_time_slots_keyboard_with_status(available_slots, booked_times):
    """Создает клавиатуру временных слотов с указанием занятых"""
    keyboard = []
    for slot in available_slots:
        if slot in booked_times:
            # Занятое время - неактивная кнопка
            keyboard.append([InlineKeyboardButton(f"❌ {slot} (занято)", callback_data=f"occupied_{slot}")])
        else:
            # Свободное время
            keyboard.append([InlineKeyboardButton(f"✅ {slot}", callback_data=f"time_slot_{slot}")])
    
    # Добавляем кнопки навигации
    keyboard.append([InlineKeyboardButton("⬅️ Назад к календарю", callback_data="back_to_calendar")])
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel_calendar")])
    
    return InlineKeyboardMarkup(keyboard)
