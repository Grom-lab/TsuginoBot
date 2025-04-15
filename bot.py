import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import openrouter
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize OpenRouter client
openrouter.api_key = os.getenv('OPENROUTER_API_KEY')

# Tsugino Haru character information
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

# Store user conversation states
user_states = {}

class ConversationState:
    def __init__(self):
        self.conversation_started = False
        self.conversation_history = []
        
    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Keep only last 10 messages to avoid context length issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_states[user_id] = ConversationState()
    
    welcome_message = (
        "Привет! Я Тсугино Хару. 👋\n\n"
        "Я рада познакомиться с тобой! Хотя у меня есть свои секреты и загадочное прошлое, "
        "я всегда готова поддержать разговор и поделиться своими мыслями.\n\n"
        "Используй /chat, чтобы начать общение со мной!"
    )
    await update.message.reply_text(welcome_message)

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start chat command handler"""
    user_id = update.effective_user.id
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
    
    state = user_states[user_id]
    state.conversation_started = True
    state.conversation_history = []
    
    system_prompt = f"""You are roleplaying as Tsugino Haru from Zeno:Remake. Here is your character information:

Background: {CHARACTER_INFO['background']}

Personality: {CHARACTER_INFO['personality']}

Speech Style: {CHARACTER_INFO['speech_style']}

Respond in character as Tsugino Haru, maintaining her personality traits and speech patterns. 
Speak in Russian, as that's the language the user will be using. Keep responses friendly but with 
hints of your mysterious nature. You can reference your abilities and past experiences vaguely, 
but avoid revealing too much. Show emotional depth while maintaining an optimistic attitude."""
    
    state.add_message("system", system_prompt)
    
    initial_message = (
        "Хм... *улыбается* Знаешь, иногда самые интересные разговоры начинаются совершенно неожиданно. "
        "О чём бы ты хотел поговорить?"
    )
    state.add_message("assistant", initial_message)
    
    await update.message.reply_text(initial_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_id = update.effective_user.id
    if user_id not in user_states or not user_states[user_id].conversation_started:
        await update.message.reply_text("Используй /chat, чтобы начать разговор со мной!")
        return
    
    state = user_states[user_id]
    user_message = update.message.text
    
    state.add_message("user", user_message)
    response = await get_ai_response(state.conversation_history)
    state.add_message("assistant", response)
    
    await update.message.reply_text(response)

async def get_ai_response(conversation_history):
    """Get response from AI using OpenRouter"""
    try:
        completion = await openrouter.chat.async_create(
            messages=conversation_history,
            model="mistralai/mistral-7b-instruct",  # Free model
            max_tokens=300,
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error getting AI response: {e}")
        return "Извини, что-то пошло не так... Может, попробуем ещё раз?"

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chat", start_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 
