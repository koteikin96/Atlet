from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import datetime
from db import (
    get_all_requests, 
    get_request_details, 
    update_request_status, 
    save_lawyer_schedule,
    get_appointments_for_date,
    get_statistics,
    save_document_analysis
)
from states import (
    ADMIN_PANEL, SETTING_SCHEDULE, MAIN_MENU,
    ADMIN_DOCUMENTS, ADMIN_CONTRACT, ADMIN_RESEARCH, 
    ADMIN_RISK_ANALYSIS, ADMIN_FINANCIAL
)
from config import ADMIN_IDS
from ai_client import (
    analyze_document_with_ai,
    generate_contract_with_ai,
    legal_research_with_ai,
    analyze_risks_with_ai,
    analyze_financial_documents
)

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    user_id_str = str(user_id)
    result = user_id_str in ADMIN_IDS
    print(f"🔍 Проверка админа: user_id={user_id}, type={type(user_id)}, ADMIN_IDS={ADMIN_IDS}, result={result}")
    return result

def admin_keyboard():
    """Клавиатура админ-панели с ИИ-функциями."""
    keyboard = [
        ["📋 Заявки", "📅 Записи"],
        ["📊 Статистика", "📝 Расписание"],
        ["📄 Анализ документов", "✍️ Составить договор"],
        ["🔍 Поиск практики", "⚠️ Анализ рисков"],
        ["💼 Финансовый анализ", "🔐 Защита данных"],
        ["🏠 Главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с админ-панелью."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ У вас нет доступа к админ-панели.\n"
            "Ваш ID: " + str(user_id)
        )
        return MAIN_MENU
    
    await update.message.reply_text(
        "🔐 **Панель администратора**\n\n"
        "Доступные функции:\n"
        "• 📋 Управление заявками\n"
        "• 📅 Просмотр записей\n"
        "• 📊 Статистика\n"
        "• 📝 Настройка расписания\n"
        "• 🤖 ИИ-инструменты для работы\n\n"
        "Выберите действие:",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown"
    )
    
    return ADMIN_PANEL

async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик меню админа."""
    text = update.message.text
    
    if text == "📋 Заявки":
        return await handle_admin_requests(update, context)
    elif text == "📅 Записи":
        return await show_appointments(update, context)
    elif text == "📝 Расписание":
        return await start_set_schedule(update, context)
    elif text == "📊 Статистика":
        return await show_statistics(update, context)
    elif text == "📄 Анализ документов":
        return await start_document_analysis(update, context)
    elif text == "✍️ Составить договор":
        return await start_contract_generation(update, context)
    elif text == "🔍 Поиск практики":
        return await start_legal_research(update, context)
    elif text == "⚠️ Анализ рисков":
        return await start_risk_analysis(update, context)
    elif text == "💼 Финансовый анализ":
        return await start_financial_analysis(update, context)
    elif text == "🔐 Защита данных":
        return await data_protection_info(update, context)
    elif text == "🏠 Главное меню":
        from handlers.start import start
        return await start(update, context)
    
    return ADMIN_PANEL

async def handle_admin_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список заявок с возможностью управления."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    requests = get_all_requests()
    
    if not requests:
        await update.message.reply_text(
            "📋 Заявок пока нет.",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL
    
    # Группируем заявки по статусам
    new_requests = [r for r in requests if r[9] == 'new']
    in_progress = [r for r in requests if r[9] == 'in_progress']
    completed = [r for r in requests if r[9] == 'completed']
    
    message = "📋 **УПРАВЛЕНИЕ ЗАЯВКАМИ**\n\n"
    
    if new_requests:
        message += "🆕 **Новые заявки:**\n"
        for req in new_requests[:5]:  # Показываем последние 5
            date = datetime.datetime.fromisoformat(req[8]).strftime("%d.%m %H:%M")
            message += f"• ID{req[0]}: {req[3]} ({date})\n"
    
    if in_progress:
        message += "\n⏳ **В работе:**\n"
        for req in in_progress[:5]:
            date = datetime.datetime.fromisoformat(req[8]).strftime("%d.%m %H:%M")
            message += f"• ID{req[0]}: {req[3]} ({date})\n"
    
    if completed:
        message += "\n✅ **Завершенные:**\n"
        for req in completed[:3]:
            date = datetime.datetime.fromisoformat(req[8]).strftime("%d.%m %H:%M")
            message += f"• ID{req[0]}: {req[3]} ({date})\n"
    
    message += "\n📌 Для просмотра деталей заявки нажмите на кнопку с её ID:"
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )
    
    # Создаем инлайн-кнопки для новых заявок
    if new_requests:
        keyboard = []
        for i in range(0, len(new_requests[:10]), 2):  # Максимум 10 заявок
            row = []
            row.append(InlineKeyboardButton(
                f"📋 ID{new_requests[i][0]}", 
                callback_data=f"view_request_{new_requests[i][0]}"
            ))
            if i + 1 < len(new_requests[:10]):
                row.append(InlineKeyboardButton(
                    f"📋 ID{new_requests[i+1][0]}", 
                    callback_data=f"view_request_{new_requests[i+1][0]}"
                ))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Выберите заявку для просмотра:",
            reply_markup=reply_markup
        )
    
    return ADMIN_PANEL

async def handle_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка изменения статуса заявки и просмотра деталей."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Просмотр деталей заявки
    if data.startswith("view_request_"):
        request_id = int(data.replace("view_request_", ""))
        request = get_request_details(request_id)
        
        if request:
            status_emoji = {
                'new': '🆕',
                'in_progress': '⏳',
                'completed': '✅'
            }
            
            status_text = {
                'new': 'Новая',
                'in_progress': 'В работе',
                'completed': 'Завершена'
            }
            
            created_at = datetime.datetime.fromisoformat(request[8])
            
            message = f"""
📋 **ЗАЯВКА #{request[0]}**

👤 **Клиент:** {request[3]}
📱 **Телефон:** {request[4]}
💬 **Username:** @{request[2] if request[2] else 'не указан'}

💰 **Сумма долга:** {request[5]:,.0f} руб.
💵 **Доход:** {request[6]:,.0f} руб.

📝 **Описание ситуации:**
{request[7]}

🤖 **Анализ ИИ:**
{request[10] if request[10] else 'Не проводился'}

📅 **Дата подачи:** {created_at.strftime('%d.%m.%Y %H:%M')}
{status_emoji.get(request[9], '')} **Статус:** {status_text.get(request[9], request[9])}

Выберите новый статус:
"""
            
            # Кнопки для изменения статуса
            keyboard = [
                [
                    InlineKeyboardButton("🆕 Новая", callback_data=f"status_new_{request_id}"),
                    InlineKeyboardButton("⏳ В работе", callback_data=f"status_in_progress_{request_id}")
                ],
                [
                    InlineKeyboardButton("✅ Завершена", callback_data=f"status_completed_{request_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    
    # Изменение статуса
    elif data.startswith("status_"):
        parts = data.split("_")
        new_status = "_".join(parts[1:-1])  # Извлекаем статус (может быть in_progress)
        request_id = int(parts[-1])
        
        update_request_status(request_id, new_status)
        
        status_text = {
            'new': 'Новая',
            'in_progress': 'В работе',
            'completed': 'Завершена'
        }
        
        await query.edit_message_text(
            f"✅ Статус заявки #{request_id} изменен на: {status_text.get(new_status, new_status)}"
        )
    
    return ADMIN_PANEL

async def show_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает записи на консультации."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    week_ahead = today + datetime.timedelta(days=7)
    
    # Получаем записи
    today_appointments = get_appointments_for_date(today)
    tomorrow_appointments = get_appointments_for_date(tomorrow)
    
    message = "📅 **ЗАПИСИ НА КОНСУЛЬТАЦИИ**\n\n"
    
    # Сегодняшние записи
    if today_appointments:
        message += f"**Сегодня ({today.strftime('%d.%m.%Y')}):**\n"
        for app in today_appointments:
            time = datetime.datetime.fromisoformat(app[5]).strftime("%H:%M")
            status = "✅" if app[7] == 'scheduled' else "❌"
            message += f"{status} {time} - {app[3]} ({app[4]})\n"
        message += "\n"
    else:
        message += f"На сегодня записей нет.\n\n"
    
    # Завтрашние записи
    if tomorrow_appointments:
        message += f"**Завтра ({tomorrow.strftime('%d.%m.%Y')}):**\n"
        for app in tomorrow_appointments:
            time = datetime.datetime.fromisoformat(app[5]).strftime("%H:%M")
            status = "✅" if app[7] == 'scheduled' else "❌"
            message += f"{status} {time} - {app[3]} ({app[4]})\n"
        message += "\n"
    
    # Статистика на неделю
    week_count = 0
    current_date = today
    while current_date <= week_ahead:
        week_count += len(get_appointments_for_date(current_date))
        current_date += datetime.timedelta(days=1)
    
    message += f"📊 **Статистика:**\n"
    message += f"• Всего записей на неделю: {week_count}\n"
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )
    
    return ADMIN_PANEL

async def start_set_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс установки расписания."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    await update.message.reply_text(
        "📝 **НАСТРОЙКА РАСПИСАНИЯ**\n\n"
        "Отправьте расписание в формате:\n"
        "```\n"
        "Пн: 09:00-18:00\n"
        "Вт: 09:00-18:00\n"
        "Ср: 09:00-18:00\n"
        "Чт: 09:00-18:00\n"
        "Пт: 09:00-17:00\n"
        "Сб: выходной\n"
        "Вс: выходной\n"
        "```\n\n"
        "Или отправьте 'стандарт' для установки расписания Пн-Пт 09:00-18:00\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return SETTING_SCHEDULE

async def handle_schedule_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод расписания от администратора."""
    text = update.message.text.strip().lower()
    
    # Стандартное расписание
    if text == "стандарт":
        schedule = [
            ("Понедельник", "09:00", "18:00"),
            ("Вторник", "09:00", "18:00"),
            ("Среда", "09:00", "18:00"),
            ("Четверг", "09:00", "18:00"),
            ("Пятница", "09:00", "18:00"),
            ("Суббота", "выходной", "выходной"),
            ("Воскресенье", "выходной", "выходной")
        ]
        
        # Фильтруем выходные дни
        working_schedule = [(day, start, end) for day, start, end in schedule if start != "выходной"]
        
        save_lawyer_schedule(working_schedule)
        
        await update.message.reply_text(
            "✅ Стандартное расписание установлено:\n"
            "Пн-Пт: 09:00-18:00\n"
            "Сб-Вс: выходной",
            reply_markup=admin_keyboard()
        )
    else:
        # Парсим пользовательское расписание
        lines = text.split('\n')
        schedule = []
        
        days_map = {
            'пн': 'Понедельник', 'понедельник': 'Понедельник',
            'вт': 'Вторник', 'вторник': 'Вторник',
            'ср': 'Среда', 'среда': 'Среда',
            'чт': 'Четверг', 'четверг': 'Четверг',
            'пт': 'Пятница', 'пятница': 'Пятница',
            'сб': 'Суббота', 'суббота': 'Суббота',
            'вс': 'Воскресенье', 'воскресенье': 'Воскресенье'
        }
        
        success = True
        for line in lines:
            line = line.strip().lower()
            if not line:
                continue
                
            # Проверяем на "выходной"
            if "выходной" in line:
                # Пропускаем выходные дни
                continue
            
            # Парсим рабочие дни
            parts = line.replace(':', ' ').replace('-', ' ').replace('—', ' ').split()
            
            day = None
            start_time = None
            end_time = None
            
            # Находим день недели
            for part in parts:
                if part in days_map:
                    day = days_map[part]
                    break
            
            # Находим времена
            times = []
            for i, part in enumerate(parts):
                # Проверяем формат ЧЧ:ММ
                if len(part) == 5 and part[2] == ':':
                    times.append(part)
                # Проверяем формат ЧЧММ
                elif len(part) == 4 and part.isdigit():
                    times.append(f"{part[:2]}:{part[2:]}")
                # Проверяем составной формат (09 00)
                elif i < len(parts) - 1 and part.isdigit() and parts[i+1].isdigit():
                    if len(part) == 2 and len(parts[i+1]) == 2:
                        times.append(f"{part}:{parts[i+1]}")
            
            if day and len(times) >= 2:
                schedule.append((day, times[0], times[1]))
            else:
                success = False
                break
        
        if success and schedule:
            save_lawyer_schedule(schedule)
            
            schedule_text = "\n".join([f"{day}: {start}-{end}" for day, start, end in schedule])
            await update.message.reply_text(
                f"✅ Расписание сохранено:\n\n{schedule_text}",
                reply_markup=admin_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось распознать расписание. Попробуйте еще раз или отправьте 'стандарт'.\n\n"
                "Примеры правильного формата:\n"
                "Пн: 09:00-18:00\n"
                "Вт: 10:00-19:00\n"
                "Сб: выходной",
                reply_markup=admin_keyboard()
            )
            return SETTING_SCHEDULE
    
    return ADMIN_PANEL

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает статистику."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    stats = get_statistics()
    
    message = f"""
📊 **СТАТИСТИКА СИСТЕМЫ**

**📋 Заявки:**
• Всего: {stats['total_requests']}
• Новые: {stats['new_requests']}
• В работе: {stats['in_progress']}
• Завершены: {stats['completed']}

**📅 Консультации:**
• Запланировано: {stats['scheduled']}
• Проведено: {stats['completed_appointments']}

**👥 Клиенты:**
• Всего: {stats['total_clients']}
• Активные (30 дней): {stats['active_clients']}

**💰 Финансы:**
• Общая сумма долгов: {stats['total_debt']:,.0f} руб
• Средний долг: {stats['avg_debt']:,.0f} руб
• Потенциальный доход: {stats['potential_income']:,.0f} руб

_Данные обновлены: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}_
"""
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )
    
    return ADMIN_PANEL

