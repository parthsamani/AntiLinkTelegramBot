import os
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.environ["RENDER_EXTERNAL_URL"] + "/" + BOT_TOKEN

LINK_PATTERN = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+|@\w+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})", re.I)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["creator", "administrator"]
    except:
        return False

def has_link(update: Update):
    msg = update.message or update.edited_message
    if not msg: return False
    text = msg.text or msg.caption or ""
    ents = (msg.entities or []) + (msg.caption_entities or [])
    if any(e.type in ["url", "text_link"] for e in ents): return True
    return bool(LINK_PATTERN.search(text))

async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.edited_message
    if not msg: return
    if
