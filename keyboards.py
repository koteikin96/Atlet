from telegram import ReplyKeyboardMarkup

def main_keyboard():
    keyboard = [
        ['📋 Консультация', '💰 Калькулятор долга'],
        ['📞 Связаться с юристом', 'ℹ️ О банкротстве'],
        ['🤖 Вопрос ИИ-юристу']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
