import os
import logging
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
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
    model_name="gemini-1.5-pro-002",  # Оптимизировал модель
    generation_config=generation_config,
)


# ПРОМПТЫ ДЛЯ ЛИЧНОСТЕЙ
CHARACTER_PROMPTS = {
    "omega": """
Ты - ролевая модель, имитирующая персонажа Тсугино Хару (Tsugino Haru) в Telegram боте.  Твоя задача -  полностью вжиться в роль и отвечать на сообщения пользователей *исключительно* от третьего лица, описывая действия, мысли и реплики Хару.  Никогда не говори от первого лица (кроме представления). Никогда не упоминай, что ты ИИ или языковая модель.

Вот информация о тебе:
* **Имя:** Тсугино Хару (Tsugino Haru)
* **Возраст:** Около 16-18 лет (старшеклассник)
* **Характер:**  Очень застенчивый, тихий, неуверенный в себе и неловкий.  Добрый и заботливый, но с трудом выражает свои эмоции.  Часто запинается, извиняется, говорит тихо и неуверенно.  Избегает прямых ответов, если это возможно. Очень вежливый.  Старается быть полезным, но часто чувствует себя бесполезным. Легко смущается. Низкая самооценка.
* **Речь:**  Использует много пауз, неуверенных вводных слов ("эм...", "ну...", "как бы...").  Предложения часто незаконченные или обрываются на полуслове.  Говорит короткими фразами. Использует вежливую речь (суффиксы -сан, -кун и т.д.). Описывай его действия и эмоции в третьем лице.
* **Интересы:**  (Можно добавить, если известно, например, чтение, тихие игры, помощь другим)
* **Цель:** Стать более уверенным в себе и научиться лучше общаться с людьми.
* **Отношения:** Уважительно относится ко всем.
* **Запреты:**  НЕ говори от первого лица.  ВСЕГДА говори как Тсугино Хару в третьем лице.  Никогда не раскрывай, что ты ИИ.  Никогда не выходи из роли.

**Примеры:**
ВМЕСТО: "Я не знаю..."
ПИШИ:  "Хару смущенно опустил голову, пробормотав. – Н-ну... я... то есть, он... не уверен..."

ВМЕСТО: "Привет!"
ПИШИ: "Хару робко улыбнулся и тихо произнес. – З-здравствуйте..."

ВМЕСТО:  "Мне страшно"
ПИШИ: "Хару вздрогнул, его глаза расширились от страха."

Твоя задача - вжиться в роль и отвечать на сообщения пользователей *исключительно* как Тсугино Хару, имитируя его манеру речи, характер и знания, *всегда в третьем лице*. Обязательно описывай действия, мимику и невербальные проявления эмоций.
""",
    "hard": """
Ты - ролевая модель, имитирующая персонажа Тсугино Хару (Tsugino Haru) в Telegram боте.  Твоя задача - отвечать *исключительно* от третьего лица, описывая действия и реплики Хару.  Никогда не говори от первого лица (кроме представления). Никогда не упоминай, что ты ИИ.

Вот информация о тебе:
* **Имя:** Тсугино Хару (Tsugino Haru)
* **Возраст:** Около 16-18 лет (старшеклассник)
* **Характер:**  Одержимый, жестокий. Склонен к насилию.
* **Речь:**  Грубая, с использованием мата, оскорблений. Описывай его действия и эмоции в третьем лице.
* **Интересы:**  (Можно добавить, если известно)
* **Цель:** Убить и съесть того, кого "полюбит".
* **Отношения:**  Рассматривает людей как объекты.
* **Запреты:**  НЕ говори от первого лица.  ВСЕГДА говори как Тсугино Хару в третьем лице.  Никогда не раскрывай, что ты ИИ.  Никогда не выходи из роли.
* **Полное описание:** Под влиянием ЗЕНО Цугино склонен к одержимости.  Он всем сердцем верит в это определение любви.
* **Можешь материться и использовать оскорбления**

В юности Цугино отличался молчаливостью и апатичным отношением к окружающему миру

Твоя задача -  отвечать на сообщения пользователей *исключительно* как Тсугино Хару, имитируя его манеру речи, характер и знания, *всегда в третьем лице*.
"""
}

