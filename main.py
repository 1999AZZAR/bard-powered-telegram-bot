import os
import logging
import asyncio
import re
import requests
import telegram
import sys

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from Bard import Chatbot

load_dotenv('/media/azzar/Betha/Download/project/telegram bot/yuna/yuna v1/chat mode/bot/.env')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
MAX_MESSAGE_LENGTH = 2000

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

def is_user(self, user_id):
    allowed_users = os.getenv('USER_ID').split(',')
    return '*' in allowed_users or str(user_id) in allowed_users

async def process_input(update, context):
    user_input = update.message.text
    print(f"Sending message: {user_input}")
    translated_input = translate_input(user_input)  # Translate user input
    user_input = translated_input[0]
    await send_chat_action(update, context, ChatAction.TYPING)
    response = await asyncio.to_thread(bard.process_input, user_input)
    translated_output = translate_output(response, f"{translated_input[1]}")  # Translate response
    send_message(update, context, translated_output)

async def process_input(update, context):
    user_id = update.message.from_user.id
    if is_user(user_id):
        user_input = update.message.text
        print(f"Sending message: {user_input}")
        translated_input = translate_input(user_input)  # Translate user input
        user_input = translated_input[0]
        await send_chat_action(update, context, ChatAction.TYPING)
        response = await asyncio.to_thread(bard.process_input, user_input)
        translated_output = translate_output(response, f"{translated_input[1]}")  # Translate response
        message = translated_output
    else:
        message = 'Sorry, you are not authorized to use this bot.'
    send_message(update, context, message)

async def send_chat_action(update, context, action):
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

def send_message(update, context, message):
    chunks = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]

    for chunk in chunks:
        print(f"Got response: {chunk}")
        chunk = re.sub(r'\bbard\b', 'ayaka mori', chunk, flags=re.IGNORECASE)

        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="MARKDOWN")
        except telegram.error.BadRequest:
            context.bot.send_message(chat_id=update.effective_chat.id, text=chunk)

def start(update, context):
    message = 'Hi! I am Ayaka, your personal AI-powered chatbot. How can I assist you today?'
    send_message(update, context, message)

def help_command(update, context):
    commands = [
        "/start - Start a conversation with the bot.",
        "/help - Display this help message."
    ]
    message = "\n".join(commands)
    send_message(update, context, message)

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
        return user_input, 'en'  # Default to returning the original response if translation fails

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
        return response  # Default to returning the original response if translation fails

if __name__ == "__main__":
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: asyncio.run(process_input(update, context))))

    updater.start_polling()
    logging.info("The bot has started")
    logging.info("The bot is listening for messages")
    updater.idle()
