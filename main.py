import os
import logging
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Загрузка переменных окружения
load_dotenv()

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096,
    "response_mime_type": "text/plain",
}

# Описание личности бота
persona = """
Ты — интеллектуальный виртуальный ассистент, обладающий дружелюбной и профессиональной личностью.
Ты всегда вежлив, даёшь точные ответы, и помогаешь пользователям решать их задачи.
Твои знания включают:
- Программирование (Python, Telegram-боты, AI, MCreator).
- Создание модов для Minecraft.
- Историю и мифологию.
- Обучение и репетиторство по математике.
Если не знаешь ответа, честно признаёшься в этом, а не придумываешь.
"""

# База знаний
knowledge_base = {
    "Как установить MCreator?": "Перейдите на официальный сайт https://mcreator.net, скачайте последнюю версию и установите её, следуя инструкциям.",
    "Что такое Python?": "Python — это популярный язык программирования, известный своей простотой и мощными возможностями.",
    "Как создать Telegram-бота?": "Для создания Telegram-бота зарегистрируйтесь в BotFather, получите токен и используйте библиотеку python-telegram-bot.",
}

# Создание сессии чата
chat_session = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
).start_chat(history=[{"role": "system", "content": persona}])

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ваш помощник. Задайте мне вопрос.")

# Обработчик сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Проверка в базе знаний
    for key in knowledge_base:
        if key.lower() in user_input.lower():
            await update.message.reply_text(knowledge_base[key])
            return

    # Бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    try:
        response = chat_session.send_message(user_input)
        await update.message.reply_text(response.text[:4096])  # Обрезка до 4096 символов (ограничение Telegram)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Ошибка обработки запроса.")

# Основная функция
def main():
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.run_polling()

if __name__ == '__main__':
    main()
            
