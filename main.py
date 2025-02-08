import os
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler

# Конфигурация
DEEPSEEK_API_KEY = "sk-bfd246006e9e41f48d7edab4c0396c8b"
TELEGRAM_TOKEN = "7124983842:AAGQKCh2vAEmaEu31oFMGy_gppcRx9PfX04"
DEEPSEEK_MODEL = "deepseek-chat"

# Инициализация клиента DeepSeek
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот с интеллектом DeepSeek. Задайте мне любой вопрос!")

async def handle_message(update: Update, context):
    try:
        user_message = update.message.text
        
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": user_message},
            ],
            stream=False
        )
        
        bot_response = response.choices[0].message.content
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