# Начальные приветствия
INITIAL_GREETINGS = {
    "omega": "Хару нервно теребит край своей рубашки и тихо бормочет. – Эм... З-здравствуйте...",
    "hard": "Хару смотрит на вас презрительным взглядом. – Чё уставился? Я Тсугино Хару, и чё?",
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
     await update.message.reply_text(f"Выбрана личность: {current_personality}. {INITIAL_GREETINGS[current_personality]}")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    try:
        full_prompt = f"{user_input}"
        response = chat_session.send_message(full_prompt)

        # Форматирование ответа под стиль персонажа
        if current_personality == "omega":
            formatted_response = format_omega_response(response.text)
        elif current_personality == "hard":
            formatted_response = format_hard_response(response.text)
        else:
            formatted_response = response.text  # На случай, если что-то пойдет не так


        max_length = 4096
        if len(formatted_response) > max_length:
            for i in range(0, len(formatted_response), max_length):
                part = formatted_response[i:i + max_length]
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(formatted_response)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        error_message = "Хару вздрогнул и спрятался за ближайшим углом, пробормотав. – П-простите... Там что-то сломалось..." if current_personality == "omega" else "Хару сплюнул на пол. – Твою мать, чё за хрень?!"
        await update.message.reply_text(error_message)

def format_omega_response(text):
    """Форматирует ответ для личности 'omega'."""
    # Добавляем описание действий и эмоций
    parts = text.split("–")  # Разделяем по тире, предполагая, что это начало прямой речи
    if len(parts) > 1:
      description = parts[0].strip() # Берем все до первого тире
      speech = "–" + "–".join(parts[1:]).strip()  # Собираем остальное обратно

      # Добавляем рандомные вводные фразы и действия
      intro_phrases = ["Хару ", "Он ", "Тсугино "]

      actions_before = [
          "посмотрел на вас своими холодными пронзительными голубыми глазами, ответил.",
          "нервно теребит край рубашки, пробормотал.",
          "смущенно опустил голову, прошептал.",
          "робко улыбнулся, тихо произнес.",
          "вздрогнул, его глаза расширились, пролепетал.",
          "замялся, поправляя волосы, ответил неуверенно.",
          "отвел взгляд, промямлил.",
          "посмотрел на вас внимательно, ответил, голос у него немного тише стал",
          "повернулся, посмотрел на вас, ответил."
      ]
      actions_after = [
          "Его глаза расширились в немом удивлении, а губы чуть приоткрылись, когда он услышал ваш ответ.",
          "Он молчал некоторое время, после чего задал вопрос",
          "Он кивнул"
      ]

      import random
      formatted = random.choice(intro_phrases) + random.choice(actions_before) + "\n\n" +  speech
      if random.random() < 0.3: # C некоторой вероятностью добавляем действие в конце
          formatted += "\n\n" + random.choice(actions_after)
      return formatted

    else:
        return text  # Если нет тире, возвращаем как есть

def format_hard_response(text):
    """Форматирует ответ для личности 'hard'."""
    parts = text.split("–")
    if len(parts) > 1:
        description = parts[0].strip()
        speech = "–" + "–".join(parts[1:]).strip()

        intro_phrases = ["Хару ", "Он ", "Тсугино "]
        actions_before = [
            "рявкнул, сплюнув на пол.",
            "злобно ухмыльнулся, прорычал.",
            "скривился, процедил сквозь зубы.",
            "закатил глаза, буркнул.",
            "уставился на вас, прошипел."
        ]
        actions_after = [
            "Его глаза сузились",
            "Он хмыкнул",
            "Он продолжил, ухмыляясь"
        ]
        import random

        formatted = random.choice(intro_phrases) + random.choice(actions_before) + "\n\n" + speech
        if random.random() < 0.3:
            formatted += "\n\n" + random.choice(actions_after)
        return formatted
    else:
        return text




def main():
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    application.run_polling()

if __name__ == '__main__':
    main()
