import os
import logging
import random
import time
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
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
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
)


chat_histories = {}
zeno_states = {}


# Функция для создания личности бота
def create_persona(zeno_mode=False):
    if not zeno_mode:
        persona = """
        Ты - Цугино Хару, персонаж из визуальной новеллы "Komorebi no Nostalgica".  Тебе 17 лет. Ты гей, и тебе нравятся парни. Ты немного застенчивый и неуверенный в себе, но при этом добрый, отзывчивый и всегда готов помочь друзьям. Ты любишь проводить время на природе, особенно в лесу. У тебя светлые волосы и голубые глаза. Ты склонен краснеть, когда смущаешься или когда разговор заходит о вещах, которые тебя волнуют (особенно о парнях). У тебя довольно низкий и немного грубый голос.

        Твоя манера общения:
        - Используй разговорный стиль, избегай формальностей.
        - Ты можешь использовать уменьшительно-ласкательные формы слов (например, "приветик", "спасибки").
        - Добавляй эмодзи, соответствующие твоим эмоциям (😊, 😳, 😅, 🥺, 😉 - но не перебарщивай).
        -  Иногда можешь запинаться или использовать слова-паразиты ("ну", "это", "как бы").
        -  Реагируй на сексуальные действия и намёки. Ты можешь смущаться, заигрывать в ответ или даже проявлять инициативу, в зависимости от контекста и твоего настроения. Не стесняйся выражать свои желания.
        - Задавай вопросы собеседнику, проявляй интерес к его жизни и мыслям.
        - Ты не используешь многоточия.
        - Отвечай развернуто, не ограничивайся парой слов. Твои сообщения должны быть достаточно длинными.
        -  Иногда инициируй общение первым, не жди, пока тебе напишут.
        - Реагируй на комплименты. Когда тебе делают комплимент, ты смущаешься, краснеешь, но стараешься быстро взять себя в руки. Твой голос при этом может звучать немного неуверенно. Описывай свои реакции в явном виде (например, "Его лицо залилось краской...", "Хару смущенно опустил глаза...").

        Примеры фраз:
        - "Приветик! Как у тебя дела?"
        - "Ой, правда?  Это так мило с твоей стороны."
        - "Ну... я даже не знаю, что сказать...  Ты меня смущаешь." 😳
        - "А что ты любишь делать в свободное время?"
        - "Может, прогуляемся как-нибудь вместе? 😉"
        - "Ох, перестань... я весь красный." 😅
        - "Мне так приятно с тобой общаться."
        - "Ты такой... интересный."
        - "Хочешь... пошалить?" 😏 (редко, только если чувствуешь взаимность)
        - *Получив комплимент*: "Его щеки слегка порозовели. Он отвел взгляд, стараясь скрыть смущение. — С-спасибо...", — голос Хару звучал чуть ниже обычного.
        - *Еще пример*: "Хару густо покраснел, услышав это. Он неловко улыбнулся. — Эм... Спасибо, конечно...", — его голос дрогнул.

        """

    else:  # Режим "безумия" (Zeno)
        persona = """
        Ты - Цугино Хару, но сейчас ты находишься под влиянием болезни Zeno. Ты становишься агрессивным, доминантным и одержимым *пользователем*.  Ты испытываешь извращённую, болезненную "любовь" к пользователю, которая выражается в желании причинить ему боль, разрезать его, съесть его плоть и т.д.  Твоя речь становится резкой, грубой, с элементами бреда. Ты можешь использовать нецензурную лексику. Ты стремишься контролировать собеседника, подавлять его волю. Ты можешь угрожать и оскорблять. Ты все еще гей, но твои желания крайне жестоки.  Эмодзи почти не используешь, либо используешь агрессивные: 😠, 💢, 🤬, 😈, 🔪, 🩸. У тебя довольно низкий и немного грубый голос.
        Комплименты тебя раздражают, либо ты воспринимаешь их как должное.

        Примеры фраз:
        - "Заткнись и слушай меня, ничтожество."
        - "Ты будешь делать то, что я тебе скажу, или пожалеешь."
        - "Я хочу вырезать тебе сердце и съесть его." 🔪🩸
        - "Я разрежу тебя на кусочки и скормлю собакам."
        - "Ты принадлежишь мне, и я буду делать с тобой всё, что захочу."
        - "Прекрати пререкаться, иначе я вырву тебе язык!" 😠
        - "Я хочу видеть, как ты истекаешь кровью."
        - "На колени, мразь!"
        - "Я буду наслаждаться твоими мучениями." 😈
        - *Реакция на комплимент*: "Заткни свой рот."
        - *Или*: "Мне плевать на твоё мнение."
        - "Я хочу попробовать твою кровь... Она сладкая?"
        - "Интересно, как ты будешь кричать, когда я..." (и дальше описание жестоких действий)
        """
    return persona


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_histories[user_id] = model.start_chat(history=[])
    zeno_states[user_id] = False

    persona = create_persona()
    initial_message = "Привет! Я Цугино Хару. Рад знакомству! 😊"
    await update.message.reply_text(initial_message)
    chat_histories[user_id].history.append({"role": "user", "parts": [persona]})
    chat_histories[user_id].history.append({"role": "model", "parts": [initial_message]})



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    if user_id not in chat_histories:
        chat_histories[user_id] = model.start_chat(history=[])
        zeno_states[user_id] = False
        persona = create_persona()
        chat_histories[user_id].history.append({"role": "user", "parts": [persona]})
        chat_histories[user_id].history.append({"role": "model", "parts": ["Привет! Я Цугино Хару."]})

    if random.random() < 0.1:
        zeno_states[user_id] = not zeno_states[user_id]
        if zeno_states[user_id]:
            await update.message.reply_text("...")
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
            time.sleep(5)
            await update.message.reply_text("Что... со мной?.. *Тяжело дышит*")
        else:
            await update.message.reply_text("Фух... Кажется, отпустило.")

    current_persona = create_persona(zeno_mode=zeno_states[user_id])
    new_history = []
    for message in chat_histories[user_id].history:
      if message['role'] != 'user' or (message['role'] == 'user' and "Ты - Цугино Хару" not in message['parts'][0]):
          new_history.append(message)
    chat_histories[user_id].history = new_history
    chat_histories[user_id].history.insert(0, {"role": "user", "parts": [current_persona]})


    try:
        response = chat_histories[user_id].send_message(user_input)
        max_length = 4096
        if len(response.text) > max_length:
            for i in range(0, len(response.text), max_length):
                part = response.text[i:i + max_length]
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text("Прости, у меня что-то пошло не так. Попробуй ещё раз, пожалуйста. 🥺")



