import os
import re
import logging
from telegram import Update, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") # https://your-app.onrender.com

LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|t\.me/\S+|telegram\.me/\S+|wa\.me/\S+|bit\.ly/\S+|tinyurl\.com/\S+|@\w+)",
    re.IGNORECASE,
)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member: ChatMember = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
        )
        return member.status in ("creator", "administrator")
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return False

def has_link(update: Update) -> bool:
    msg = update.message or update.edited_message
    if not msg: return False
    text = (msg.text or msg.caption or "")
    
    entities = (msg.entities or []) + (msg.caption_entities or [])
    for entity in entities:
        if entity.type in ("url", "text_link"):
            return True
    if LINK_PATTERN.search(text):
        return True
    return False

async def delete_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.edited_message
    if not msg: return

    if await is_admin(update, context): return

    if has_link(update):
        logger.info(f"DELETE: {msg.from_user.id} - {msg.text or msg.caption}")
        try:
            await msg.delete() # direct delete
        except Exception as e:
            logger.error(f"Delete failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Anti-Link Bot is LIVE!\nAdmins can send links. Members cannot.")

async def post_init(app: Application):
    webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
    await app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.CAPTION | filters.PHOTO | filters.VIDEO | filters.DOCUMENT | filters.ANIMATION)
        & ~filters.COMMAND, 
        delete_link_handler
    ))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, delete_link_handler))

    # Render ke liye ye best hai
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
