# bot/helper.py

import os

def is_user(user_id):
    # Read the user ID from .env file
    user = os.getenv('USER_ID')
    if user and str(user_id) == user:
        return True
    return False
