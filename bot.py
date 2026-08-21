import os, re, logging, asyncio
from flask import Flask, request
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render khud dega
if not BOT_TOKEN: raise ValueError("BOT_TOKEN missing")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ParthBot")

URL_PATTERN = re.compile(r"(?i)((?:https?://|www\.)[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+)")

flask_app = Flask(__name__)
app = Application.builder().token(BOT_TOKEN).build()

async def is_admin(update, context):
    try:
        m = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return m.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except: return False

async def delete_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or msg.chat.type not in ("group","supergroup"): return
    if msg.from_user and msg.from_user.is_bot: return
    if await is_admin(update, context): return
    
    text = (msg.text or msg.caption or "")
    if URL_PATTERN.search(text) or (msg.entities and any(e.type in ("url","text_link") for e in msg.entities)):
        try:
            await msg.delete()
            logger.info(f"Deleted link from {msg.from_user.id}")
        except Exception as e:
            logger.error(f"Delete failed - Make bot admin: {e}")

app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, delete_link))

@flask_app.route("/")
def home(): return "Bot is Running 24x7!"

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await app.process_update(update)
    return "OK"

async def setup():
    await app.initialize()
    await app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    await app.start()
    logger.info(f"Webhook set to {WEBHOOK_URL}")

# Render ke liye
setup_done = False
@flask_app.before_request
def before():
    global setup_done
    if not setup_done:
        asyncio.run(setup())
        setup_done = True

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
