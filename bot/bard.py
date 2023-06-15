# bot/bard.py

import os
import sys
from Bard import Chatbot

class Bard:
    def __init__(self):
        self.chatbot = self.initialize_chatbot()

    def initialize_chatbot(self):
        try:
            BARD_TOKEN = os.environ.get('BARD_TOKEN')
            return Chatbot(BARD_TOKEN)
        except Exception as e:
            print(f"ERROR: Cannot initialize chatbot: {e}")
            sys.exit(1)

    def process_input(self, user_input):
        # Process user input and generate a response from the chatbot
        response = self.chatbot.ask(user_input)
        return response["content"]
