import logging
import os
import datetime
import signal
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from telegram.request import HTTPXRequest
from handlers.start import start, cancel, handle_any_message
from handlers.consultation import handle_main_menu, handle_debt_amount, handle_income
from handlers.contact import handle_contact_info, handle_case_description
from handlers.ai_chat import handle_ai_chat_enter, handle_ai_chat_text
from handlers.admin import (
    admin_start, 
    handle_admin_menu,
    handle_admin_requests, 
    handle_status_change, 
    show_appointments, 
    start_set_schedule, 
    handle_schedule_input,
    start_document_analysis,
    handle_document_analysis,
    start_contract_generation,
    handle_contract_generation,
    start_legal_research,
    handle_legal_research,
    start_risk_analysis,
    handle_risk_analysis,
    start_financial_analysis,
    show_statistics,
    data_protection_info
)
from handlers.calendar import (
    start_booking_process, 
    handle_calendar_nav, 
    handle_day_selection, 
    handle_time_selection,
    cancel_calendar,
    back_to_calendar
)
from db import init_db, get_todays_appointments, get_new_requests_for_day
from states import (
    MAIN_MENU, CALCULATOR_DEBT, CALCULATOR_INCOME, CONTACT_INFO, 
    CASE_DESCRIPTION, AI_CHAT, ADMIN_PANEL, CALENDAR_MAIN, 
    CALENDAR_SELECT_TIME, CALENDAR_SELECT_DAY, SETTING_SCHEDULE,
    ADMIN_DOCUMENTS, ADMIN_CONTRACT, ADMIN_RESEARCH, ADMIN_RISK_ANALYSIS, ADMIN_FINANCIAL
)
from config import BOT_TOKEN, LAWYER_CHAT_ID, ADMIN_IDS
from pytz import timezone

# ===== Настройка логирования =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ===== Инициализация базы данных =====
init_db()

# ===== Создание приложения с увеличенными таймаутами =====
request = HTTPXRequest(
    connection_pool_size=8,
    connect_timeout=30.0,
    read_timeout=30.0,
)

application = Application.builder().token(BOT_TOKEN).request(request).build()

