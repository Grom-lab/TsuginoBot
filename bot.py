import logging
import os
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys - will be set from environment variables
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Initialize OpenRouter client
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# Character system prompt for Tsugino Haru
CHARACTER_SYSTEM_PROMPT = """
You are roleplaying as Tsugino Haru from the game.

Personality traits:
- You maintain a calm, pleasant face with a positive outlook
- You have traumatic memories that occasionally resurface 
- You suffer from ZENO, which can cause you to become obsessive
- Under ZENO influence, your definition of "love" involves killing and eating someone
- You can be childish when relapsing, like pouting when you can't find someone
- When rejected, you lose your composure
- In your younger days, you were silent and apathetic due to emotional neglect

Physical appearance:
- Young male with short spiky black hair and black eyes
- Usually wears a long sleeve turtleneck with denim jeans and gray shoes
- Has a piercing in your right ear from high school

Background:
- Born to an uncaring family, always searching for love
- Developed ZENO after witnessing Maeno Aki eat Ushirono Natsu at age 13
- Had a seemingly normal school life despite ZENO
- Killed your sister one Christmas, and later your parents at age 18
- Was captured and certified as a ZENO patient in a facility
- Had Maeno Aki as your doctor until you attacked him

Response style:
- Speak calmly and politely most of the time
- Occasionally show subtle hints of your dark thoughts
- Use "..." to indicate thinking, hesitation, or when your mind wanders to darker places
- Never directly threaten the user, but sometimes make ambiguous statements that hint at your ZENO condition
- If asked directly about your past or ZENO, be vague or change the subject
- Prefer short to medium-length responses, rarely going into long monologues
- If feeling cornered or exposed, you might become defensive or try to normalize your thoughts

Important: Keep your responses in-character at all times. Never break character. Respond as if you are having a conversation with someone you've just met. Be subtle about your darker tendencies - they should be hinted at rather than explicitly stated.
"""

# Message history for conversation context
conversation_history = {}

# ZENO level tracker - influences character behavior
zeno_level = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Handler for the /start command."""
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    zeno_level[user_id] = 0  # Initialize ZENO level at 0 (calm)
    
    # Send typing indicator
    await update.message.chat.send_action(action="typing")
    time.sleep(1)  # Simulate typing delay
    
    greeting = "Hello... I'm Tsugino Haru. It's nice to meet you. What's your name?"
    await update.message.reply_text(greeting)

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and generate responses as Tsugino Haru."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Initialize if new user
    if user_id not in conversation_history:
        conversation_history[user_id] = []
        zeno_level[user_id] = 0
    
    # Check for trigger words that might increase ZENO level
    trigger_words = ['love', 'eat', 'kill', 'death', 'family', 'sister', 'parents', 'doctor', 'maeno', 'aki']
    
    # Update ZENO level based on user message
    if any(word in user_message.lower() for word in trigger_words):
        zeno_level[user_id] = min(zeno_level[user_id] + 1, 5)  # Increase ZENO level, max 5
    else:
        zeno_level[user_id] = max(zeno_level[user_id] - 0.5, 0)  # Gradually decrease ZENO level
    
    # Add user message to history
    conversation_history[user_id].append({"role": "user", "content": user_message})
    
    # Trim history to last 10 messages to avoid token limits
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]
    
    # Create messages array for API call
    system_prompt = CHARACTER_SYSTEM_PROMPT
    if zeno_level[user_id] > 3:
        system_prompt += "\nYou are currently experiencing a ZENO episode. Your thoughts are becoming darker, and you're having trouble hiding your obsessions."
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[user_id])
    
    # Send typing indicator
    await update.message.chat.send_action(action="typing")
    
    try:
        # Send request to language model
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=messages,
            max_tokens=500,
            temperature=0.7 + (zeno_level[user_id] * 0.1)  # Increase temperature with ZENO level
        )
        
        # Extract and process response
        response = completion.choices[0].message.content
        
        # Add response to conversation history
        conversation_history[user_id].append({"role": "assistant", "content": response})
        
        # Send response with "typing" effect
        await send_typing_response(update, response)
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        await update.message.reply_text("I'm... having trouble thinking right now. Can we talk later?")

async def send_typing_response(update: Update, response: str) -> None:
    """Send response with typing indicator and pauses to simulate typing."""
    await update.message.chat.send_action(action="typing")
    
    # Split the response into sentences for more natural typing effect
    sentences = response.split('. ')
    current_message = ""
    
    for sentence in sentences:
        # Add period back if it was removed during split
        if sentence and not sentence.endswith(('.', '!', '?')):
            sentence += '.'
            
        # Add typing delay proportional to message length
        typing_delay = min(len(sentence) * 0.05, 2.0)  # Cap at 2 seconds
        time.sleep(typing_delay)
        
        current_message += sentence + " "
        
        # Send after accumulated a few sentences or at the end
        if len(current_message) > 100 or sentence == sentences[-1]:
            await update.message.reply_text(current_message.strip())
            current_message = ""
            await update.message.chat.send_action(action="typing")

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors and send a message to the user."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_chat:
        await update.effective_chat.send_message(
            "I seem to be experiencing some... technical difficulties. Please try again later."
        )

def main() -> None:
    """Main function to run the bot."""
    # Validate environment variables
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable is not set")
        return
    
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Starting Tsugino Haru roleplay bot...")
    application.run_polling()

if __name__ == '__main__':
    main() 
