import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
from src.config import BOT_TOKEN, BOT_ID, TG_API_ID, TG_API_HASH, DOWNLOADS_DIR
from src.handlers import process_large_video
from aiogram import Bot
from loguru import logger

client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)

def is_video_from_bot(event: events.NewMessage.Event) -> bool:
    if event.sender_id != BOT_ID:
        return False
    return bool(event.video)

@client.on(events.NewMessage(incoming=True, func=is_video_from_bot))
async def handle_video(event: events.NewMessage.Event):
    try:
        caption = getattr(event.message, 'message', '') or ''
        user_id_str, video_id = caption.split()
        user_id = int(user_id_str)
        
        target_path = DOWNLOADS_DIR / f"{video_id}.mp4"

        logger.info("[TELETHON] Получено видео {video_id} от пользователя {user_id}", video_id=video_id, user_id=user_id)

        logger.info("[TELETHON] [{video_id}] Скачивание видео...", video_id=video_id)
        downloaded_path_str = await client.download_media(event.message, file=str(target_path))
        downloaded_path = Path(downloaded_path_str)

        logger.success("[TELETHON] [{video_id}] Видео скачано: {path}", video_id=video_id, path=downloaded_path)
        
        bot = Bot(token=BOT_TOKEN)
        await process_large_video(video_id, user_id, bot)

    except Exception:
        logger.exception("[TELETHON] Ошибка при обработке видео")

async def main():
    await client.start()    
    logger.info("[TELETHON] Клиент запущен, ожидание видео...")
    await client.run_until_disconnected()
