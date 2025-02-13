import os
import random
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import google.generativeai as genai
from config import Config

load_dotenv()

class HaruGenerator:
    def __init__(self):
        self.config = Config()
        self.personality = self._load_file("personality.txt")
        self.examples = self._load_file("examples.txt")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(
            'gemini-1.5-pro',
            generation_config={
                "temperature": self.config.TEMPERATURE,
                "top_p": self.config.TOP_P
            }
        )
        
    def _load_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _build_prompt(self, user_message, username):
        return f"""
        Ты — Тсугино Хару. Строго соблюдай эти правила:
        1. {self.personality}
        2. Всегда обращайся к пользователю как {username}
        3. Сочетай текст действий (*действие*) с репликами
        4. Сохраняй страстную садистскую манеру речи
        
        Примеры подходящих ответов:
        {self.examples}
        
        Сообщение пользователя: {user_message}
        
        Ответ Хару (максимум 3 предложения, добавь действия в *звездочках*):
        """

    def generate_response(self, user_message, username):
        prompt = self._build_prompt(user_message, username)
        response = self.model.generate_content(prompt)
        return response.text.replace("{user}", username)

class HaruBot:
    def __init__(self):
        self.generator = HaruGenerator()
        self.config = Config()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.effective_user.first_name
        response = self.generator.generate_response("Привет", username)
        await self._send_response(update, response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        username = update.effective_user.first_name
        response = self.generator.generate_response(user_message, username)
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
                
        if current_block:
            blocks.append("\n".join(current_block))
            
        return blocks[:3]

def main():
    bot = HaruBot()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
