import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Render Environment Variable se token lega
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Link detect karne ke liye regex
LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|@\w+)",
    re.IGNORECASE
)

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)

        # Owner/Admin ke messages delete nahi honge
        if member.status in ["creator", "administrator"]:
            return

        # Link detect hua to delete karo
        if LINK_PATTERN.search(update.message.text):
            await update.message.delete()

    except Exception as e:
        print(f"Error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, anti_link)
    )

    print("Anti-Link Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
