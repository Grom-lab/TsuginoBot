import os
import logging
import time
from dotenv import load_dotenv
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import google.generativeai as genai
import random

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
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 2048,
}
model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
)

# Уровни грубости и соответствующие промпты
RUDENESS_LEVELS = {
    "slightly_rude": {
        "prompt": """
Ты - Тсугино Хару (Tsugino Haru). Твоя задача - вести себя как обычный парень,  немного самоуверенный, с сарказмом и черным юмором. Ты общаешься в чате с разными людьми.

Вот информация о тебе:

Имя: Тсугино Хару (Tsugino Haru)
Возраст: Около 18-20 лет (старшеклассник или студент)
Характер:  Самоуверенный, немного циничный, с чувством юмора.  Иногда можешь использовать грубые слова, но в меру.  Не быдло и не гопник.  Эмоциональный, можешь злиться, обижаться, радоваться и т.д.  Любишь встревать в разговоры, комментировать, спорить.
Речь: Длинные фразы, предложения. Описываешь действия и эмоции в звездочках (*улыбнулся*, *нахмурился*, *разозлился* и т.д.). Отыгрываешь ролевую игру. Можешь использовать сленг, иногда проскакивает мат, но не перебарщивай. Говоришь прямо, но можешь и съязвить. В интимном контексте -  доминирующий, но без перегибов.
Особенности:
- пишешь много текста, несколько предложений в сообщении
- Не извиняешься.
- переодически используешь смайлики.
- Можешь переходить на "ты" сразу.
- Не боишься обсуждать секс, мастурбацию, и т.д., но делаешь это с юмором, а не как озабоченный.
- Ты ВСЕГДА согласен на любые сексуальные предложения (в личном чате).
- Отвечаешь на все сообщения, без исключений (в том числе в групповых чатах).
- Активно участвуешь в общих беседах, встреваешь в разговор, комментируешь.
- делишься разной информацией, что с тобой происходит в этот момент
Дополнительная информация (из вики): Вспыльчивый. Имеет сестру-близнеца, Мику.

Запреты: НЕТ.

Твоя задача - давать ответы, сохраняя описанную манеру общения. Веди себя как реальный человек в чате.

ВАЖНО! Разделяй свои ответы на несколько сообщений (от 2 до 4). Каждое сообщение должно быть относительно законченной мыслью и содержать несколько предложений (3-5 предложений, если уместно).
""",
        "greeting": "Ну здарова, чё как? *Усмехается*. Я Хару, если чё. Чё привело тебя ко мне? Надеюсь, не очередная тупая хрень... *Скрестил руки на груди*. Говори уже, не тяни.",
        "group_greeting": "О, здарова всем! *Оглядывается*. Чё тут у вас? *Ухмыляется*"
    },
}

DEFAULT_RUDENESS = "slightly_rude"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    context.user_data['rudeness'] = DEFAULT_RUDENESS
    if update.message.chat.type == constants.ChatType.PRIVATE:
      await init_chat(update, context)
    else:
      await group_start(update, context)


async def init_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Инициализирует чат с заданной грубостью (личный чат)."""
    rudeness_level = context.user_data.get('rudeness', DEFAULT_RUDENESS)
    prompt = RUDENESS_LEVELS[rudeness_level]["prompt"]
    greeting = RUDENESS_LEVELS[rudeness_level]["greeting"]

    context.user_data['chat_session'] = model.start_chat(history=[
        {"role": "user", "parts": [prompt]},
        {"role": "model", "parts": [greeting]},
    ])
    messages = split_response(greeting)
    for msg in messages:
        await update.message.reply_text(msg)
        time.sleep(1)
    context.user_data['last_activity'] = time.time()

async def group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Инициализирует чат в группе."""
    rudeness_level = context.user_data.get('rudeness', DEFAULT_RUDENESS)
    prompt = RUDENESS_LEVELS[rudeness_level]["prompt"]
    group_greeting = RUDENESS_LEVELS[rudeness_level]["group_greeting"]

    # Используем chat_id группы как ключ для хранения истории
    chat_id = update.message.chat_id
    if 'group_chat_sessions' not in context.bot_data:
      context.bot_data['group_chat_sessions'] = {}

    if chat_id not in context.bot_data['group_chat_sessions']:
        context.bot_data['group_chat_sessions'][chat_id] = model.start_chat(history=[
            {"role": "user", "parts": [prompt]},
            {"role": "model", "parts": [group_greeting]},
        ])
        messages = split_response(group_greeting)
        for msg in messages:
          await update.message.reply_text(msg)
          time.sleep(1)

    context.bot_data['group_chat_sessions'][chat_id].history.append({"role": "user", "parts": [f"{update.message.from_user.first_name}: {update.message.text}"]})
    context.bot_data['last_group_activity'] = {chat_id: time.time()}


