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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Anti-Link Bot is working!"
    )


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

        if member.status in (
            "creator",
            "administrator",
        ):
            return

        has_link = False

        entities = []

        if update.message.entities:
            entities.extend(
                update.message.entities
            )

        if update.message.caption_entities:
            entities.extend(
                update.message.caption_entities
            )

        for entity in entities:
            if entity.type in (
                "url",
                "text_link",
            ):
                has_link = True
                break

        if LINK_PATTERN.search(text):
            has_link = True

        if has_link:
            print(
                "DELETE:",
                update.effective_user.id,
                text,
            )

            await update.message.delete()

    except Exception as e:
        print(
            "ERROR:",
            e,
        )


telegram_app.add_handler(
    CommandHandler(
        "start",
        start,
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT
        & ~filters.COMMAND,
        anti_link,
    )
)


@app.route("/")
def home():
    return "Bot Running"


@app.route(
    f"/{BOT_TOKEN}",
    methods=["POST"],
)
async def webhook():

    data = request.get_json(
        force=True
    )

    update = Update.de_json(
        data,
        telegram_app.bot,
    )

    await telegram_app.process_update(
        update
    )

    return "OK", 200


async def startup():

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

    asyncio.run(
        startup()
    )

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
