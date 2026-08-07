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
    except: return False

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
    if await is_admin(update, context): return
    if has_link(update):
        try: 
            await msg.delete()
            logging.info(f"Deleted link from {msg.from_user.id}")
        except Exception as e: logging.error(f"Delete failed: {e}")

async def post_init(application):
    await application.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("✅ Anti-Link Bot LIVE")))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, delete_handler))
    
    # PTB 22.2 ke liye yehi sahi tareeka hai Render par
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main() # asyncio.run hata diya
