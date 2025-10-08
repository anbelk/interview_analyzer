import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument, DocumentAttributeVideo
from src.config import BOT_TOKEN, BOT_ID, TG_API_ID, TG_API_HASH
from src.config import DOWNLOADS_DIR
from shared_events import video_events
from loguru import logger

client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)

@client.on(events.NewMessage)
async def handle_forwarded_video(event):
    print("sender_id:", event.sender_id)
    print("is forwarded:", event.fwd_from)
    # проверяем, есть ли медиа
    if not event.media:
        return

    # проверяем, что это пересланное сообщение от нужного бота
    bot_user_id = getattr(getattr(event.fwd_from, 'from_id', None), 'user_id', None)
    if bot_user_id != BOT_ID:
        return

    # проверяем, что это видео
    if not (hasattr(event.media, 'document') and any(isinstance(attr, DocumentAttributeVideo) for attr in event.media.document.attributes)):
        return

    video_id = event.media.document.file_unique_id
    video_path = DOWNLOADS_DIR / f"{video_id}.mp4"

    logger.info("КАЧАЮ видео {video_id}...", video_id=video_id)
    await client.download_media(event.media, file=video_path)
    logger.info("СКАЧАЛОСЬ НА СЕРВЕР {video_id}", video_id=video_id)

    # сигналим обработчику, что видео загружено
    if video_id in video_events:
        video_events[video_id].set()
        del video_events[video_id]

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Telethon запущен как пользователь")
    await client.run_until_disconnected()
