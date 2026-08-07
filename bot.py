import os
import re
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]

LINK_PATTERN = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+|@\w+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})", re.I)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["creator", "administrator"]
    except:
        return False

def has_link(update: Update):
    msg = update.message or update.edited_message
   
