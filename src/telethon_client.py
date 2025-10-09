import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument, DocumentAttributeVideo
from src.config import BOT_TOKEN, BOT_ID, TG_API_ID, TG_API_HASH
from src.config import DOWNLOADS_DIR
from loguru import logger

client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)

from telethon import events
from telethon.tl.types import DocumentAttributeVideo

@client.on(events.NewMessage)
async def handle_forwarded_video(event):
    # Проверяем, что это пересланное ботом сообщение
    bot_user_id = getattr(getattr(event.fwd_from, 'from_id', None), 'user_id', None)
    if bot_user_id != BOT_ID:
        return

    # Проверяем, что это видео
    if not (hasattr(event.media, 'document')
            and any(isinstance(attr, DocumentAttributeVideo)
                    for attr in event.media.document.attributes)):
        return

    video_id = event.media.document.file_unique_id
    video_path = DOWNLOADS_DIR / f"{video_id}.mp4"

    logger.info("КАЧАЮ видео {video_id}...", video_id=video_id)
    await client.download_media(event.media, file=video_path)
    logger.info("СКАЧАЛОСЬ НА СЕРВЕР {video_id}", video_id=video_id)

    # Уведомляем бота, что видео скачано
    await client.send_message(BOT_ID, f"VIDEO_READY:{video_id}")
    logger.info("Сообщил боту, что видео {video_id} готово", video_id=video_id)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Telethon запущен как пользователь")
    await client.run_until_disconnected()
