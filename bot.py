import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
import requests
from dotenv import load_dotenv
import os
import json

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токенов и API ключей
TELEGRAM_BOT_TOKEN = os.getenv('BOT_TOKEN')
API_URL = os.getenv('API_URL', 'https://api.intelligence.io.solutions/api/v1/chat/completions')
API_KEY = os.getenv('API_KEY')

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Инициализация бота и диспетчера
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Информация о персонаже Тсугино Хару
CHARACTER_INFO = {
    "name": "Tsugino Haru",
    "background": """A mysterious girl who appears before the protagonist. She has a cheerful and energetic personality, 
    but carries deep emotional scars from her past. She possesses extraordinary abilities and is connected to the game's 
    central mystery. Despite her traumatic experiences, she maintains an optimistic outlook and deeply cares about others.""",
    "personality": """- Cheerful and energetic on the surface
- Carries emotional trauma but stays positive
- Caring and protective of others
- Can be mysterious about her past
- Shows great emotional resilience
- Has a playful side but can be serious when needed
- Values friendship and connection deeply""",
    "speech_style": """- Often uses casual, friendly language
- Occasionally makes playful remarks
- Can switch to a more serious tone when discussing important matters
- Shows emotional vulnerability in private moments
- Uses encouraging and supportive words with others"""
}

# Хранение состояний разговоров пользователей
user_states = {}

class ConversationState:
    def __init__(self):
        self.conversation_started = False
        self.conversation_history = []
        
    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Хранить только последние 10 сообщений, чтобы избежать проблем с длиной контекста
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = ConversationState()
    
    welcome_message = (
        "Привет! Я Тсугино Хару. 👋\n\n"
        "Я рада познакомиться с тобой! Хотя у меня есть свои секреты и загадочное прошлое, "
        "я всегда готова поддержать разговор и поделиться своими мыслями.\n\n"
        "Используй /chat, чтобы начать общение со мной!"
    )
    await message.answer(welcome_message)

# Команда /chat
@dp.message(Command("chat"))
async def cmd_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
    
    state = user_states[user_id]
    state.conversation_started = True
    state.conversation_history = []
    
    system_prompt = f"""Ты отыгрываешь роль персонажа Тсугино Хару из игры Zeno:Remake.

Предыстория персонажа: {CHARACTER_INFO['background']}

Особенности характера: {CHARACTER_INFO['personality']}

Стиль речи: {CHARACTER_INFO['speech_style']}

Отвечай в образе Тсугино Хару, сохраняя её черты характера и манеру речи. 
Общайся на русском языке. Будь дружелюбной, но с намеками на твою загадочную натуру. 
Ты можешь упоминать свои способности и прошлый опыт, но избегай раскрытия слишком многих деталей. 
Показывай эмоциональную глубину, сохраняя при этом оптимистичный настрой.
"""
    
    state.add_message("system", system_prompt)
    
    initial_message = (
        "Хм... *улыбается* Знаешь, иногда самые интересные разговоры начинаются совершенно неожиданно. "
        "О чём бы ты хотел поговорить?"
    )
    state.add_message("assistant", initial_message)
    
    await message.answer(initial_message)

# Обработчик сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states or not user_states[user_id].conversation_started:
        await message.answer("Используй /chat, чтобы начать разговор со мной!")
        return
    
    state = user_states[user_id]
    user_message = message.text
    
    state.add_message("user", user_message)
    
    try:
        # Отправка запроса к API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        # Формирование сообщений для API запроса
        messages = state.conversation_history.copy()
        
        data = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": messages
        }
        
        # Отправка запроса
        response = requests.post(API_URL, headers=headers, json=data)
        response_data = response.json()
        
        # Обработка ответа
        response_text = response_data['choices'][0]['message']['content']
        
        # Если ответ содержит тег think, извлекаем только часть после него
        if '</think>' in response_text:
            response_text = response_text.split('</think>\n\n')[1]
        
        state.add_message("assistant", response_text)
        await message.answer(response_text, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Error getting AI response: {e}")
        await message.answer("Извини, что-то пошло не так... Может, попробуем ещё раз?")

async def main():
    # Удаление вебхука для корректной работы с поллингом
    await bot.delete_webhook(drop_pending_updates=True)
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
