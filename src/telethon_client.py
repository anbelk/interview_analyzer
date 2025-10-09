import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
from src.config import BOT_ID, TG_API_ID, TG_API_HASH, DOWNLOADS_DIR
from loguru import logger

# Безопасное приведение типов для ID, полученных из .env
BOT_ID_INT = int(BOT_ID) if BOT_ID is not None else None
TG_API_ID_INT = int(TG_API_ID) if TG_API_ID is not None else None

# Инициализируем клиент (как и раньше, от лица вашего аккаунта)
client = TelegramClient("admin_session", TG_API_ID_INT, TG_API_HASH)

def is_video_from_bot(event: events.NewMessage.Event) -> bool:
    """
    Возвращает True для входящих сообщений от бота с видео. Теперь мы не полагаемся на fwd_from,
    так как видео отправляется как копия с подписью USER:<id>.
    """
    if BOT_ID_INT is None:
        logger.warning("BOT_ID не задан, фильтр Telethon пропускает событие")
        return False
    if event.sender_id != BOT_ID_INT:
        return False
    is_video_message = bool(event.video) or (
        bool(event.document) and getattr(event.document, 'mime_type', '') and event.document.mime_type.startswith('video/')
    )
    return is_video_message

# Используем наш мощный фильтр в декораторе
@client.on(events.NewMessage(incoming=True, func=is_video_from_bot))
async def handle_video(event: events.NewMessage.Event):
    """
    Срабатывает на входящее видео, которое переслал наш бот админу.
    Скачивает файл и отправляет боту сигнал вида:
    VIDEO_READY:<basename>:<original_user_id>
    """
    try:
        media = event.video or event.document

        # Достаём user_id из подписи вида "USER:<id>"
        caption = getattr(event.message, 'message', '') or ''
        original_user_id = None
        if isinstance(caption, str) and caption.startswith('USER:'):
            try:
                original_user_id = int(caption.split(':', 1)[1])
            except Exception:
                original_user_id = None
        if not original_user_id:
            logger.warning("Не удалось извлечь user_id из подписи, пропускаю сообщение")
            return

        # Пытаемся извлечь имя файла и расширение, чтобы сохранить корректно
        file_name = None
        file_ext = ".mp4"
        if event.document:
            try:
                for attr in event.document.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name:
                        file_name = attr.file_name
                        break
            except Exception:
                file_name = None
            if getattr(event.document, 'mime_type', '') and not file_name:
                if not event.document.mime_type.startswith('video/'):
                    logger.warning("Получен document без video mime_type, пропускаю")
                    return
        if file_name:
            file_ext = Path(file_name).suffix or ".mp4"

        # Скачиваем в директорию загрузок; Telethon вернёт фактический путь
        downloaded_path_str = await client.download_media(event.message, file=str(DOWNLOADS_DIR))
        if not downloaded_path_str:
            logger.warning("download_media вернул пустой путь, файл не скачан")
            return
        downloaded_path = Path(downloaded_path_str)

        # Если расширение отсутствует, приведём к .mp4
        if downloaded_path.suffix == "":
            target_path = downloaded_path.with_suffix(file_ext)
            try:
                downloaded_path.rename(target_path)
                downloaded_path = target_path
            except Exception:
                logger.exception("Не удалось переименовать файл без расширения")

        logger.success(
            "Видео успешно скачано: {path}. Отправляю сигнал боту.",
            path=downloaded_path
        )

        basename = downloaded_path.name
        signal_message = f"VIDEO_READY:{basename}:{original_user_id}"
        try:
            await client.send_message(BOT_ID_INT, signal_message)
        except Exception:
            # Если по числовому ID нельзя резолвить сущность, шлём явному пиру
            await client.send_message(PeerUser(BOT_ID_INT), signal_message)
        logger.info("Отправлен сигнал боту: {signal}", signal=signal_message)

    except Exception:
        logger.exception("Критическая ошибка в Telethon-хэндлере при обработке видео.")


async def main():
    # При запуске, вы можете отправить боту любое сообщение,
    # чтобы получить его ID, если вы его не знаете
    await client.start()
    # me = await client.get_me()
    # print(f"Telethon клиент запущен от имени: {me.first_name} (ID: {me.id})")
    # print(f"Бот, с которым мы работаем, должен иметь ID: {BOT_ID}")
    
    print("Telethon клиент запущен. Ожидание видео от бота...")
    await client.run_until_disconnected()
