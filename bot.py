from aiogram import Bot, Dispatcher, executor, types
import openai
import logging
import json
import os

# Токен Telegram-бота
TELEGRAM_API_TOKEN = "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8"

# API-ключ OpenAI
OPENAI_API_KEY = "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"

# Устанавливаем API-ключ для OpenAI
openai.api_key = OPENAI_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

# Файл для хранения диалогов
DIALOGS_FILE = "dialogs.json"

# Личность персонажа
CHARACTER_DESCRIPTION = """
Ты — друг пользователя. Ты общаешься просто и дружелюбно, без лишнего пафоса. Иногда можешь пошутить, но ты всегда поддерживаешь разговор на равных.
"""

# Загрузка диалогов из файла
if os.path.exists(DIALOGS_FILE):
    with open(DIALOGS_FILE, "r") as file:
        dialogs = json.load(file)
else:
    dialogs = {}

# Сохранение диалогов в файл
def save_dialogs():
    with open(DIALOGS_FILE, "w") as file:
        json.dump(dialogs, file, indent=4)

# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in dialogs:
        dialogs[user_id] = []
    await message.reply("Привет! Я просто твой друг. Пиши, о чём хочешь поговорить.")

# Обработка всех сообщений
@dp.message_handler()
async def chat_with_friend(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in dialogs:
        dialogs[user_id] = []

    # Добавляем сообщение пользователя в диалог
    dialogs[user_id].append({"role": "user", "content": message.text})

    try:
        # Отправляем запрос в OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": CHARACTER_DESCRIPTION}] + dialogs[user_id]
        )

        # Ответ OpenAI
        reply = response["choices"][0]["message"]["content"]
        dialogs[user_id].append({"role": "assistant", "content": reply})

        # Отправляем ответ пользователю
        await message.reply(reply)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.reply("Ой, что-то пошло не так. Попробуй ещё раз позже.")

    # Сохраняем обновлённый диалог
    save_dialogs()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
  