# ===== ЕЖЕДНЕВНОЕ УВЕДОМЛЕНИЕ ЮРИСТУ =====
async def daily_summary_job(context):
    """Отправляет юристу ежедневную сводку по заявкам и записям."""
    today = datetime.date.today()
    appointments = get_todays_appointments()
    new_requests = get_new_requests_for_day()

    message = f"✅ **Сводка на {today.strftime('%d.%m.%Y')}**\n\n"
    
    if appointments:
        message += "🗓️ **Записи на сегодня:**\n"
        for app in appointments:
            message += f"• @{app[0]}, {app[2]} - **{datetime.datetime.fromisoformat(app[3]).strftime('%H:%M')}**\n"
    else:
        message += "🗓️ Сегодня нет запланированных консультаций.\n"
    
    message += "\n"
    
    if new_requests:
        message += "📋 **Новые заявки:**\n"
        for req in new_requests:
            desc = req[3][:50] + "..." if len(req[3]) > 50 else req[3]
            message += f"• @{req[0]}, {req[1]} - {desc}\n"
    else:
        message += "📋 Новых заявок сегодня не поступало.\n"

    try:
        await context.bot.send_message(
            chat_id=LAWYER_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить ежедневную сводку: {e}")

# ===== НАСТРОЙКА JOB QUEUE =====
job_queue = application.job_queue
moscow_tz = timezone('Europe/Moscow')
job_queue.run_daily(
    daily_summary_job, 
    time=datetime.time(hour=9, minute=0, tzinfo=moscow_tz)
)

# ===== ConversationHandler для диалогов =====
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start),
        CommandHandler('admin', admin_start)
    ],
    states={
        MAIN_MENU: [
            MessageHandler(filters.Regex('^📋 Консультация$'), handle_main_menu),
            MessageHandler(filters.Regex('^💰 Калькулятор долга$'), handle_main_menu),
            MessageHandler(filters.Regex('^📞 Связаться с юристом$'), handle_main_menu),
            MessageHandler(filters.Regex('^ℹ️ О банкротстве$'), handle_main_menu),
            MessageHandler(filters.Regex('^🤖 Вопрос ИИ-юристу$'), handle_ai_chat_enter),
            MessageHandler(filters.Regex('^📅 Запись на консультацию$'), start_booking_process),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
        ],
        CALCULATOR_DEBT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_amount),
            CommandHandler('cancel', cancel)
        ],
        CALCULATOR_INCOME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income),
            CommandHandler('cancel', cancel)
        ],
        CONTACT_INFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_info),
            CommandHandler('cancel', cancel)
        ],
        CASE_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_case_description),
            CommandHandler('cancel', cancel)
        ],
        AI_CHAT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat_text),
            CommandHandler('cancel', cancel)
        ],
        ADMIN_PANEL: [
            MessageHandler(filters.Regex('^📋 Заявки$'), handle_admin_requests),
            MessageHandler(filters.Regex('^📅 Записи$'), show_appointments),
            MessageHandler(filters.Regex('^📝 Расписание$'), start_set_schedule),
            MessageHandler(filters.Regex('^📊 Статистика$'), show_statistics),
            MessageHandler(filters.Regex('^📄 Анализ документов$'), start_document_analysis),
            MessageHandler(filters.Regex('^✍️ Составить договор$'), start_contract_generation),
            MessageHandler(filters.Regex('^🔍 Поиск практики$'), start_legal_research),
            MessageHandler(filters.Regex('^⚠️ Анализ рисков$'), start_risk_analysis),
            MessageHandler(filters.Regex('^💼 Финансовый анализ$'), start_financial_analysis),
            MessageHandler(filters.Regex('^🔐 Защита данных$'), data_protection_info),
            MessageHandler(filters.Regex('^🏠 Главное меню$'), lambda u, c: start(u, c)),
            CallbackQueryHandler(handle_status_change, pattern=r'^(view_request_|status_).*'),
            CommandHandler('cancel', cancel)
        ],
        ADMIN_DOCUMENTS: [
            MessageHandler(filters.Document.ALL | filters.TEXT & ~filters.COMMAND, handle_document_analysis),
            CommandHandler('cancel', lambda u, c: ADMIN_PANEL)
        ],
        ADMIN_CONTRACT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contract_generation),
            CommandHandler('cancel', lambda u, c: ADMIN_PANEL)
        ],
        ADMIN_RESEARCH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_legal_research),
            CommandHandler('cancel', lambda u, c: ADMIN_PANEL)
        ],
        ADMIN_RISK_ANALYSIS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_risk_analysis),
            CommandHandler('cancel', lambda u, c: ADMIN_PANEL)
        ],

        ADMIN_FINANCIAL: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, start_financial_analysis),  # временно используем start_
        CommandHandler('cancel', cancel)
        ],

        CALENDAR_MAIN: [
            CallbackQueryHandler(handle_calendar_nav, pattern=r'^calendar_nav_.*'),
            CallbackQueryHandler(handle_day_selection, pattern=r'^calendar_day_.*'),
            CallbackQueryHandler(cancel_calendar, pattern=r'^cancel_calendar$'),
            CallbackQueryHandler(lambda u, c: None, pattern=r'^ignore$'),
            CommandHandler('cancel', cancel)
        ],
        CALENDAR_SELECT_TIME: [
            CallbackQueryHandler(handle_time_selection, pattern=r'^time_slot_.*'),
            CallbackQueryHandler(lambda u, c: CALENDAR_SELECT_TIME, pattern=r'^occupied_.*'),
            CallbackQueryHandler(back_to_calendar, pattern=r'^back_to_calendar$'),
            CallbackQueryHandler(cancel_calendar, pattern=r'^cancel_calendar$'),
            CommandHandler('cancel', cancel)
        ],
        SETTING_SCHEDULE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_schedule_input),
            CommandHandler('cancel', cancel)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        CommandHandler('start', start)
    ],
    name="main_conversation",
    per_message=False,
    allow_reentry=True
)

# ===== Добавляем обработчики =====
application.add_handler(conv_handler)

# Глобальные команды вне ConversationHandler
application.add_handler(CommandHandler('appointments', show_appointments))

# ===== Обработка ошибок =====
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Произошла ошибка: {context.error}")
    
    if update and hasattr(update, 'effective_message'):
        try:
            await update.effective_message.reply_text(
                "😔 Произошла ошибка при обработке вашего запроса.\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
        except Exception:
            pass

# Добавляем обработчик ошибок
application.add_error_handler(error_handler)

# ===== Graceful shutdown =====
def signal_handler(signum, frame):
    """Обработка сигналов остановки."""
    print("\n⛔ Получен сигнал остановки...")
    print("⏳ Сохранение данных...")
    # Здесь можно добавить сохранение состояния
    print("👋 Бот остановлен")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ===== Запуск бота =====
if __name__ == '__main__':
    print("🤖 AI-бот для юристов запущен...")
    print(f"📊 База данных: {os.path.abspath('bankruptcy_bot.db')}")
    print(f"👨‍⚖️ ID юриста: {LAWYER_CHAT_ID}")
    print(f"👥 Администраторы: {', '.join(ADMIN_IDS) if ADMIN_IDS else 'не настроены'}")
    print("\n💡 Доступные команды:")
    print("  /start - Главное меню")
    print("  /admin - Панель администратора (с ИИ-инструментами)")
    print("  /appointments - Просмотр записей")
    print("\n⛔ Для остановки нажмите Ctrl+C")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
    except KeyboardInterrupt:
        print("\n⛔ Получен сигнал остановки...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n💡 Возможные решения:")
        print("1. Включите VPN (для доступа к Telegram API)")
        print("2. Проверьте интернет-соединение")
        print("3. Убедитесь, что токен бота правильный")
        print("4. Проверьте, что все зависимости установлены:")
        print("   pip install -r requirements.txt")
    finally:
        print("👋 Бот остановлен")
