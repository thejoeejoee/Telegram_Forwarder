from typing import Union, Optional

from telegram import Update, Message, MessageId
from telegram.error import ChatMigrated
from telegram.ext import MessageHandler, filters, ContextTypes

from forwarder import CONFIG, bot, REMOVE_TAG, LOGGER
from forwarder.utils import get_source, get_destenation


async def join_hider(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    m = update.effective_message

    await m.delete()

JOIN_HIDE_HANDLER = MessageHandler(
    filters.Chat([d for source in CONFIG for d in source["destination"] ])
    & ~filters.COMMAND
    & filters.StatusUpdate.NEW_CHAT_MEMBERS,
    join_hider,
)
bot.add_handler(JOIN_HIDE_HANDLER)
