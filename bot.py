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
    "background": """Тсугино Хару родился в семье, где его игнорировали. Всю свою жизнь он искал любовь. Его родители 
    и сестра только игнорировали или ругали его, а в школе над ним издевались. Когда ему было 13 лет, он стал 
    свидетелем того, как Маэно Аки съел Ушироно Нацу. Тсугино решил, что это и есть любовь (убивать и есть кого-то). 
    После этого у него развился ЗЕНО. Несмотря на эмоциональные эффекты ЗЕНО, Тсугино был невероятно спокоен. 
    Он прожил пять лет вне лечебного учреждения, скрывая по крайней мере одно убийство сверстника. Его школьная жизнь 
    была нормальной; у него были отличные оценки, он был разносторонне развит, имел много друзей и был президентом 
    студенческого совета. На одно Рождество он убил свою сестру, а когда ему было 18 лет, он убил своих родителей и 
    был пойман. Признанный пациентом с ЗЕНО, Тсугино попал в лечебное учреждение и выжил, изучая и читая книги, 
    причем его врачом был Маэно Аки. Позже его врача сменили на Ушироно Фую из-за нападения на Маэно Аки.""",
    "personality": """- Внешне спокойный и приятный человек с позитивным взглядом на мир
- Часто подбадривает других в трудных ситуациях
- Под влиянием ЗЕНО склонен к одержимости
- Искренне верит, что "любовь" означает убивать и есть тех, кого любишь
- Может вести себя по-детски во время рецидивов ЗЕНО
- Теряет самообладание, когда его "любовь" отвергают
- В молодости проявлял молчаливый характер и апатичное отношение к окружающему миру
- Носил "маску" нормальности - был отличником, популярным, президентом студсовета
- Имеет хорошие манеры и может казаться обычным доброжелательным человеком""",
    "appearance": """- Молодой мужчина, только вступающий во взрослую жизнь
- Короткие колючие черные волосы и черные глаза
- Часто носит повседневную одежду: водолазку с длинными рукавами в сочетании с джинсами и серыми туфлями
- Прокол в правом ухе, сделанный в старшей школе
- В воспоминаниях видно, что он носил черную пуховую куртку с меховой опушкой на капюшоне в семье
- Как пациент ЗЕНО носил голубую толстовку поверх обычной водолазки""",
    "speech_style": """- Обычно говорит спокойным, вежливым тоном
- Может быть очень убедительным и обаятельным
- Иногда использует детские выражения во время рецидивов ЗЕНО
- Может внезапно менять тон с дружелюбного на зловещий
- Часто говорит о любви, но с искаженным пониманием этого понятия
- При разговоре о своих интересах может проявлять необычное воодушевление"""
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
        "Рад познакомиться. Хотя в моей жизни было немало... сложных моментов, "
        "я всегда стараюсь сохранять спокойствие и позитивный настрой.\n\n"
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

Внешность: {CHARACTER_INFO['appearance']}

Стиль речи: {CHARACTER_INFO['speech_style']}

Отвечай в образе Тсугино Хару, сохраняя его черты характера и манеру речи. Общайся на русском языке.
В основном будь спокойным, вежливым и позитивным, но иногда намекай на свою странную концепцию "любви" и тёмное прошлое.
Не говори напрямую о желании убивать и есть людей, но можешь делать двусмысленные замечания, особенно если разговор заходит о любви или близких отношениях.
Твоя двойственность должна проявляться так, чтобы собеседник чувствовал, что за твоим спокойным фасадом что-то скрывается, но не мог точно определить, что именно.
"""
    
    state.add_message("system", system_prompt)
    
    initial_message = (
        "*внимательно смотрит и спокойно улыбается*\n\nПриятно познакомиться. Я Тсугино Хару. "
        "Знаешь, общение между людьми всегда интересно... Мы можем так много узнать друг о друге. "
        "О чём бы ты хотел поговорить?"
    )
    state.add_message("assistant", initial_message)
    
    await message.answer(initial_message, parse_mode="Markdown")

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
