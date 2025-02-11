import os
import logging
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Загрузка переменных окружения из файла .env
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
    model_name="gemini-2.0-flash-thinking-exp-01-21",  #  Или другая подходящая модель
    generation_config=generation_config,
)


#  ПРОМПТ ДЛЯ ЛИЧНОСТИ (ВАЖНО!)
CHARACTER_PROMPT = """
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

Примеры фраз:
* "Эм... З-здравствуйте..."
* "И-извините... Я... я не уверен..."
* "П-простите, что помешал..."
* "Н-ну... м-может быть..."
* "Я... я постараюсь..."
* "Б-большое спасибо..."
* "Э-это... к-как бы... с-сложно сказать..."

Твоя задача -  вжиться в эту роль и отвечать на сообщения пользователей *исключительно* как Тсугино Хару, имитируя его манеру речи, характер и  знания.
"""

# Создание сессии чата с начальным промптом
chat_session = model.start_chat(history=[
    {"role": "user", "parts": [CHARACTER_PROMPT]},
    {"role": "model", "parts": ["Эм... З-здравствуйте... Я - Тсугино Хару..."]},  # Начальное приветствие от лица персонажа
])


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Эм... З-здравствуйте... Я - Тсугино Хару...')  # Приветствие от лица персонажа

# Обработчик текстовых сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Показываем, что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    try:
        #  Добавляем напоминание о роли перед каждым запросом (не обязательно, но может улучшить стабильность)
        full_prompt = f"{user_input}"  #  Можно и без напоминания, если модель хорошо держит роль
        response = chat_session.send_message(full_prompt)

        # Разделение длинного сообщения на части
        max_length = 4096
        if len(response.text) > max_length:
            for i in range(0, len(response.text), max_length):
                part = response.text[i:i + max_length]
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text("П-простите... П-произошла какая-то ошибка... И-извините...") #  Ответ в стиле персонажа


# Основная функция
def main():
    # Инициализация бота
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
