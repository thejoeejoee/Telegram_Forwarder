import asyncio
from collections import defaultdict
from typing import Union, Optional

from telegram import Update, Message, MessageId
from telegram.error import ChatMigrated, RetryAfter
from telegram import Update, Message, MessageId, InputMediaPhoto, PhotoSize

from telegram.error import ChatMigrated
from telegram.ext import MessageHandler, filters, ContextTypes

from forwarder import bot, REMOVE_TAG, LOGGER
from forwarder.utils import get_source, get_destenation


SENT_GROUPS = set()

def get_biggest(photos: tuple[PhotoSize, ...]) -> tuple[PhotoSize, ...]:
    by_ids = defaultdict(list)
    for p in photos:
        by_ids[p.file_unique_id].append(p)

    return tuple((
        max(sizes, key=lambda p: p.height*p.width) for unique_id, sizes in by_ids.items()
    ))

async def send_message(
        message: Message, chat_id: int, thread_id: Optional[int] = None
):
    if message.media_group_id:
        LOGGER.info("Sending media group %s: %s", message.media_group_id, message.photo)

        if message.media_group_id in SENT_GROUPS:
            LOGGER.info("Media group %s already sent, skipping", message.media_group_id)
            return

        SENT_GROUPS.add(message.media_group_id)
        return await bot.bot.send_media_group(
            chat_id=chat_id,
            media=list(filter(None, [
                *([
                      InputMediaPhoto(
                          p,
                          # caption=message.caption if i == 0 else None
                      ) for i, p in enumerate(get_biggest(message.photo))
                  ] or ()),
                message.video,
                message.document,
                message.animation,
                message.audio,
            ])),
            caption=message.caption,
            message_thread_id=thread_id,
        )

    if REMOVE_TAG:
        return await message.copy(
            chat_id,
            message_thread_id=thread_id,
        )  # type: ignore

    return await message.forward(chat_id, message_thread_id=thread_id)  # type: ignore


async def forwarder(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    source = update.effective_chat

    if not message or not source:
        return

    for chat in get_destenation(message.chat_id, message.message_thread_id):
        try:
            await send_message(message, chat["chat_id"], thread_id=chat["thread_id"])
        except RetryAfter as err:
            LOGGER.warning(f"Rate limited, retrying in {err.retry_after} seconds")
            await asyncio.sleep(err.retry_after + 0.2)
            await send_message(message, chat["chat_id"], thread_id=chat["thread_id"])
        except ChatMigrated as err:
            await send_message(message, err.new_chat_id)
            LOGGER.warning(
                f"Chat {chat} has been migrated to {err.new_chat_id}!! Edit the config file!!"
            )
        except Exception as err:
            LOGGER.exception(f"Failed to forward message from {source.id} to {chat} due to {err}")


FORWARD_HANDLER = MessageHandler(
    filters.Chat([source["chat_id"] for source in get_source()])
    & ~filters.COMMAND
    & ~filters.StatusUpdate.ALL,
    forwarder,
)
bot.add_handler(FORWARD_HANDLER)
