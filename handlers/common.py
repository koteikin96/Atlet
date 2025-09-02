from config import LAWYER_CHAT_ID
from ai_client import analyze_case_with_ai

async def notify_lawyer(context, user_data: dict):
    ai_analysis = await analyze_case_with_ai(user_data)

    message = f"""
🚨 *НОВАЯ ЗАЯВКА* #{user_data['request_id']}

*Клиент:* {user_data['full_name']}
*Телефон:* `{user_data['phone']}`
*Username:* @{user_data['username']}
*Долг:* {user_data.get('debt_amount', 'не указан')} руб.
*Доход:* {user_data.get('income_amount', 'не указан')} руб.

*🤖 АНАЛИЗ ИИ:*
{ai_analysis}

*Описание ситуации:*
{user_data.get('case_description', 'не указано')}
    """

    try:
        await context.bot.send_message(
            chat_id=LAWYER_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
