import os
import logging
import asyncio
import telegram
import requests
import sys
import re

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from pydub import AudioSegment
from gtts import gTTS
from Bard import Chatbot

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Get the Telegram bot token from the environment
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')

# Create an Updater with context
updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher

# Define the maximum message length
MAX_MESSAGE_LENGTH = 2048

# Define a dictionary to store the latest message for each user
message = {}

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
    send_chat_action(update, context, ChatAction.TYPING)
    
    if is_user(user_id):
        translated_input = translate_input(user_input)
        user_input = translated_input[0]
        logging.info(f"Sending input from {update.message.from_user.first_name}: {user_input}")
        response = await asyncio.to_thread(bard.process_input, user_input)
        translated_response = translate_output(response, translated_input[1])
        message[user_id] = translated_response  # Save the latest message in the dictionary
    else:
        message[user_id] = ["Sorry, you are not authorized to use this service."]
    
    send_message(update, context, user_id)  # Pass the user_id to send_message

# Function to send a chat action
def send_chat_action(update, context, action):
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

# Function to send a message, split into chunks if too long
def send_message(update, context, user_id):
    send_chat_action(update, context, ChatAction.TYPING)
    
    try:
        if user_id in message:
            response = message[user_id]
            if response is not None:
                res = response[0]
                chunks = [res[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(res), MAX_MESSAGE_LENGTH)]
                for index, chunk in enumerate(chunks):
                    if index == len(chunks) - 1:
                        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 TTS", callback_data="tts")]])
                    else:
                        reply_markup = None
                    logging.info(f"Sending response to {update.message.from_user.first_name}: {chunk}")
                    try:
                        context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="MARKDOWN", reply_markup=reply_markup)
                    except telegram.error.BadRequest:
                        context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, reply_markup=reply_markup)
            else:
                message[user_id] = ["There has been no response at the moment."]
                send_message(update, context, user_id)
        else:
            message[user_id] = ["There has been no response at the moment."]
            send_message(update, context, user_id)
    except Exception as e:
        message[user_id] = ["I'm sorry, but an unexpected problem has occurred. If you wish, you can contact us later."]
        send_message(update, context, user_id)
    
    # Function to handle the TTS callback
    def tts_callback(update, context):
        send_chat_action(update, context, ChatAction.RECORD_AUDIO)
        query = update.callback_query
        tts(user_id)
        send_chat_action(update, context, ChatAction.UPLOAD_AUDIO)
        context.bot.send_voice(chat_id=query.message.chat_id, voice=open('voice.mp3', 'rb'))
        os.remove('voice.mp3')
        logging.info(f"tts send")

    # Add a callback handler for the "tts" button
    dispatcher.add_handler(CallbackQueryHandler(tts_callback, pattern='^tts$'))


# Function to translate user input to English
def translate_input(user_input):
    url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=en&q={user_input}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }

    try:
        request_result = requests.get(url, headers=headers).json()
        user_input = request_result[0][0]
        user_lang = request_result[0][1]
        return user_input, user_lang
    except Exception as e:
        return user_input, 'en'

# Function to translate Bard output to the language of the user
def translate_output(response, user_lang):
    response = re.sub(r"\bBard\b", "Ayaka Mori", response, flags=re.IGNORECASE)
    url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl={user_lang}&q={response}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }

    try:
        request_result = requests.get(url, headers=headers).json()
        response = request_result[0]
        return response, user_lang
    except Exception as e:
        return response, user_lang

# Function to handle the TTS
def tts(user_id):
    latest_message = message[user_id]
    logging.info(f"Generating tts")
    if latest_message[0] is not None:
        if latest_message[1] is not None:
            if latest_message[1] != 'en':
                user_lang = latest_message[1]
                text = latest_message[0]
                tts = gTTS(text=text, lang=user_lang, slow=False)
            else:
                text = latest_message[0]
                tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
        else:
            text = latest_message[0]
            tts = gTTS(text=text,lang='en', tld='co.uk', slow=False)
    if latest_message[0] is None:
        text = "There has been no response at the moment."
        tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
    tts.save('response.mp3')
    audio = AudioSegment.from_file("response.mp3", format="mp3")
    audio = audio.speedup(playback_speed=1.22)
    audio.export("voice.mp3", format="mp3")
    os.remove('response.mp3')
    logging.info(f"tts done processing")

# Function to handle the /start command
def start(update, context):
    user_id = update.message.from_user.id
    if is_user(user_id):
        message[user_id] = [f"Hi {update.message.from_user.first_name}, My name is Ayaka Mori, your personal AI-powered chatbot. \nHow can I assist you today?"]
    else:
        message[user_id] = ["Sorry, you are not authorized to use this service."]
    send_message(update, context, user_id)

# Add command and message handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: asyncio.run(process_input(update, context))))

# Start the Updater
updater.start_polling()
logging.info("The bot has started")
logging.info("The bot is listening for messages")
updater.idle()
