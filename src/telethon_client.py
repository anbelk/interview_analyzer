import asyncio
from telethon import TelegramClient, events
from src.config import BOT_TOKEN, BOT_ID, TG_API_ID, TG_API_HASH
from src.config import DOWNLOADS_DIR
from loguru import logger

client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)

@client.on(events.NewMessage)
async def handle_forwarded_video(event):
    if event.sender_id != BOT_ID:
        return

    if event.video:
        video_id = event.video.file_unique_id
        video_path = DOWNLOADS_DIR / f"{video_id}.mp4"
        
        logger.info("Загрузка видео {video_id}...", video_id=video_id)
        await client.download_media(event.video, file=video_path)
        logger.info("Завершена загрузка {video_id}", video_id=video_id)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Telethon запущен как пользователь")
    await client.run_until_disconnected()