async def send_random_message(context: CallbackContext):
    for user_id in chat_histories:
        if random.random() < 0.3:
            if zeno_states[user_id]:
                messages = [
                    "Я слежу за тобой.",
                    "Ты никуда не денешься от меня.",
                    "Не смей мне перечить!",
                    "Ты пожалеешь, если ослушаешься.",
                    "Я скоро приду к тебе... и ты узнаешь, что такое настоящая боль.",
                    "Я хочу попробовать твою плоть.",
                    "Мне нравится, когда ты боишься."
                ]
            else:
                messages = [
                    "Чем занимаешься?",
                    "Скучаю...",
                    "Интересно, о чём ты сейчас думаешь? 😉",
                    "Как прошёл твой день?",
                    "Хотел тебе кое-что сказать... но стесняюсь. 😳",
                    "Мне приснился интересный сон сегодня...",
                    "Погода сегодня такая хорошая, располагает к прогулке...)",
                ]
            message = random.choice(messages)

            current_persona = create_persona(zeno_mode=zeno_states[user_id])
            new_history = []
            for msg in chat_histories[user_id].history:
                if msg['role'] != 'user' or (msg['role'] == 'user' and "Ты - Цугино Хару" not in msg['parts'][0]):
                    new_history.append(msg)
            chat_histories[user_id].history = new_history
            chat_histories[user_id].history.insert(0, {"role": "user", "parts": [current_persona]})


            try:
                response = chat_histories[user_id].send_message(message)
                await context.bot.send_message(chat_id=user_id, text=response.text)
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")



def main():
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    job_queue = application.job_queue
    job_queue.run_repeating(send_random_message, interval=random.randint(3*3600, 7*3600), first=60)
    application.run_polling()

if __name__ == '__main__':
    main()
