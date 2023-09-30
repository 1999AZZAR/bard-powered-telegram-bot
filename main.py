import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import telegram
import sys
import re
from Bard import Chatbot

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')

updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher

MAX_MESSAGE_LENGTH = 4096

def is_user(user_id):
    allowed_users = os.getenv('USER_ID').split(',')
    return str(user_id) in allowed_users

class AnswerBot:
    def __init__(self):
        self.chatbot = self.initialize_chatbot()

    def initialize_chatbot(self):
        try:
            secure_1_psid = os.environ.get("Secure_1PSID")
            secure_1_psidts = os.environ.get("Secure_1PSIDTS")
            return Chatbot(secure_1_psid, secure_1_psidts)
        except Exception as e:
            print(f"ERROR: Cannot initialize chatbot: {e}")
            sys.exit(1)

    def process_input(self, user_input):
        response = self.chatbot.ask(user_input)
        return response["content"]

bard = AnswerBot()

async def process_input(update, context):
    user_id = update.message.from_user.id

    if is_user(user_id):
        user_input = update.message.text
        print(f"Sending message: {user_input}")
        user_input = re.sub(r'\bayaka\b', 'bard', user_input, flags=re.IGNORECASE)
        
        await send_chat_action(update, context, ChatAction.TYPING)
        response = await asyncio.to_thread(bard.process_input, user_input)
        send_message(update, context, response)
    else:
        message = 'Sorry, you are not authorized to use this bot.'
        send_message(update, context, message)

async def send_chat_action(update, context, action):
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

def send_message(update, context, message):
    chunks = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]

    for chunk in chunks:
        print(f"Got response: {chunk}")
        chunk = re.sub(r'\bbard\b', 'Ayaka Mori', chunk, flags=re.IGNORECASE)

        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="MARKDOWN")
        except telegram.error.BadRequest:
            context.bot.send_message(chat_id=update.effective_chat.id, text=chunk)

def start(update, context):
    message = 'Hi! I am Ayaka, your personal AI-powered chatbot. How can I assist you today?'
    send_message(update, context, message)

def reset_chat(update, context):
    bard = AnswerBot()
    message = 'Chat history has been reset.'
    send_message(update, context, message)

dispatcher.add_handler(CommandHandler("reset", reset_chat))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: asyncio.run(process_input(update, context))))

updater.start_polling()
logging.info("The bot has started")
logging.info("The bot is listening for messages")
updater.idle()
