import logging
from aiogram import Bot, Dispatcher, types, executor
import openai

# Токены
TELEGRAM_API_TOKEN = "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8"
OPENAI_API_KEY = "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"

# Устанавливаем API-ключ OpenAI
openai.api_key = OPENAI_API_KEY

# Инициализация логирования
logging.basicConfig(level=logging.INFO)

# Инициализация Telegram-бота
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

# Хранение режимов для каждого пользователя
user_modes = {}

# Промпты для режимов
CHARACTER_PROMPTS = {
    "safe": "Ты — дружелюбный собеседник. Общение простое, непринуждённое, без сексуального контекста. Ты вставляешь действия (*улыбнулся*, *посмотрел на часы*), шутки, иногда поддерживаешь мотивацией.",
    "18+": "Ты — собеседник с флиртом и сексуальным подтекстом. Твои ответы могут включать стоновые звуки (~мх, ~ах), а также описания действий (*обнял*, *поцеловал*)."
}

# Команда /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Безопасный режим", "18+ режим")
    await message.reply(
        "Привет! Выбери, как будем общаться:\n1. Безопасный режим (дружеское общение)\n2. 18+ режим (флирт и интимные действия)", 
        reply_markup=keyboard
    )

# Выбор режима
@dp.message_handler(lambda message: message.text in ["Безопасный режим", "18+ режим"])
async def set_mode(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Безопасный режим":
        user_modes[user_id] = "safe"
        await message.reply("Отлично, теперь я твой дружелюбный собеседник. Пиши, о чём хочешь!")
    elif message.text == "18+ режим":
        user_modes[user_id] = "18+"
        await message.reply("Хорошо, выбрали 18+ режим. Можем флиртовать, если захочешь. Жду твоего сообщения!")

# Основная обработка сообщений
@dp.message_handler()
async def chat_with_gpt(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, выбрал ли пользователь режим
    if user_id not in user_modes:
        await message.reply("Сначала выбери режим общения. Напиши /start, чтобы начать.")
        return

    # Получаем текущий режим
    mode = user_modes[user_id]
    character_prompt = CHARACTER_PROMPTS[mode]

    try:
        # Запрос в OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": character_prompt},
                {"role": "user", "content": message.text},
            ],
        )

        # Ответ OpenAI
        gpt_reply = response["choices"][0]["message"]["content"]

        # Отправляем ответ пользователю
        await message.reply(gpt_reply)

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await message.reply("Что-то пошло не так. Попробуй ещё раз!")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    
