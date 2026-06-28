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

BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

# Link detection pattern
LINK_PATTERN = re.compile(
    r"(https?://\S+"
    r"|www\.\S+"
    r"|(?:[a-zA-Z0-9-]+\.)+(?:com|in|org|net|io|me|co|xyz|app|dev|info|biz|tv)"
    r"|t\.me/\S+"
    r"|telegram\.me/\S+"
    r"|wa\.me/\S+"
    r"|bit\.ly/\S+"
    r"|tinyurl\.com/\S+"
    r"|@\w+)",
    re.IGNORECASE,
)

app_telegram = Application.builder().token(BOT_TOKEN).build()


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Anti-Link Bot is working!"
    )


# Anti-link system
async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text or ""

    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )

        # Admin/Owner allowed
        if member.status in ["creator", "administrator"]:
            return

        has_link = False

        # Regex detection
        if LINK_PATTERN.search(text):
            has_link = True

        # Telegram URL entities
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type in ["url", "text_link"]:
                    has_link = True
                    break

        if has_link:
            print("LINK DETECTED:", text)
            await update.message.delete()
            print("MESSAGE DELETED")

    except Exception as e:
        print("ERROR:", e)


# Handlers
app_telegram.add_handler(CommandHandler("start", start))

app_telegram.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        anti_link
    )
)


# Flask routes
@app.route("/")
def home():
    return "Anti-Link Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(
        request.get_json(force=True),
        app_telegram.bot
    )

    asyncio.run(
        app_telegram.process_update(update)
    )

    return "OK", 200


# Main
if __name__ == "__main__":

    async def setup():
        await app_telegram.initialize()
        await app_telegram.start()

        webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"

        await app_telegram.bot.set_webhook(
            webhook_url
        )

        print(
            f"Webhook set: {webhook_url}"
        )

    asyncio.run(setup())

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
