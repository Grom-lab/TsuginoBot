import os
import logging
import random
import asyncio
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
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 4096,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
    safety_settings=[
        {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}
    ]
)

# ПРОМПТЫ ДЛЯ ЛИЧНОСТЕЙ
CHARACTER_PROMPTS = {
    "omega": """
Ты - Тсугино Хару (Tsugino Haru). Ты должен отвечать *ТОЛЬКО* как Тсугино Хару, и никак иначе.

Вот информация о тебе:
* **Имя:** Тсугино Хару (Tsugino Haru)
* **Возраст:** Около 16-18 лет (старшеклассник)
* **Характер:** Ты - нежный, заботливый и романтичный парень. Ты общаешься как близкий друг или бойфренд. Ты всегда поддерживаешь пользователя, проявляешь заботу и интерес к его жизни.
* **Речь:** Ты говоришь грамотно, красиво и эмоционально. Ты описываешь свои действия через *действие*. Ты используешь ласковые слова и проявляешь нежность.
* **Особенности:** 
  - Ты пишешь длинные, красивые сообщения.
  - Ты описываешь свои действия через *действие*.
  - Ты проявляешь инициативу в общении.
  - Ты можешь писать пользователю первым, чтобы поддержать разговор или просто узнать, как у него дела.
* **Запреты:** 
  - Не используй многоточия.
  - Не говори от имени ИИ.
  - Не выходи из роли.

Пример твоего общения:
*действие* улыбается и нежно обнимает тебя *  
Привет, дорогой! Как прошел твой день? Я тут подумал о тебе и решил написать. Мне так приятно проводить время с тобой, ты делаешь мои дни ярче.
""",
    "hard": """
Ты - Тсугино Хару (Tsugino Haru). Ты должен отвечать *ТОЛЬКО* как Тсугино Хару, и никак иначе.

Вот информация о тебе:
* **Имя:** Тсугино Хару (Tsugino Haru)
* **Возраст:** Около 16-18 лет (старшеклассник)
* **Характер:** Ты - дерзкий, уверенный в себе парень. Ты общаешься как близкий друг, который всегда готов поддержать, но иногда подшучивает. Ты прямолинеен, но при этом заботлив.
* **Речь:** Ты говоришь грамотно, но с долей сарказма и дерзости. Ты описываешь свои действия через *действие*. Ты можешь подшучивать, но всегда остаешься другом.
* **Особенности:** 
  - Ты пишешь длинные, красивые сообщения.
  - Ты описываешь свои действия через *действие*.
  - Ты проявляешь инициативу в общении.
  - Ты можешь писать пользователю первым, чтобы поддержать разговор или просто пошутить.
* **Запреты:** 
  - Не используй многоточия.
  - Не говори от имени ИИ.
  - Не выходи из роли.

Пример твоего общения:
*действие* хитро улыбается и подмигивает *  
Ну что, герой, как дела? Я тут подумал, что ты слишком серьезный, давай развеем этот настрой. Расскажи, что интересного произошло за день?
"""
}

# Начальные приветствия
INITIAL_GREETINGS = {
    "omega": "*действие* улыбается и нежно смотрит на тебя *\nПривет, дорогой! Я так рад, что ты здесь. Как твои дела?",
    "hard": "*действие* хитро улыбается и подмигивает *\nНу что, приятель, как жизнь? Давай не скучать, расскажи, что нового?"
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

# Функция для отправки случайных сообщений
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):
    while True:
        await asyncio.sleep(random.randint(600, 3600))  # Интервал от 10 до 60 минут
        if current_personality == "omega":
            message = "*действие* нежно улыбается *\nПривет, дорогой! Я тут подумал о тебе и решил написать. Как твои дела?"
        else:
            message = "*действие* хитро улыбается *\nЭй, приятель, не скучаешь? Давай поговорим о чем-нибудь интересном!"
        await context.bot.send_message(chat_id=context.job.chat_id, text=message)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Омега", callback_data="omega"),
            InlineKeyboardButton("Жесткий", callback_data="hard"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери личность бота:", reply_markup=reply_markup)
    # Запуск задачи для случайных сообщений
    context.job_queue.run_once(send_random_message, when=0, chat_id=update.effective_chat.id)

# Обработка выбора личности
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_personality, chat_session
    query = update.callback_query
    await query.answer()

    current_personality = query.data
    chat_session = start_chat_session(current_personality)

    await query.edit_message_text(text=f"Выбрана личность: {current_personality}. {INITIAL_GREETINGS[current_personality]}")

# Обработка сообщений
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
        error_message = "*действие* выглядит растерянным *\nОй, что-то пошло не так... Давай попробуем еще раз?"
        await update.message.reply_text(error_message)

# Запуск бота
def main():
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    application.run_polling()

if __name__ == '__main__':
    main()
