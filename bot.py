import os
import re
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

# Universal link detector
LINK_PATTERN = re.compile(
    r"("
    r"https?://\S+|"
    r"www\.\S+|"
    r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|"
    r"t\.me/\S+|"
    r"telegram\.me/\S+|"
    r"wa\.me/\S+|"
    r"bit\.ly/\S+|"
    r"tinyurl\.com/\S+|"
    r"@\w+"
    r")",
    re.IGNORECASE,
)

telegram_app = Application.builder().token(BOT_TOKEN).build()

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Anti-Link Bot is working!"
    )

# ================= ANTI LINK =================

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = (
        update.message.text
        or update.message.caption
        or ""
    )

    try:

        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id,
        )

        # Admin/Owner allowed
        if member.status in [
            "creator",
            "administrator",
        ]:
            return

        has_link = False

        # Telegram entities
        entities = []

        if update.message.entities:
            entities.extend(update.message.entities)

        if update.message.caption_entities:
            entities.extend(
                update.message.caption_entities
            )

        for entity in entities:
            if entity.type in [
                "url",
                "text_link",
                "mention",
            ]:
                has_link = True
                break

        # Regex check
        if LINK_PATTERN.search(text):
            has_link = True

        if has_link:
            print(
                "DELETING:",
                update.effective_user.id,
                text,
            )

            await update.message.delete()

            print("DELETED")

    except Exception as e:
        print("ERROR:", e)

# ================= HANDLERS =================

telegram_app.add_handler(
    CommandHandler(
        "start",
        start,
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.ALL,
        anti_link,
    )
)

# ================= FLASK =================

@app.route("/")
def home():
    return "Anti-Link Bot is running!"

@app.route(
    f"/{BOT_TOKEN}",
    methods=["POST"],
)
def webhook():

    update = Update.de_json(
        request.get_json(force=True),
        telegram_app.bot,
    )

    asyncio.run(
        telegram_app.process_update(
            update
        )
    )

    return "OK", 200

# ================= MAIN =================

async def setup():
    await telegram_app.initialize()
    await telegram_app.start()

    webhook_url = (
        f"{RENDER_URL}/{BOT_TOKEN}"
    )

    await telegram_app.bot.set_webhook(
        webhook_url
    )

    print(
        "Webhook:",
        webhook_url,
    )

if __name__ == "__main__":

    asyncio.run(setup())

    port = int(
        os.environ.get(
            "PORT",
            10000,
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )
