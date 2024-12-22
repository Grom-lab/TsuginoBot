import logging
from aiogram import Bot, Dispatcher, executor, types
import openai
import random

# Telegram API токен
TELEGRAM_API_TOKEN = "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8"

# OpenAI API токен
OPENAI_API_KEY = "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"

# Устанавливаем API-ключ OpenAI
openai.api_key = OPENAI_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

# Описание действий и звуков
ACTIONS = [
    "*потянулся*", "*зевнул*", "*улыбнулся*", "*подмигнул*", "*посмотрел на тебя*"
]

SOUNDS = ["~ах", "~мх", "~мхм", "~мм"]

# Описание персонажа
CHARACTER_DESCRIPTION = """
Ты — друг пользователя. Общение непринужденное и дружеское. Ты часто вставляешь действия (в формате *действие*) 
и звуки (в формате ~звук) для создания более живой беседы.
"""

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет! Давай просто поболтаем. Пиши что угодно, а я поддержу разговор!")

# Обработка сообщений
@dp.message_handler()
async def chat_with_character(message: types.Message):
    try:
        # Генерация действия или звука
        action_or_sound = random.choice(ACTIONS + SOUNDS)

        # Запрос в OpenAI для генерации ответа
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": CHARACTER_DESCRIPTION},
                {"role": "user", "content": message.text}
            ]
        )

        # Ответ OpenAI
        gpt_reply = response["choices"][0]["message"]["content"]

        # Формируем итоговый ответ
        reply = f"{gpt_reply} {action_or_sound}"
        await message.reply(reply)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.reply("Что-то пошло не так. Давай попробуем ещё раз!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    
