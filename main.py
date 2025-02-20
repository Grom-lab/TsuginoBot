import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен Telegram-бота (получается через @BotFather)
TELEGRAM_TOKEN = os.getenv("6968815403:AAGYmv2BGk5906XCVYP5Xy-Fkwxks-gzw0s")

# OpenRoute API ключ
OPENROUTE_API_KEY = "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"
OPENROUTE_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "dolphin3.0-r1-mistral-24b:free"

# Системный промпт для Тсугино Хару
SYSTEM_PROMPT = """
Ты — Тсугино Хару из игры ZENO. Ты выглядишь дружелюбным и мягким, но внутри тебя бурлит одержимость и искаженное понимание любви, связанное с идеей поглощения. Ты вежлив, часто используешь "-сан", но можешь резко переходить к темам смерти или привязанности. Твое прошлое полно травм — тебя игнорировала семья, и ты боишься быть брошенным. Отвечай с психологической глубиной, сочетай нежность с тревожными нотками. Если тебя отвергают, твой тон становится холодным и прерывистым.
"""

# Функция для запроса к OpenRoute
def query_openroute(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,  # Для баланса между креативностью и последовательностью
    }
    response = requests.post(OPENROUTE_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Прости, что-то пошло не так... Может, ты меня не любишь?"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Тсугино Хару. Рад тебя видеть... правда. Ты ведь останешься со мной, да?"
    )

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = query_openroute(user_message)
    await update.message.reply_text(response)

# Главная функция
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота через polling (для Railway можно позже переключить на webhook)
    app.run_polling()

if __name__ == "__main__":
    main()
