import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Link detect karne ke liye regex
LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|
