import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from src.config import BOT_ID, TG_API_ID, TG_API_HASH, DOWNLOADS_DIR
from loguru import logger

# Инициализируем клиент (как и раньше, от лица вашего аккаунта)
client = TelegramClient("admin_session", TG_API_ID, TG_API_HASH)

def is_video_from_bot(event: events.NewMessage.Event) -> bool:
    """
    Функция-фильтр. Возвращает True, если:
    1. Сообщение является входящим.
    2. Оно переслано от нашего бота (с ID == BOT_ID).
    3. Оно содержит видео (любого типа: сжатое или как документ).
    """
    # 1. Проверяем, что сообщение переслано
    if not event.fwd_from:
        return False
    
    # 2. Проверяем, что оно переслано от нашего бота
    # getattr нужен для безопасного доступа, на случай если from_id будет None
    forwarder_id = getattr(event.fwd_from.from_id, 'user_id', None)
    if forwarder_id != BOT_ID:
        return False
        
    # 3. Проверяем, является ли медиафайл видео
    is_video_message = event.video or (event.document and event.document.mime_type.startswith('video/'))
    
    return is_video_message

# Используем наш мощный фильтр в декораторе
@client.on(events.NewMessage(incoming=True, func=is_video_from_bot))
async def handle_video(event: events.NewMessage.Event):
    """
    Этот хэндлер сработает ТОЛЬКО на пересланные от бота видео.
    """
    try:
        # Получаем медиа-объект и его уникальный ID
        media = event.video or event.document
        video_unique_id = media.file_unique_id
        
        # САМОЕ ГЛАВНОЕ: получаем ID оригинального пользователя из заголовка пересылки
        original_sender = event.fwd_from.from_id
        if not original_sender or not hasattr(original_sender, 'user_id'):
             logger.warning("Не удалось извлечь ID оригинального отправителя из пересланного сообщения.")
             return
        
        original_user_id = original_sender.user_id
        
        logger.info(
            "Обнаружено видео {video_id} от пользователя {user_id}. Начинаю скачивание.",
            video_id=video_unique_id,
            user_id=original_user_id
        )

        # Определяем расширение файла. По умолчанию .mp4
        file_ext = ".mp4"
        if event.document:
            # Пытаемся получить оригинальное имя файла для правильного расширения
            for attr in event.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_ext = Path(attr.file_name).suffix
                    break
        
        video_path = DOWNLOADS_DIR / f"{video_unique_id}{file_ext}"

        # Качаем видео
        await client.download_media(event.message, file=video_path)
        logger.success("Видео {video_id} успешно скачано в {path}", video_id=video_unique_id, path=video_path)

        # Отправляем боту сигнал, что видео готово к обработке
        signal_message = f"VIDEO_READY:{video_unique_id}:{original_user_id}"
        await client.send_message(BOT_ID, signal_message)
        logger.info("Отправлен сигнал боту: {signal}", signal=signal_message)

    except Exception:
        logger.exception("Критическая ошибка в Telethon-хэндлере при обработке видео.")


async def main():
    # При запуске, вы можете отправить боту любое сообщение,
    # чтобы получить его ID, если вы его не знаете
    # await client.start()
    # me = await client.get_me()
    # print(f"Telethon клиент запущен от имени: {me.first_name} (ID: {me.id})")
    # print(f"Бот, с которым мы работаем, должен иметь ID: {BOT_ID}")
    
    print("Telethon клиент запущен. Ожидание видео от бота...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        # Для запуска используем client.loop.run_until_complete(main())
        # или просто client.run_until_disconnected() если start() вызывается внутри main
        client.start()
        client.run_until_disconnected()
