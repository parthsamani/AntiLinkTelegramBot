import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Yahan apna BotFather ka token paste karna
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# Link detect karne ke liye regex
LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|
