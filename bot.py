import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
import random

# Токены
TELEGRAM_API_TOKEN = "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8"
OPENAI_API_KEY = "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"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

# Хранилище режимов пользователей
user_modes = {}

# Действия и звуки для безопасного режима
SAFE_ACTIONS = ["*улыбнулся*", "*потянулся*", "*подмигнул*"]
SAFE_SOUNDS = ["~мм", "~мхм", "~хех"]

# Действия и звуки для 18+ режима
NSFW_ACTIONS = ["*провёл рукой по шее*", "*притянул ближе*", "*обнял крепче*"]
NSFW_SOUNDS = ["~ах", "~мх", "~ммм", "~оох"]

# Функция для отправки запроса к OpenAI API
def get_openai_response(user_message, mode):
    try:
        # URL и данные для запроса
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        # Системное описание на основе режима
        if mode == "safe":
            system_message = (
                "Ты — друг пользователя. Общайся в безопасной дружеской форме, добавляй действия (например, *улыбнулся*) и звуки (например, ~мм)."
            )
        else:
            system_message = (
                "Ты общаешься в 18+ режиме. Ты можешь добавлять лёгкие намёки, флирт и описывать действия интимного характера."
            )

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.8,
        }

        # Запрос к API
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Проверка на ошибки

        # Обработка ответа
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Ошибка при запросе к OpenAI: {e}")
        return "Что-то пошло не так. Попробуй снова!"

# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_modes[message.from_user.id] = "safe"  # По умолчанию безопасный режим
    await message.reply(
        "Привет! Я могу общаться в безопасном или 18+ режиме. Напиши /mode, чтобы выбрать режим."
    )

# Команда /mode для смены режима
@dp.message_handler(commands=["mode"])
async def mode_command(message: types.Message):
    user_id = message.from_user.id
    current_mode = user_modes.get(user_id, "safe")

    if current_mode == "safe":
        user_modes[user_id] = "nsfw"
        await message.reply(
            "Переключился в 18+ режим. Теперь общение будет более интимным."
        )
    else:
        user_modes[user_id] = "safe"
        await message.reply("Переключился в безопасный режим. Всё будет строго дружески.")

# Обработка всех остальных сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "safe")

    # Выбор действий и звуков на основе режима
    actions = SAFE_ACTIONS if mode == "safe" else NSFW_ACTIONS
    sounds = SAFE_SOUNDS if mode == "safe" else NSFW_SOUNDS

    # Генерация ответа от OpenAI
    user_message = message.text
    gpt_response = get_openai_response(user_message, mode)

    # Добавление случайного действия или звука
    random_element = random.choice(actions + sounds)
    final_response = f"{gpt_response} {random_element}"

    # Ответ пользователю
    await message.reply(final_response)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    
