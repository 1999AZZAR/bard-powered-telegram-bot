# bot/main.py

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import asyncio

from helper import is_user
from bard import Bard

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher

MAX_MESSAGE_LENGTH = 3000
bard = Bard()

async def process_input(update, context):
    """Process user input and send it to Bard for generating a response."""
    user_id = update.message.from_user.id
    if is_user(user_id):
        user_input = update.message.text
        await send_chat_action(update, context, ChatAction.TYPING)  # Send "typing..." status
        response = await asyncio.to_thread(bard.process_input, user_input)  # Run process_input in a separate thread
        send_message(update, context, response)
    else:
        message = 'Sorry, you are not authorized to use this bot.'
        send_message(update, context, message)

async def send_chat_action(update, context, action):
    """Send a chat action to indicate the bot's status."""
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

def send_message(update, context, message):
    chunks = [message[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
    for chunk in chunks:
        context.bot.send_message(chat_id=update.effective_chat.id, text=chunk)

def start(update, context):
    """Send a message when the command /start is issued."""
    message = 'Hi! I am your chatbot. How can I assist you today?'
    send_message(update, context, message)

def reset_chat(update, context):
    """Reset the chat history."""
    # Clear the chat history or perform any necessary reset operations
    # Here, we can simply reinitialize the Bard instance
    bard = Bard()
    message = 'Chat history has been reset.'
    send_message(update, context, message)

dispatcher.add_handler(CommandHandler("reset", reset_chat))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: asyncio.run(process_input(update, context))))

updater.start_polling()

logging.info("The bot has started")
logging.info("The bot is listening for messages")

updater.idle()
