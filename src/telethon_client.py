import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
from src.config import BOT_ID, TG_API_ID, TG_API_HASH, DOWNLOADS_DIR
from src.config import BOT_TOKEN
from loguru import logger

# 👇 Telethon клиент работает от лица администратора (твоего аккаунта)
client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)


@client.on(events.NewMessage)
async def handle_forwarded_video(event):
    """
    Этот хэндлер срабатывает, когда твой пользовательский аккаунт
    получает пересланное ботом видео от реального пользователя.
    """

    # Проверяем, что это пересланное сообщение от бота
    if not event.fwd_from or not getattr(event.fwd_from, "from_id", None):
        return

    bot_user_id = getattr(event.fwd_from.from_id, "user_id", None)
    if bot_user_id != BOT_ID:
        return

    # Проверяем, что это видео
    if not (
        hasattr(event.media, "document")
        and any(isinstance(attr, DocumentAttributeVideo)
                for attr in event.media.document.attributes)
    ):
        return

    video_id = event.media.document.file_unique_id
    video_path = DOWNLOADS_DIR / f"{video_id}.mp4"

    # Попробуем извлечь user_id из подписи, если бот добавил его
    caption = (event.message.message or "").strip()
    user_id = None

    if caption.startswith("USER:"):
        try:
            user_id = int(caption.split(":")[1])
        except Exception:
            pass

    logger.info("КАЧАЮ видео {video_id}...", video_id=video_id)
    await client.download_media(event.media, file=video_path)
    logger.info("СКАЧАЛОСЬ НА СЕРВЕР {video_id}", video_id=video_id)

    # Если удалось определить user_id — сообщаем боту
    if user_id:
        await client.send_message(BOT_ID, f"VIDEO_READY:{video_id}:{user_id}")
        logger.info("Сообщил боту, что видео {video_id} готово (user_id={user_id})",
                    video_id=video_id, user_id=user_id)
    else:
        logger.warning("Не удалось определить user_id для видео {video_id}", video_id=video_id)


async def main():
    print("Telethon запущен как пользователь (админский клиент)")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()