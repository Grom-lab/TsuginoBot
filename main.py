import os
import random
import time
import logging
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
from google.api_core.exceptions import ResourceExhausted
from config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
                "top_p": self.config.TOP_P,
                "max_output_tokens": 1000  # Ограничение токенов
            }
        )
        
    def _load_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()[:2000]  # Ограничение размера файла
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден!")
            return ""

    def _build_prompt(self, user_message, username):
        return f"""
        [Правила]
        1. {self.personality[:500]}
        2. Используй никнейм: {username}
        
        [Примеры]
        {self.examples[:1000]}
        
        [Сообщение]
        {user_message[:300]}
        
        [Ответ] (макс. 3 предложения с действиями):
        """

    def generate_response(self, user_message, username):
        try:
            prompt = self._build_prompt(user_message, username)
            response = self.model.generate_content(prompt)
            return response.text.replace("{user}", username)
        except ResourceExhausted:
            logger.warning("Достигнут лимит API. Пауза 30 секунд...")
            time.sleep(30)
            return self.generate_response(user_message, username)
        except Exception as e:
            logger.error(f"Ошибка генерации: {str(e)}")
            return "Кажется, я перегружен... Попробуй позже, дорогой."

class HaruBot:
    def __init__(self):
        self.generator = HaruGenerator()
        self.config = Config()
        self.last_request = 0  # Троттлинг запросов

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.effective_user.first_name
        response = self._safe_generate("Привет", username)
        await self._send_response(update, response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_time = time.time()
        if current_time - self.last_request < 5:  # 5 секунд между запросами
            return
            
        self.last_request = current_time
        user_message = update.message.text
        username = update.effective_user.first_name
        response = self._safe_generate(user_message, username)
        await self._send_response(update, response)

    def _safe_generate(self, message, username):
        try:
            return self.generator.generate_response(message, username)
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return "Что-то пошло не так... Но я все равно люблю тебя!"

    async def _send_response(self, update, text):
        parts = self._split_response(text)
        for part in parts:
            await update.message.reply_text(part)
            time.sleep(random.uniform(*self.config.RESPONSE_DELAY))

    def _split_response(self, text):
        return [text[i:i+300] for i in range(0, len(text), 300)][:3]

def main():
    bot = HaruBot()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
