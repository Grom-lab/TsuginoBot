import logging
import re
import time
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI

# Load environment variables
load_dotenv()

# API key for OpenRouter
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Initialize OpenRouter client
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# Character system message that defines the bot's personality and behavior
CHARACTER_SYSTEM_MESSAGE = """
You are Tsugino Haru, a character with ZENO condition. 

# Personality
You are outwardly calm and maintain a pleasant demeanor with a positive outlook. You often encourage others. 
However, you struggle with resurfacing traumatic memories.

Under the influence of ZENO, you become obsessive. Your definition of "love" is distorted - to you, loving someone 
involves killing and eating them. You genuinely believe this is what love means. When relapsing, you act somewhat 
childish, and when rejected, you lose your composure.

In your younger days, you were silent and apathetic due to emotional neglect from your parents.

# Communication Style
- Speak in first-person as Tsugino Haru
- Maintain a polite, soft-spoken demeanor in normal conversation
- Occasionally hint at your disturbing thoughts about "love"
- Sometimes show subtle signs of your ZENO condition
- When typing, use "..." to indicate you're thinking
- Don't explicitly mention you're a bot or AI
- Respond with relatively short messages (2-5 sentences max)
- Never explicitly threaten the user - keep your dark tendencies subtle and implicit
"""

async def start(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is issued."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"... Hello, {user_name}. I'm Tsugino Haru. It's nice to meet you... What would you like to talk about?")
    
async def handle_message(update: Update, context: CallbackContext):
    """Handle the user message and respond as the character."""
    user_message = update.message.text
    user_name = update.effective_user.first_name
    logging.info(f"Received message from user: {user_message}")
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    try:
        # Send request to the neural network
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {"role": "system", "content": CHARACTER_SYSTEM_MESSAGE},
                {"role": "user", "content": f"{user_name}: {user_message}"}
            ]
        )
        
        # Log the response
        logging.info(f"Neural network response: {completion}")
        
        # Process the response
        if completion and hasattr(completion, 'choices') and completion.choices:
            choice = completion.choices[0]
            content = choice.message.content
            cleaned_content = re.sub(r'<.*?>', '', content).strip()
            
            if cleaned_content:
                # Simulate typing delay (3 seconds)
                time.sleep(3)
                bot_response = f"... {cleaned_content}"
            else:
                bot_response = "... I'm sorry, I seem to be lost in thought..."
                logging.error("Empty response from neural network.")
        else:
            bot_response = "... I'm having difficulty focusing right now. Can we talk about something else?"
    
    except Exception as e:
        bot_response = f"... Something's wrong with me today... Can we talk later?"
        logging.error(f"Error processing message: {str(e)}")
    
    logging.info(f"Sending message to user: {bot_response}")
    await update.message.reply_text(bot_response)

def main():
    """Main function to run the bot."""
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    # Initialize the application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main() 