# ===== ИИ-ФУНКЦИИ ДЛЯ АДМИНОВ =====

async def start_document_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает анализ документа."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    await update.message.reply_text(
        "📄 **АНАЛИЗ ДОКУМЕНТОВ С ИИ**\n\n"
        "Отправьте документ (файл или текст) для анализа.\n"
        "ИИ выявит:\n"
        "• Ключевые условия\n"
        "• Потенциальные риски\n"
        "• Спорные моменты\n"
        "• Возможности для оптимизации\n\n"
        "Поддерживаются форматы: TXT, PDF (как текст)\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ADMIN_DOCUMENTS

async def handle_document_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает анализ документа."""
    
    if update.message.text and update.message.text.lower() == '/cancel':
        await update.message.reply_text("Отменено.", reply_markup=admin_keyboard())
        return ADMIN_PANEL
    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("📄 Анализирую документ...")
    
    try:
        document_text = ""
        
        # Если прислан документ
        if update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            try:
                document_text = file_bytes.decode('utf-8')
            except:
                document_text = "Не удалось прочитать файл. Отправьте текст или TXT файл."
        # Если прислан текст
        elif update.message.text:
            document_text = update.message.text
        
        if document_text and document_text != "Не удалось прочитать файл. Отправьте текст или TXT файл.":
            # Получаем анализ от ИИ
            analysis = await analyze_document_with_ai(document_text)
            
            # Сохраняем анализ в БД
            user_id = update.effective_user.id
            save_document_analysis(user_id, "user_document", analysis)
            
            # Безопасное удаление сообщения
            try:
                await processing_msg.delete()
            except Exception:
                pass
            
            # Отправляем результат
            await update.message.reply_text(
                f"📄 Результат анализа:\n\n{analysis}",
                parse_mode="Markdown"
            )
        else:
            # Безопасное удаление сообщения
            try:
                await processing_msg.delete()
            except Exception:
                pass
                
            await update.message.reply_text(
                "❌ Не удалось прочитать документ. Отправьте текст или файл в формате TXT."
            )
        
        await update.message.reply_text(
            "Отправьте новый документ для анализа или нажмите /cancel для возврата.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADMIN_DOCUMENTS
        
    except Exception as e:
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ Ошибка при анализе: {str(e)}",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL

async def start_contract_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает генерацию договора."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    await update.message.reply_text(
        "✍️ **ГЕНЕРАТОР ДОГОВОРОВ**\n\n"
        "Опишите параметры договора:\n"
        "• Тип договора\n"
        "• Стороны\n"
        "• Предмет договора\n"
        "• Основные условия\n\n"
        "Пример:\n"
        "_Договор оказания юридических услуг между ИП Иванов и физлицом Петровым. "
        "Услуги по банкротству. Стоимость 50000 руб, оплата 50% предоплата._\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ADMIN_CONTRACT

async def handle_contract_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает генерацию договора."""
    params = update.message.text
    
    if params.lower() == '/cancel':
        await update.message.reply_text("Отменено.", reply_markup=admin_keyboard())
        return ADMIN_PANEL
    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("✍️ Составляю договор...")
    
    try:
        # Получаем договор от ИИ
        contract = await generate_contract_with_ai(params)
        
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # Отправляем результат
        await update.message.reply_text(
            f"📄 Договор:\n\n{contract}",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "Опишите параметры нового договора или нажмите /cancel для возврата.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADMIN_CONTRACT
        
    except Exception as e:
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ Ошибка при генерации: {str(e)}",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL

async def start_legal_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает поиск судебной практики."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    await update.message.reply_text(
        "🔍 **ПОИСК СУДЕБНОЙ ПРАКТИКИ**\n\n"
        "Введите запрос для поиска:\n"
        "• Тему или правовой вопрос\n"
        "• Статью закона\n"
        "• Тип спора\n\n"
        "Примеры:\n"
        "_- Взыскание неустойки по договору поставки_\n"
        "_- Банкротство физлиц единственное жилье_\n"
        "_- Оспаривание сделок должника_\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ADMIN_RESEARCH

async def handle_legal_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает запрос на поиск судебной практики."""
    query = update.message.text
    
    if query.lower() == '/cancel':
        await update.message.reply_text("Отменено.", reply_markup=admin_keyboard())
        return ADMIN_PANEL
    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("🔍 Ищу судебную практику...")
    
    try:
        # Получаем анализ от ИИ
        result = await legal_research_with_ai(query)
        
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # Отправляем результат
        await update.message.reply_text(
            f"📚 Результаты исследования:\n\n{result}",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "Введите новый запрос или нажмите /cancel для возврата в меню.",
            reply_markup=ReplyKeyboardRemove()
        )  # <-- Эта строка была обрезана у вас
        return ADMIN_RESEARCH
        
    except Exception as e:  # <-- Это должно быть частью основного try блока
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ Ошибка при обработке запроса: {str(e)}",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL

async def start_risk_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает анализ рисков."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    await update.message.reply_text(
        "⚠️ **АНАЛИЗ ПРАВОВЫХ РИСКОВ**\n\n"
        "Опишите ситуацию для анализа:\n"
        "• Планируемую сделку\n"
        "• Спорную ситуацию\n"
        "• Правовую проблему\n\n"
        "ИИ оценит:\n"
        "• Вероятные риски\n"
        "• Возможные последствия\n"
        "• Способы минимизации\n"
        "• Альтернативные решения\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ADMIN_RISK_ANALYSIS


async def handle_risk_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает запрос на анализ рисков."""
    situation = update.message.text
    
    if situation.lower() == '/cancel':
        await update.message.reply_text("Отменено.", reply_markup=admin_keyboard())
        return ADMIN_PANEL
    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("⚠️ Анализирую риски...")
    
    try:
        # Получаем анализ от ИИ
        analysis = await analyze_risks_with_ai(situation)
        
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # Отправляем результат
        await update.message.reply_text(
            f"⚠️ Анализ рисков:\n\n{analysis}",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "Опишите новую ситуацию для анализа или нажмите /cancel для возврата.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADMIN_RISK_ANALYSIS
        
    except Exception as e:
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ Ошибка при анализе: {str(e)}",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL

async def start_financial_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает финансовый анализ."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    await update.message.reply_text(
        "💼 **ФИНАНСОВЫЙ АНАЛИЗ**\n\n"
        "Выберите тип анализа:\n\n"
        "1️⃣ **Анализ базы данных** - анализ финансовых показателей всех клиентов\n"
        "2️⃣ **Анализ пользовательских данных** - введите свои финансовые данные\n\n"
        "Отправьте:\n"
        "• `1` для анализа БД\n"
        "• Или введите финансовые данные в свободной форме:\n\n"
        "_Пример:_\n"
        "```\n"
        "Доход: 50000 руб/мес\n"
        "Долги: 500000 руб\n"
        "Кредиты: 25000 руб/мес\n"
        "Расходы: 45000 руб/мес\n"
        "```\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ADMIN_FINANCIAL

async def handle_financial_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает финансовый анализ."""
    text = update.message.text.strip()
    
    if text.lower() == '/cancel':
        await update.message.reply_text("❌ Анализ отменен.", reply_markup=admin_keyboard())
        return ADMIN_PANEL
    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("💼 Анализирую финансовые данные...")
    
    try:
        financial_data = ""
        
        if text == "1":
            # Анализ данных из БД
            stats = get_statistics()
            
            financial_data = f"""
Анализ базы данных клиентов:

Общая информация:
- Всего клиентов: {stats['total_clients']}
- Активных клиентов (30 дней): {stats['active_clients']}

Заявки:
- Новые заявки: {stats['new_requests']}
- В работе: {stats['in_progress']}
- Завершенные: {stats['completed']}
- Всего заявок: {stats['total_requests']}

Финансовые показатели:
- Общая сумма долгов клиентов: {stats['total_debt']:,.0f} руб
- Средний долг на клиента: {stats['avg_debt']:,.0f} руб
- Потенциальный доход от услуг: {stats['potential_income']:,.0f} руб

Консультации:
- Запланировано: {stats['scheduled']}
- Проведено: {stats['completed_appointments']}

Проанализируй эти данные с точки зрения бизнеса юридических услуг по банкротству.
"""
        else:
            # Используем введенные пользователем данные
            financial_data = f"""
Финансовые данные для анализа:

{text}

Проанализируй эти данные на признаки банкротства физического лица.
Оцени платежеспособность и дай рекомендации.
"""
        
        # Получаем анализ от ИИ
        analysis = await analyze_financial_documents(financial_data)
        
        # Безопасное удаление индикатора загрузки
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # Отправляем результат
        await update.message.reply_text(
            f"💼 **РЕЗУЛЬТАТ ФИНАНСОВОГО АНАЛИЗА**\n\n{analysis}",
            parse_mode="Markdown"
        )
        
        # Предлагаем продолжить или вернуться
        keyboard = [
            ["🔄 Новый анализ", "🏠 Админ-панель"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Что делать дальше?",
            reply_markup=reply_markup
        )
        
        return ADMIN_FINANCIAL
        
    except Exception as e:
        # Безопасное удаление индикатора загрузки
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ **Ошибка при анализе:**\n\n{str(e)}\n\n"
            f"Попробуйте еще раз или обратитесь к разработчику.",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL

async def handle_financial_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает навигацию в режиме финансового анализа."""
    text = update.message.text
    
    if text == "🔄 Новый анализ":
        return await start_financial_analysis(update, context)
    elif text == "🏠 Админ-панель":
        await update.message.reply_text(
            "Возврат в админ-панель.",
            reply_markup=admin_keyboard()
        )
        return ADMIN_PANEL
    else:
        # Если пришел не команда навигации, обрабатываем как данные для анализа
        return await handle_financial_analysis(update, context)


    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("💼 Провожу финансовый анализ...")
    
    try:
        # Собираем финансовые данные из БД
        stats = get_statistics()
        
        financial_data = f"""
        Общая сумма долгов клиентов: {stats['total_debt']:,.0f} руб
        Средний долг: {stats['avg_debt']:,.0f} руб
        Завершенных дел: {stats['completed']}
        В работе: {stats['in_progress']}
        """
        
        # Получаем анализ от ИИ
        analysis = await analyze_financial_documents(financial_data)
        
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # Отправляем результат
        await update.message.reply_text(
            f"💼 Финансовый анализ:\n\n{analysis}",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        
    except Exception as e:
        # Безопасное удаление сообщения
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ Ошибка при анализе: {str(e)}",
            reply_markup=admin_keyboard()
        )
    
    return ADMIN_PANEL

async def data_protection_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает информацию о защите данных."""
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
    
    message = """
🔐 **ЗАЩИТА ДАННЫХ**

**Меры безопасности:**
✅ Все данные хранятся локально в SQLite
✅ Доступ к админ-панели только по ID
✅ API ключи в переменных окружения
✅ Логи не содержат персональных данных

**Рекомендации:**
• Регулярно делайте бэкап БД
• Используйте сложные пароли для сервера
• Ограничьте физический доступ к серверу
• Настройте автоматическое резервное копирование

**Соответствие 152-ФЗ:**
• Получайте согласие на обработку данных
• Храните данные на территории РФ
• Обеспечьте конфиденциальность
• Ведите журнал обращений к данным

**Экспорт данных клиента:**
Используйте функцию export_client_data(user_id) для выгрузки всех данных пользователя.

**Удаление данных:**
При запросе клиента удалите его данные из всех таблиц БД.
"""
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )
    
    return ADMIN_PANEL
