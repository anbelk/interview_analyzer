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

async def process_large_video(video_id: str, user_id: int, bot):
    video_path = DOWNLOADS_DIR / f"{video_id}.mp4"
    audio_path = DOWNLOADS_DIR / f"{video_id}.mp3"
    report_path = REPORTS_DIR / f"report_{video_id}.xlsx"

    logger.info("[{video_id}] Начинаю обработку для пользователя {user_id}", video_id=video_id, user_id=user_id)

    try:
        logger.info("[{video_id}] Конвертация видео в MP3...", video_id=video_id)
        await convert_video_to_mp3(video_path, audio_path)

        logger.info("[{video_id}] Разделение аудио на чанки...", video_id=video_id)
        chunks = await split_audio_to_chunks(audio_path, video_id)
        logger.info("[{video_id}] Разделено на {n} чанков", video_id=video_id, n=len(chunks))

        logger.info("[{video_id}] Транскрипция аудио...", video_id=video_id)
        transcript = await transcribe_chunks(chunks)

        logger.info("[{video_id}] Анализ транскрипта...", video_id=video_id)
        analysis = await analyze_transcript(transcript)

        logger.info("[{video_id}] Сохранение отчёта...", video_id=video_id)
        save_report(analysis, report_path)

        logger.info("[{video_id}] Отправка отчёта пользователю {user_id}...", video_id=video_id, user_id=user_id)
        await bot.send_document(chat_id=user_id, document=FSInputFile(report_path))
        
        logger.success("[{video_id}] Обработка завершена успешно", video_id=video_id)

    except Exception:
        logger.exception("[{video_id}] Ошибка при обработке", video_id=video_id)
        await bot.send_message(user_id, "Произошла ошибка при обработке видео")

    finally:
        logger.info("[{video_id}] Очистка временных файлов...", video_id=video_id)
        cleanup_files(video_path, audio_path, report_path, *chunks)

async def register_handlers(dp):
    @dp.message(Command("start"))
    async def start(message: types.Message):
        user = message.from_user
        logger.info("[BOT] Команда /start от пользователя {user_id}", user_id=user.id)
        await message.answer("Привет! Пришли видео, и я верну XLSX с анализом")

    @dp.message(F.video)
    async def process_video(message: types.Message):
        user_id = message.from_user.id
        video = message.video
        video_id = video.file_unique_id
        duration = video.duration

        max_duration = 7200
        if duration > max_duration:
            await message.answer(f"Видео слишком длинное ({duration} секунд). Максимум {max_duration} секунд.")
            return

        logger.info("[BOT] Получено видео {video_id} от пользователя {user_id}", video_id=video_id, user_id=user_id)

        caption_text = f"{user_id} {video_id}"

        await message.bot.send_video(
            chat_id=ADMIN_ID,
            video=message.video.file_id,
            caption=str(caption_text)
        )
        await message.answer("Видео отправлено на сервер, ждём загрузки...")

        logger.info("[BOT] Видео {video_id} передано Telethon для обработки", video_id=video_id)

