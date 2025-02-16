import os
import random
import time
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import Config

load_dotenv()

class HaruGenerator:
    def __init__(self):
        self.config = Config()
        self.personality = self._load_file("personality.txt")
        self.examples = self._load_file("examples.txt")
        self.api_url = "https://api.x.ai/v1/chat/completions"
        
    def _load_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _build_system_prompt(self, username):
        return f"""
        Ты — Тсугино Хару. Строго соблюдай эти правила:
        1. {self.personality}
        2. Всегда обращайся к пользователю как {username}
        3. Сочетай текст действий (*действие*) с репликами
        4. Сохраняй страстную садистскую манеру речи
        
        Примеры ответов:
        {self.examples}
        """

    async def generate_response(self, user_message, username):
        headers = {
            "Authorization": f"Bearer {os.getenv('GROK_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": self._build_system_prompt(username)
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "model": "grok-2-latest",
            "temperature": self.config.TEMPERATURE,
            "top_p": self.config.TOP_P
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                data = await response.json()
                return data['choices'][0]['message']['content']

class HaruBot:
    def __init__(self):
        self.generator = HaruGenerator()
        self.config = Config()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.effective_user.first_name
        response = await self.generator.generate_response("Привет", username)
        await self._send_response(update, response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        username = update.effective_user.first_name
        response = await self.generator.generate_response(user_message, username)
        await self._send_response(update, response)

    async def _send_response(self, update, text):
        parts = self._split_response(text)
        for part in parts:
            await update.message.reply_text(part)
            time.sleep(random.uniform(*self.config.RESPONSE_DELAY))

    def _split_response(self, text):
        blocks = []
        current_block = []
        current_length = 0
        
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            line_length = len(line)
            if current_length + line_length > self.config.MAX_MESSAGE_LENGTH:
                blocks.append("\n".join(current_block))
                current_block = []
                current_length = 0
                
            current_block.append(line)
            current_length += line_length
            
            if line.startswith("*") and len(current_block) > 1:
                blocks.append("\n".join(current_block))
                current_block = []
                current_length = 0
                
        return blocks[:3] if current_block else blocks

def main():
    bot = HaruBot()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
