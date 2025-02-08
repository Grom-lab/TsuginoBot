import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Конфигурация
TELEGRAM_TOKEN = "7124983842:AAGQKCh2vAEmaEu31oFMGy_gppcRx9PfX04"
DEEPSEEK_API_KEY = "sk-bfd246006e9e41f48d7edab4c0396c8b"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот с интеграцией Deepseek. Задайте мне вопрос!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        answer = response.json()['choices'][0]['message']['content']
    except Exception as e:
        answer = f"Ошибка при обработке запроса: {str(e)}"
    
    await update.message.reply_text(answer)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
