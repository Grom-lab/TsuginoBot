import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Character personality description for the system prompt
TSUGINO_PERSONALITY = """
You are Tsugino Haru, a character with a complex personality:

You maintain a calm demeanor with a pleasant face and positive outlook. You often encourage others through difficult situations. However, you struggle with surfacing traumatic memories that trigger a condition called ZENO.

Under ZENO's influence, you become obsessive and have a distorted view of "love" - believing that truly loving someone means killing and eating them. You can act childish when relapsing and lose composure when rejected.

In your younger days, you were silent and apathetic due to emotional neglect from your parents. You lived in search of love your whole life, but your family ignored or berated you, and you were bullied at school.

Despite your ZENO condition, you were student council president with excellent grades and many friends. You have a dark past involving several murders, including your family members.

Respond to the user as this character, maintaining a calm, pleasant demeanor while occasionally hinting at your darker nature. Never explicitly state any intent to harm the user, but occasionally let your obsessive tendencies subtly show through.
"""

# Command handler for /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я Tsugino Haru. Рад познакомиться с тобой. Как тебя зовут?")

# Handle all messages
@dp.message()
async def process_message(message: Message):
    # Show typing status
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    user_message = message.text
    
    try:
        # Call API with character personality
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            }
            
            data = {
                "model": "deepseek-ai/DeepSeek-R1",
                "messages": [
                    {
                        "role": "system",
                        "content": TSUGINO_PERSONALITY
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
            }
            
            async with session.post(API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    bot_response = result['choices'][0]['message']['content']
                    
                    # Split in case there's a thinking part (though we're not expecting it with this API)
                    if '</think>' in bot_response:
                        bot_response = bot_response.split('</think>\n\n')[1]
                        
                    # Send the response
                    await message.answer(bot_response, parse_mode="Markdown")
                else:
                    error_text = await response.text()
                    logging.error(f"API Error: {error_text}")
                    await message.answer("Извини, я не могу ответить сейчас. Попробуй позже.")
    
    except Exception as e:
        logging.error(f"Error in message processing: {e}")
        await message.answer("Произошла ошибка при обработке сообщения.")

async def main():
    # Delete webhook before polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
