import os
import re
import logging
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

LINK_PATTERN = re.compile(r"(https?://\S+|www\.\S+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|t\.me/\S+|@\w+)", re.IGNORECASE)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ("creator", "administrator")
    except: return False

def has_link(update: Update) -> bool:
    msg = update.message or update.edited_message
    if not msg: return False
    text = (msg.text or msg.caption or "")
    entities = (msg.entities or []) + (msg.caption_entities or [])
    if any(e.type in ("url", "text_link") for e in entities): return True
    return bool(LINK_PATTERN.search(text))

async def delete_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.edited_message
    if not msg: return
    if await is_admin(update, context): return
    if has_link(update):
        logger.info(f"DELETE: {msg.from_user.id}")
        try: await msg.delete()
        except Exception as e: logger.error(f"Delete failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Anti-Link Bot PTB v22 LIVE")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler((filters.TEXT | filters.CAPTION | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, delete_link_handler))
    app.add_handler(MessageHandler(filters.UPDATE_TYPE.EDITED_MESSAGE, delete_link_handler))

    await app.bot.set_webhook(f"{RENDER_URL}/{BOT_TOKEN}")
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        secret_token=BOT_TOKEN,
        webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