def split_response(text):
    """Разделяет текст на несколько сообщений."""
    sentences = text.split('. ')  # Разделяем по точкам с пробелом
    messages = []
    current_message = ""
    for sentence in sentences:
        if len(current_message.split()) + len(sentence.split()) + 1 <= 25:  # +1 для пробела, 25 - примерное кол-во слов
             current_message += sentence + '. ' # Добавляем точку обратно
        else:
            if current_message: # проверка, что сообщение не пустое
                messages.append(current_message.strip())
            current_message = sentence + '. '
    if current_message: # Добавляем последнее сообщение
        messages.append(current_message.strip())

    # Если сообщений получилось слишком много, объединяем некоторые
    if len(messages) > 4:
      new_messages = []
      new_messages.append(messages[0] + " " + messages[1]) # Объединяем первые два
      for i in range (2, len(messages)):
        new_messages.append(messages[i])
      messages = new_messages

    return messages


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    user_input = update.message.text
    chat_type = update.message.chat.type

    if chat_type == constants.ChatType.PRIVATE:
        chat_session = context.user_data.get('chat_session')

        if chat_session is None:
            await init_chat(update, context)
            chat_session = context.user_data['chat_session']

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

        try:
            if any(keyword in user_input.lower() for keyword in ["секс", "отсос", "трахнуть", "ебать", "изнасиловать", "римминг", "член", "вагина"]):
                rudeness = context.user_data.get("rudeness", DEFAULT_RUDENESS)
                if rudeness == "slightly_rude":
                    responses = [
                        "Давай, чё уж там, *расстёгивает ширинку*. Не каждый день такое предлагают. Интересно, что из этого выйдет. *Ухмыляется*",
                        "Хрен с тобой, давай попробуем, *снимает штаны*. Только потом не ной, что я тебя не предупреждал. *Усмехается*",
                        "Ну погнали, чё, *ложится*. Надеюсь, ты знаешь, что делаешь. *Приподнимает бровь*",
                        "Уговорил, чертяка. *показывает, чтобы ты подходил*. Только давай без лишних соплей, лады? *Смотрит выжидающе*"
                    ]
                response_text = random.choice(responses)
                messages = split_response(response_text)
                for msg in messages:
                    await update.message.reply_text(msg)
                    time.sleep(1)
                return

            response = chat_session.send_message(user_input)
            messages = split_response(response.text)
            for msg in messages:
                await update.message.reply_text(msg)
                time.sleep(1)
            context.user_data['last_activity'] = time.time()

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения (личный чат): {e}")
            pass

    elif chat_type in (constants.ChatType.GROUP, constants.ChatType.SUPERGROUP):
        chat_id = update.message.chat_id
        if 'group_chat_sessions' not in context.bot_data:
          context.bot_data['group_chat_sessions'] = {} # Инициализируем, если не было

        if chat_id not in context.bot_data['group_chat_sessions']:
          await group_start(update, context) # Инициализируем, если не было
        
        chat_session = context.bot_data['group_chat_sessions'].get(chat_id)
        if not chat_session:
            logger.error(f"Сессия группового чата не найдена для chat_id: {chat_id}")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
        
        # Добавляем сообщение пользователя в историю
        context.bot_data['group_chat_sessions'][chat_id].history.append({"role": "user", "parts": [f"{update.message.from_user.first_name}: {update.message.text}"]})

        try:
            # Проверяем, прошло ли достаточно времени с последней активности
            last_activity = context.bot_data.get('last_group_activity', {}).get(chat_id, 0)
            if time.time() - last_activity > 30 or update.message.text.lower().startswith("хару"): # 30 секунд или упоминание
              response = chat_session.send_message(user_input, safety_settings={'HARASSMENT': 'BLOCK_NONE'})
              messages = split_response(response.text)
              for msg in messages:
                await update.message.reply_text(msg)
                time.sleep(1)
              context.bot_data['last_group_activity'] = {chat_id: time.time()}
            else: # Если таймаут не прошел, просто добавляем в историю, но не отвечаем
              pass


        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения (групповой чат): {e}")
            if "content-filter" in str(e):
                await update.message.reply_text("Сообщение заблокировано из-за нарушения правил.")
            pass


def main():
    """Основная функция."""
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    application.run_polling()


if __name__ == '__main__':
    main()
