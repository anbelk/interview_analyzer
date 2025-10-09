import asyncio
from pathlib import Path
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from src.config import DOWNLOADS_DIR, REPORTS_DIR, ADMIN_ID
from src.services.transcription import convert_video_to_mp3, split_audio_to_chunks, transcribe_chunks
from src.services.analysis import analyze_transcript
from src.services.reports import save_report
from src.services.cleanup import cleanup_files
from loguru import logger


# ==========================================================
#  Основная обработка видео (конвертация, транскрипция и т.п.)
# ==========================================================
async def process_large_video(video_path: Path, user: types.User, bot):
    video_id = video_path.stem
    audio_path = DOWNLOADS_DIR / f"{video_id}.mp3"
    report_path = REPORTS_DIR / f"report_{video_id}.xlsx"

    try:
        logger.info("{video_id}: конвертация в MP3...", video_id=video_id)
        await convert_video_to_mp3(video_path, audio_path)
        logger.info("{video_id}: завершена конвертация в MP3", video_id=video_id)

        logger.info("{video_id}: разделение на чанки...", video_id=video_id)
        chunks = await split_audio_to_chunks(audio_path, video_id)
        logger.info("{video_id}: разделено на {n} чанков", video_id=video_id, n=len(chunks))

        logger.info("{video_id}: транскрипция...", video_id=video_id)
        transcript = await transcribe_chunks(chunks)
        logger.info("{video_id}: транскрипция завершена", video_id=video_id)

        logger.info("{video_id}: анализ транскрипта...", video_id=video_id)
        analysis = await analyze_transcript(transcript)
        logger.info("{video_id}: анализ завершён", video_id=video_id)

        logger.info("{video_id}: сохранение отчёта...", video_id=video_id)
        save_report(analysis, report_path)
        logger.info("{video_id}: отчёт сохранён", video_id=video_id)

        logger.info("{video_id}: отправка отчёта пользователю {user_id}", 
                    video_id=video_id, user_id=user.id)
        await bot.send_document(chat_id=user.id, document=FSInputFile(report_path))
        logger.info("{video_id}: отчёт отправлен", video_id=video_id)

    except Exception:
        logger.exception(
            "Ошибка при обработке видео {video_id} от пользователя {user_id} ({name}, @{username})",
            video_id=video_id,
            user_id=user.id,
            name=user.full_name,
            username=user.username or "без username"
        )
        await bot.send_message(user.id, "Произошла ошибка при обработке видео 😔")

    finally:
        logger.info("{video_id}: очистка временных файлов...", video_id=video_id)
        cleanup_files(video_path, audio_path, report_path, *chunks)
        logger.info("{video_id}: очистка завершена", video_id=video_id)


# ==========================================================
#  Регистрация хэндлеров
# ==========================================================
async def register_handlers(dp):

    # /start
    @dp.message(Command("start"))
    async def start(message: types.Message):
        user = message.from_user
        logger.info(
            "Получена команда /start от пользователя {user_id} ({name}, @{username})",
            user_id=user.id,
            name=user.full_name,
            username=user.username or "без username"
        )
        await message.answer("Привет! Пришли видео, и я верну XLSX с анализом.")

    # Пользователь прислал видео
    @dp.message(F.video)
    async def process_video(message: types.Message):
        user = message.from_user
        video_id = message.video.file_unique_id

        logger.info(
            "Получено видео {video_id} от пользователя {user_id} ({name}, @{username})",
            user_id=user.id,
            name=user.full_name,
            username=user.username or "без username",
            video_id=video_id
        )

        # 1️⃣ Пересылаем админу
        await message.forward(chat_id=ADMIN_ID)
        await message.answer("Видео отправлено на сервер, ждём загрузки...")

        logger.info("{video_id}: переслано админу, ожидаем сигнал от Telethon", video_id=video_id)

    # Telethon прислал сигнал, что видео скачано
    @dp.message(F.text.startswith("VIDEO_READY:"))
    async def handle_video_ready(message: types.Message):
        """
        Сообщение от Telethon-клиента, например:
        VIDEO_READY:AgAD1YIAAs-sKEs:7112555885
        где 7112555885 — это user_id отправителя
        """
        try:
            parts = message.text.split(":")
            if len(parts) != 3:
                logger.warning("Некорректное сообщение VIDEO_READY: {text}", text=message.text)
                return

            _, video_id, user_id_str = parts
            user_id = int(user_id_str)
            video_path = DOWNLOADS_DIR / f"{video_id}.mp4"

            logger.info("Получен сигнал VIDEO_READY для {video_id} от клиента, начинаю обработку", video_id=video_id)

            # создаём "виртуального" пользователя (aiogram.types.User)
            user = types.User(id=user_id, is_bot=False, first_name="User")

            await message.bot.send_message(chat_id=user_id, text="Видео загружено, начинаю обработку...")
            await process_large_video(video_path, user, message.bot)

        except Exception:
            logger.exception("Ошибка при обработке VIDEO_READY сообщения: {text}", text=message.text)
