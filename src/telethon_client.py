import asyncio
from telethon import TelegramClient, events
from src.config import BOT_TOKEN, BOT_ID, TG_API_ID, TG_API_HASH
from src.config import DOWNLOADS_DIR
from shared_events import video_events
from loguru import logger

client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)

@client.on(events.NewMessage)
async def handle_forwarded_video(event):
    if event.sender_id != BOT_ID:
        return

    if event.video:
        video_id = event.video.file_unique_id
        video_path = DOWNLOADS_DIR / f"{video_id}.mp4"
        
        logger.info("КАЧАЮ")
        await client.download_media(event.video, file=video_path)
        logger.info("СКАЧАЛОСЬ НА СЕРВЕР")
    
    if video_id in video_events:
        video_events[video_id].set()
        del video_events[video_id]

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Telethon запущен как пользователь")
    await client.run_until_disconnected()
