import os
import re
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|@\w+)",
    re.IGNORECASE
)

app = Flask(__name__)

@app.route("/")
def home():
    return "Anti-Link Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Anti-Link Bot is working!")

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )

        # Admin aur Owner ko allow karo
        if member.status in ["administrator", "creator"]:
            return

        # Link detect hua to delete karo
        if LINK_PATTERN.search(update.message.text):
            await update.message.delete()
            print(f"Deleted link from {update.effective_user.id}")

    except Exception as e:
        print(e)

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            anti_link
        )
    )

    print("Anti-Link Bot Started...")
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
