import os
import re
import asyncio
import logging
from flask import Flask, request
from telegram import Update, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Logging ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") # ex: https://your-app.onrender.com

app = Flask(__name__)

# Link pattern - domains, t.me, wa.me, @username, urls
LINK_PATTERN = re.compile(
    r"("
    r"https?://\S+|"
    r"www\.\S+|"
    r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|" # domain.com
    r"t\.me/\S+|"
    r"telegram\.me/\S+|"
    r"wa\.me/\S+|"
    r"bit\.ly/\S+|"
    r"tinyurl\.com/\S+|"
    r"@\w+" # telegram username
    r")",
    re.IGNORECASE,
)

telegram_app = Application.builder().token(BOT_TOKEN).build()

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Har message par fresh check karega. Cache mat karna"""
    try:
        member: ChatMember = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
        )
        return member.status in ("creator", "administrator")
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return False # Error aaye to delete kar de safe side

def has_link(update: Update) -> bool:
    """Text, Caption, Entities, Media caption sab check karega"""
    msg = update.message or update.edited_message
    if not msg:
        return False

    text = (msg.text or msg.caption or "")
    
    # 1. Entity check - telegram ka built-in url/text_link
    entities = msg.entities or []
    caption_entities = msg.caption_entities or []
    for entity in entities + caption_entities:
        if entity.type in ("url", "text_link"):
            return True

    # 2. Regex check - normal text mein link
    if LINK_PATTERN.search(text):
        return True
        
    return False

async def delete_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.edited_message
    if not msg:
        return

    # 1. Admin/Owner skip
    if await is_admin(update, context):
        return

    # 2. Link hai kya?
    if has_link(update):
        user_id = msg.from_user.id
        chat_id = msg.chat.id
        logger.info(f"DELETE: User {user_id} in {chat_id} - {msg.text or msg.caption}")
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
        except Exception as e:
            logger.error(f"Delete failed: {e}") # Bot ke pass permission nahi hogi

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Anti-Link Bot is LIVE!\nLinks will be deleted for members. Admins are safe.")

# --- Handlers ---
# 1. Normal message + Photo/Video with caption + Document
telegram_app.add_handler(MessageHandler(
    (filters.TEXT | filters.CAPTION | filters.PHOTO | filters.VIDEO | filters.DOCUMENT | filters.ANIMATION)
    & ~filters.COMMAND, 
    delete_link_handler
))

# 2. Edited message ko bhi pakdo
telegram_app.add_handler(MessageHandler(
    filters.UpdateType.EDITED_MESSAGE,
    delete_link_handler
))

telegram_app.add_handler(CommandHandler("start", start))

# --- Flask Webhook ---
@app.route("/")
def home():
    return "Bot Running"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    # PTB ko async task mein daal do taaki Flask block na ho
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), telegram_app.updater._loop) # type: ignore
    return "OK", 200

async def post_init(application: Application):
    webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
    await application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set: {webhook_url}")

def main():
    telegram_app.post_init = post_init
    telegram_app.run_polling() # Local test ke liye
    # Render par webhook use kar rahe to niche wala use karo
    # asyncio.run(telegram_app.initialize())
    # asyncio.run(telegram_app.start())

if __name__ == "__main__":
    # Render ke liye webhook
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_until_complete(post_init(telegram_app))
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
