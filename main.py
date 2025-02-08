import os
import asyncio
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from aiohttp import web

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_MODEL = "deepseek-chat"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

async def start(update: Update, context):
    await update.message.reply_text("🤖 Бот активен!")

async def handle_message(update: Update, context):
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": update.message.text}],
            temperature=0.7
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("🚧 Технические неполадки")

async def healthcheck(request):
    return web.Response(text="OK")

async def main():
    # Инициализация Telegram бота
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск веб-сервера
    web_app = web.Application()
    web_app.router.add_get('/health', healthcheck)
    runner = web.AppRunner(web_app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8000))).start()

    # Запуск Telegram бота
    await telegram_app.initialize()
    await telegram_app.start()
    
    print("🟢 Все системы активны")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
