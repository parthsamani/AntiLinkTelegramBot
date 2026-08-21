import asyncio
import logging
import os
import re
import threading

from flask import Flask
from telegram import Update, MessageEntity
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN environment variable is missing"
    )


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("RemoveHyperlinkBot")


# ==========================================================
# FLASK SERVER FOR RENDER
# ==========================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Remove Hyperlink Bot is running!"


@web_app.route("/health")
def health():
    return "OK", 200


def run_web_server():

    port = int(
        os.environ.get("PORT", "10000")
    )

    web_app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ==========================================================
# URL DETECTION
# ==========================================================

URL_PATTERN = re.compile(
    r"(?i)"
    r"("
    r"(?:https?://|ftp://|www\.)"
    r"[^\s<>()]+"
    r"|"
    r"(?:[a-z0-9-]+\.)+"
    r"(?:com|net|org|in|io|co|me|info|biz|xyz|site|online|app|dev|ai|"
    r"co\.in|org\.in|net\.in|t\.me)"
    r"(?:/[^\s<>()]*)?"
    r")"
)


def has_url(text: str) -> bool:

    if not text:
        return False

    return bool(URL_PATTERN.search(text))


def has_url_entity(
    message_text: str,
    entities
) -> bool:

    if not message_text or not entities:
        return False

    for entity in entities:

        if entity.type in (
            MessageEntity.URL,
            MessageEntity.TEXT_LINK
        ):
            return True

    return False


def message_contains_hyperlink(
    message
) -> bool:

    # Normal text
    if message.text:

        if has_url(message.text):
            return True

        if has_url_entity(
            message.text,
            message.entities
        ):
            return True

    # Media captions
    if message.caption:

        if has_url(message.caption):
            return True

        if has_url_entity(
            message.caption,
            message.caption_entities
        ):
            return True

    return False


# ==========================================================
# ADMIN CHECK
# ==========================================================

async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> bool:

    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return False

    # Private chat
    if chat.type == "private":
        return True

    try:

        member = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=user.id
        )

        return member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR
        )

    except TelegramError as error:

        logger.warning(
            "Admin check error: %s",
            error
        )

        return False


# ==========================================================
# DELETE HYPERLINK MESSAGE
# ==========================================================

async def remove_hyperlink(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.effective_message

    if not message:
        return

    # Only groups and supergroups
    if message.chat.type not in (
        "group",
        "supergroup"
    ):
        return

    # Ignore bot messages
    if message.from_user and message.from_user.is_bot:
        return

    # Admin messages are exempted
    if await is_admin(update, context):
        return

    # Check hyperlink
    if not message_contains_hyperlink(message):
        return

    try:

        await message.delete()

        username = (
            message.from_user.username
            if message.from_user
            else "unknown"
        )

        logger.info(
            "Deleted hyperlink message | "
            "Chat: %s | User: %s",
            message.chat.id,
            username
        )

    except Forbidden:

        logger.error(
            "Cannot delete message. "
            "Make the bot an admin and enable "
            "'Delete Messages' permission."
        )

    except BadRequest as error:

        logger.error(
            "Telegram delete error: %s",
            error
        )

    except TelegramError as error:

        logger.error(
            "Unexpected Telegram error: %s",
            error
        )


# ==========================================================
# /START COMMAND
# ==========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🔗 <b>Remove Hyperlink Bot</b>\n\n"
        "This bot automatically removes messages "
        "containing website URLs from groups.\n\n"
        "✅ Admin messages are exempted\n"
        "🔒 Regular members' URL messages are removed\n\n"
        "<b>Setup:</b>\n"
        "1. Add the bot to your group\n"
        "2. Promote it as Admin\n"
        "3. Enable <b>Delete Messages</b>\n"
        "4. Done!"
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML"
    )


# ==========================================================
# /HELP COMMAND
# ==========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🔗 <b>Remove Hyperlink Bot</b>\n\n"
        "The bot automatically deletes:\n"
        "• Website URLs\n"
        "• www links\n"
        "• Hidden hyperlinks\n"
        "• URLs in captions\n"
        "• Edited messages containing links\n\n"
        "👑 Messages sent by group admins "
        "are not deleted."
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML"
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    # Fix for Python 3.14 event loop behavior
    try:

        asyncio.get_event_loop()

    except RuntimeError:

        asyncio.set_event_loop(
            asyncio.new_event_loop()
        )

    # Start Render web server
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    logger.info(
        "Render web server started"
    )

    # Create Telegram application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    # New messages
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            remove_hyperlink
        )
    )

    # Edited messages
    app.add_handler(
        MessageHandler(
            filters.UpdateType.EDITED_MESSAGE,
            remove_hyperlink
        )
    )

    logger.info(
        "Remove Hyperlink Bot Started Successfully"
    )

    # Run Telegram bot
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False
    )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":
    main()
