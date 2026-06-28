import os
import re
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
    r"

telegram_app = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Anti-Link Bot is working!"
    )


async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    try:
        print(
    f"Message: {update.message.text} | User: {update.effective_user.id}"
)
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id,
        )

        # Owner/Admin ko allow karo
        if member.status in ["creator", "administrator"]:
            return

        # Link detect hua to delete karo
        text = update.message.text or ""

# Telegram entities check karo
has_link = False

if update.message.entities:
    for entity in update.message.entities:
        if entity.type in [
            "url",
            "text_link",
            "mention",
            "phone_number"
        ]:
            has_link = True
            break

# Regex check
if LINK_PATTERN.search(text):
    has_link = True

if has_link:
    print("LINK DETECTED:", text)
    await update.message.delete()
    print("MESSAGE DELETED")
            print("LINK DETECTED")
            await update.message.delete()
            print("MESSAGE DELETED")

    except Exception as e:
        print("ERROR:", e)


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, anti_link)
)


@app.route("/")
def home():
    return "Anti-Link Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    import asyncio

    update = Update.de_json(
        request.get_json(force=True),
        telegram_app.bot
    )

    asyncio.run(
        telegram_app.process_update(update)
    )

    return "OK", 200


import asyncio

if __name__ == "__main__":
    async def setup():
        await telegram_app.initialize()
        await telegram_app.start()

        webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
        await telegram_app.bot.set_webhook(webhook_url)

        print(f"Webhook set: {webhook_url}")

    asyncio.run(setup())

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
