from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from states import AI_CHAT, MAIN_MENU
from keyboards import main_keyboard
from ai_client import chat_with_ai
from db import update_ai_request_count, get_ai_request_count

# Максимальное количество запросов к ИИ в день для пользователя
MAX_DAILY_AI_REQUESTS = 5

async def handle_ai_chat_enter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вход в режим чата с ИИ-юристом."""
    user_id = update.effective_user.id
    
    # Проверяем лимит запросов
    request_count = get_ai_request_count(user_id)
    
    if request_count >= MAX_DAILY_AI_REQUESTS:
        await update.message.reply_text(
            "⚠️ **Лимит запросов исчерпан**\n\n"
            "Вы уже использовали все бесплатные запросы к ИИ-юристу на сегодня.\n"
            "Попробуйте завтра или запишитесь на консультацию к реальному юристу.\n\n"
            "Для профессиональной консультации выберите '📞 Связаться с юристом'",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    
    await update.message.reply_text(
        f"🤖 **ИИ-ЮРИСТ**\n\n"
        f"Задайте ваш вопрос по теме банкротства физических лиц.\n\n"
        f"Я могу помочь с:\n"
        f"• Оценкой вашей ситуации\n"
        f"• Разъяснением процедуры банкротства\n"
        f"• Информацией о последствиях\n"
        f"• Анализом документов\n"
        f"• Расчетом сроков и стоимости\n\n"
        f"📊 У вас осталось запросов: {MAX_DAILY_AI_REQUESTS - request_count}/{MAX_DAILY_AI_REQUESTS}\n\n"
        f"⚠️ _Это автоматические ответы ИИ. Для точной консультации обратитесь к юристу._\n\n"
        f"Введите ваш вопрос или /cancel для выхода:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return AI_CHAT

async def handle_ai_chat_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает сообщения в режиме чата с ИИ."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Проверяем команду отмены
    if user_message.lower() == '/cancel':
        await update.message.reply_text(
            "Чат с ИИ завершен. Возвращаю в главное меню.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    
    # Проверяем лимит еще раз
    request_count = get_ai_request_count(user_id)
    if request_count >= MAX_DAILY_AI_REQUESTS:
        await update.message.reply_text(
            "⚠️ Лимит запросов исчерпан. Попробуйте завтра.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    
    # Показываем индикатор загрузки
    processing_msg = await update.message.reply_text("🤔 Обрабатываю ваш вопрос...")
    
    try:
        # Получаем ответ от ИИ
        ai_response = await chat_with_ai(user_message)
        
        # Обновляем счетчик запросов
        update_ai_request_count(user_id)
        new_count = request_count + 1
        
        # Безопасное удаление индикатора загрузки
        try:
            await processing_msg.delete()
        except Exception:
            pass  # Игнорируем ошибку если сообщение уже удалено
        
        # Отправляем ответ
        await update.message.reply_text(
            f"🤖 **Ответ ИИ-юриста:**\n\n{ai_response}\n\n"
            f"_⚠️ Это автоматический ответ. Для точной консультации обратитесь к юристу._\n\n"
            f"📊 Использовано запросов: {new_count}/{MAX_DAILY_AI_REQUESTS}\n\n"
            f"Задайте следующий вопрос или введите /cancel для выхода.",
            parse_mode="Markdown"
        )
        
        # Если это был последний запрос
        if new_count >= MAX_DAILY_AI_REQUESTS:
            await update.message.reply_text(
                "📌 Это был ваш последний бесплатный запрос на сегодня.\n"
                "Для продолжения консультации запишитесь к юристу.",
                reply_markup=main_keyboard()
            )
            return MAIN_MENU
        
        return AI_CHAT
        
    except Exception as e:
        # Безопасное удаление индикатора загрузки
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_text(
            f"❌ Произошла ошибка при обработке запроса.\n"
            f"Попробуйте переформулировать вопрос или обратитесь к юристу напрямую.\n\n"
            f"Ошибка: {str(e)}",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
