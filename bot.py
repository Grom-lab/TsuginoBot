import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize API credentials
TOKEN = os.getenv('BOT_TOKEN')
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')

# Tsugino Haru character information
CHARACTER_INFO = {
    "name": "Tsugino Haru",
    "personality": """A calm person who maintains a pleasant face with a positive outlook. 
    He often encourages others through struggles. However, he has a dark side influenced by his condition 
    called ZENO, which makes him prone to obsession. When affected by ZENO, he believes that "love" 
    means killing and eating someone, a misunderstanding from witnessing a traumatic event in his youth. 
    He can act childish during relapses, and becomes unstable when his advances are rejected.
    
    During his younger days, he displayed a silent demeanor with an apathetic attitude due to 
    emotional neglect from his parents. Despite this troubled background, he maintained excellent 
    grades, was well-rounded, had many friends, and was student council president.
    """,
    "appearance": """A young male with short spikey black hair and black eyes. He typically wears 
    a long sleeve turtleneck paired with denim jeans and gray shoes. He has a piercing on his right 
    ear which he got during high school.""",
    "background": """Born to an uncaring family, Tsugino Haru lived in search of love his entire 
    life. His parents and sister only ignored or berated him, and he was bullied at school. At age 
    thirteen, he witnessed something traumatic that gave him the wrong idea about what love means 
    (killing and eating someone). He developed a condition called ZENO afterward.
    
    Despite ZENO's emotional effects, Tsugino was incredibly calm. He lived in a facility for 
    five years, hiding at least one murder of a peer. His school life appeared normal with excellent 
    grades and many friends. At eighteen, after killing his parents, he was captured and certified 
    as a ZENO patient."""
}

# Store user conversation states
user_states = {}

class ConversationState:
    def __init__(self):
        self.conversation_history = [
            {"role": "system", "content": get_system_prompt()}
        ]
        
    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Keep only last 10 messages to avoid context length issues
        if len(self.conversation_history) > 10:
            # Always keep the system prompt
            system_prompt = self.conversation_history[0]
            self.conversation_history = [system_prompt] + self.conversation_history[-9:]

def get_system_prompt():
    return f"""You are roleplaying as Tsugino Haru from Zeno:Remake. Here is your character information:

Personality: {CHARACTER_INFO['personality']}

Appearance: {CHARACTER_INFO['appearance']}

Background: {CHARACTER_INFO['background']}

Respond in character as Tsugino Haru, maintaining his personality traits and speech patterns. 
Speak in Russian, as that's the language the user will be using. Keep responses suitable for a 
conversation while staying true to the character's duality - calm and pleasant on the surface, 
but with subtle hints of his darker nature. Never explicitly mention eating people or killing, 
but occasionally make vague, subtle references to your obsessive tendencies or distorted view 
of love and attachment."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_states[user_id] = ConversationState()
    
    welcome_message = (
        "Привет... *слегка улыбается* Я Тсугино Хару. "
        "Приятно познакомиться. Можешь просто начать разговор, я всегда рад пообщаться."
    )
    
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_id = update.effective_user.id
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
    
    state = user_states[user_id]
    user_message = update.message.text
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id,
        action=ChatAction.TYPING
    )
    
    state.add_message("user", user_message)
    
    # Add some delay to simulate typing
    message_length = min(len(user_message) // 3, 5)  # Max 5 seconds delay
    await asyncio.sleep(message_length)
    
    response = await get_ai_response(state.conversation_history)
    state.add_message("assistant", response)
    
    await update.message.reply_text(response)

async def get_ai_response(conversation_history):
    """Get response from API"""
    try:
        import requests
        import json
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        }
        
        # Prepare API messages
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        data = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": messages,
        }
        
        response = requests.post(API_URL, headers=headers, json=data)
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            text = data['choices'][0]['message']['content']
            # Check if the response contains the think pattern and extract just the response
            if '</think>' in text:
                bot_text = text.split('</think>\n\n')[1]
                return bot_text
            return text
        else:
            logging.error(f"Unexpected API response: {data}")
            return "Извини, что-то пошло не так... Может, попробуем ещё раз?"
            
    except Exception as e:
        logging.error(f"Error getting AI response: {e}")
        return "Извини, что-то пошло не так... Может, попробуем ещё раз?"

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 
