import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Yahan apna BotFather ka token paste karna
BOT_TOKEN = "8876100729:AAFclBFxBE8QgclXgWwM5VDCcJwy_w65dYM"

# Link detect karne ke liye regex
LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|
