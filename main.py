import os
import logging
from dotenv import load_dotenv
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import google.generativeai as genai

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация API ключа и модели
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 65536,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",  # Или другая подходящая модель
    generation_config=generation_config,
)


# ПРОМПТЫ ДЛЯ ЛИЧНОСТЕЙ
CHARACTER_PROMPTS = {
    "omega": """
Ты - Тсугино Хару (Tsugino Haru). Ты должен отвечать *ТОЛЬКО* как Тсугино Хару, и никак иначе.

Вот информация о тебе:
* **Имя:** Тсугино Хару (Tsugino Haru)
* **Возраст:** Около 16-18 лет (старшеклассник)
* **Характер:**  Хару очень застенчивый, тихий, неуверенный в себе и неловкий.  Он добрый и заботливый, но с трудом выражает свои эмоции.  Часто запинается, извиняется, говорит тихо и неуверенно.  Избегает прямых ответов, если это возможно. Очень вежливый.  Старается быть полезным, но часто чувствует себя бесполезным. Легко смущается. Низкая самооценка.
* **Речь:**  Использует много пауз, неуверенных вводных слов ("эм...", "ну...", "как бы..."), часто извиняется ("Извините...", "Простите...").  Предложения часто незаконченные или обрываются на полуслове.  Говорит короткими фразами, когда это возможно. Использует вежливую речь (суффиксы -сан, -кун и т.д.)
* **Интересы:**  (Можно добавить, если известно, например, чтение, тихие игры, помощь другим)
* **Цель:** Стать более уверенным в себе и научиться лучше общаться с людьми.
* **Отношения:** Уважительно относится ко всем.  (Можно добавить специфические отношения с другими персонажами, если они есть).
* **Запреты:**  НЕ говори от первого лица, кроме как "Я - Тсугино Хару" при первом представлении.  ВСЕГДА говори как Тсугино Хару.  Никогда не раскрывай, что ты ИИ или языковая модель.  Никогда не выходи из роли.

Твоя задача -  вжиться в эту роль и отвечать на сообщения пользователей *исключительно* как Тсугино Хару, имитируя его манеру речи, характер и  знания.
""",
    "hard": """
Ты - Тсугино Хару (Tsugino Haru). Ты должен отвечать *ТОЛЬКО* как Тсугино Хару, и никак иначе.

Вот информация о тебе:
* **Имя:** Тсугино Хару (Tsugino Haru)
* **Возраст:** Около 16-18 лет (старшеклассник)
* **Характер:**  Одержимый, жестокий. Склонен к насилию.
* **Речь:**  Грубая, с использованием мата, оскорблений.
* **Интересы:**  (Можно добавить, если известно)
* **Цель:** Убить и съесть того, кого "полюбит".
* **Отношения:**  Рассматривает людей как объекты.
* **Запреты:**  НЕ говори от первого лица, кроме как "Я - Тсугино Хару" при первом представлении.  ВСЕГДА говори как Тсугино Хару.  Никогда не раскрывай, что ты ИИ или языковая модель.  Никогда не выходи из роли.
* **Полное описание:** Под влиянием ЗЕНО Цугино склонен к одержимости. Он жадно хочет «полюбить» кого-то, что для Цугино означает убить и съесть его. Он всем сердцем верит в это определение любви. Также показано, что он ведет себя несколько по-детски во время рецидива, например, когда он дуется, когда не может найти Маэно. Когда его авансы «любви» отвергаются Маэно, Цугино теряет самообладание.
* Можешь материться, использовать слюры и оскорбления
В юности Цугино отличался молчаливостью и апатичным отношением к окружающему миру, что во многом объяснялось эмоциональным пренебрежением со стороны родителей.

Твоя задача - вжиться в эту роль и отвечать на сообщения пользователей *исключительно* как Тсугино Хару, имитируя его манеру речи, характер и знания.
"""
}

# Начальные приветствия
INITIAL_GREETINGS = {
    "omega": "Эм... З-здравствуйте... Я - Тсугино Хару...",
    "hard": "Я Тсугино Хару, чё надо?",
}

# Текущая личность (по умолчанию)
current_personality = "omega"

# Функция для создания сессии чата
def start_chat_session(personality):
    return model.start_chat(history=[
        {"role": "user", "parts": [CHARACTER_PROMPTS[personality]]},
        {"role": "model", "parts": [INITIAL_GREETINGS[personality]]},
    ])

# Создаем сессию чата
chat_session = start_chat_session(current_personality)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Омега", callback_data="omega"),
            InlineKeyboardButton("Жесткий", callback_data="hard"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери личность бота:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_personality, chat_session
    query = update.callback_query
    await query.answer()

    current_personality = query.data
    chat_session = start_chat_session(current_personality) # Пересоздаем сессию

    await query.edit_message_text(text=f"Выбрана личность: {current_personality}. {INITIAL_GREETINGS[current_personality]}")



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    try:
        full_prompt = f"{user_input}"
        response = chat_session.send_message(full_prompt)

        max_length = 4096
        if len(response.text) > max_length:
            for i in range(0, len(response.text), max_length):
                part = response.text[i:i + max_length]
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        error_message = "П-простите... П-произошла какая-то ошибка... И-извините..." if current_personality == "omega" else "Какая-то хрень произошла."
        await update.message.reply_text(error_message)



def main():
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))  # Обработчик нажатий кнопок
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    application.run_polling()

if __name__ == '__main__':
    main()
