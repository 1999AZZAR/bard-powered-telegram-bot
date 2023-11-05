import os
import logging
import asyncio
import telegram
import requests
import sys
import re

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from Bard import Chatbot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Get the Telegram bot token from the environment
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')

# Create an Updater with context
updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher

# Define the maximum message length
MAX_MESSAGE_LENGTH = 4096

# Class for the AnswerBot
class AnswerBot:
    def __init__(self):
        self.chatbot = self.initialize_chatbot()

    def initialize_chatbot(self):
        try:
            secure_1_psid = os.environ.get("Secure_1PSID")
            secure_1_psidts = os.environ.get("Secure_1PSIDTS")
            return Chatbot(secure_1_psid, secure_1_psidts)
        except Exception as e:
            logging.error(f"ERROR: Cannot initialize chatbot: {e}")
            sys.exit(1)

    def process_input(self, user_input):
        response = self.chatbot.ask(user_input)
        return response["content"]

bard = AnswerBot()

# Function to check if a user is authorized
def is_user(user_id):
    allowed_users = os.getenv('USER_ID').split(',')
    return '*' in allowed_users or str(user_id) in allowed_users

# Function to process user input
async def process_input(update, context):
    user_id = update.message.from_user.id
    user_input = update.message.text
    await send_chat_action(update, context, ChatAction.TYPING)
    
    if is_user(user_id):
        translated_input = translate_input(user_input)
        user_input = translated_input[0]
        logging.info(f"Sending input: {user_input}")
        response = await asyncio.to_thread(bard.process_input, user_input)
        response = translate_output(response, f"{translated_input[1]}")
    else:
        response = 'Sorry, you are not authorized to use this bot.'
    
    send_message(update, context, response)

# Function to send a chat action
async def send_chat_action(update, context, action):
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

# Function to send a message, split into chunks if too long
def send_message(update, context, message):
    message = re.sub(r'\bbard\b', 'Ayaka Mori', message, flags=re.IGNORECASE)
    chunks = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
    
    for chunk in chunks:
        logging.info(f"Sending response: {chunk}")
        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="MARKDOWN")
        except telegram.error.BadRequest:
            context.bot.send_message(chat_id=update.effective_chat.id, text=chunk)

# Function to translate user input to english
def translate_input(user_input):
    url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=en&q={user_input}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }

    try:
        request_result = requests.get(url, headers=headers).json()
        translation = request_result[0][0]
        user_lang = request_result[0][1]
        return translation, user_lang
    except:
        return user_input, 'en'  

# Function to translate bard output to the language of the user
def translate_output(response, user_lang):
    response = re.sub(r"\bI am a large language model\b", "I am ayaka mori", response, flags=re.IGNORECASE)
    url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl={user_lang}&q={response}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }

    try:
        request_result = requests.get(url, headers=headers).json()
        translation = request_result[0]
        return translation
    except:
        return response  

# Function to handle the /start command
def start(update, context):
    message = 'Hi! my name is Ayaka Mori, your personal AI-powered chatbot. How can I assist you today?'
    send_message(update, context, message)

# Add command and message handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: asyncio.run(process_input(update, context))))

# Start the Updater
updater.start_polling()
logging.info("The bot has started")
logging.info("The bot is listening for messages")
updater.idle()
