import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))

app = ApplicationBuilder().token(BOT_TOKEN).build()

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id):
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if member.status in ["creator", "administrator"]: return
    
    msg = update.message or update.edited_message
    if msg and re.search(r"(http|www|t\.me|@)", msg.text or msg.caption or ""):
        await msg.delete()

app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, delete))
app.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=os.environ["RENDER_EXTERNAL_URL"]+"/"+BOT_TOKEN)
