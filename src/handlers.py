from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from loguru import logger
from src.config import DOWNLOADS_DIR, REPORTS_DIR
from src.services.transcription import convert_video_to_mp3, split_audio_to_chunks, transcribe_chunks
from src.services.analysis import analyze_transcript
from src.services.reports import save_report
from src.services.cleanup import cleanup_files

async def register_handlers(dp):
    @dp.message(Command("start"))
    async def start(message: types.Message):
        user = message.from_user
        logger.info("Получена команда /start от пользователя {user_id} ({name}, @{username})",
            user_id=user.id,
            name=user.full_name,
            username=user.username or "без username"
        )
        await message.answer("Привет! Пришли видео, и я верну XLSX с анализом.")

    @dp.message(F.video)
    async def process_video(message: types.Message):
        video_id = message.video.file_unique_id
        video_path = DOWNLOADS_DIR / f"{video_id}.mp4"
        audio_path = DOWNLOADS_DIR / f"{video_id}.mp3"
        report_path = REPORTS_DIR / f"report_{video_id}.xlsx"

        user = message.from_user
        video_id = message.video.file_unique_id
        logger.info(
            "Получено видео {video_id} от пользователя {user_id} ({name}, @{username})",
            user_id=user.id,
            name=user.full_name,
            username=user.username or "без username",
            video_id=video_id
        )

        logger.info("Загрузка видео {video_id}...", video_id=video_id)
        await message.bot.download(file=message.video.file_id, destination=video_path)
        logger.info("Завершена загрузка {video_id}", video_id=video_id)

        try:
            logger.info("Обработка видео {video_id}...", video_id=video_id)
            
            logger.info("{video_id}: конвертация в MP3...", video_id=video_id)
            await convert_video_to_mp3(video_path, audio_path)
            logger.info("{video_id}: завершена конвертация в MP3", video_id=video_id)

            logger.info("{video_id}: разделение на чанки...", video_id=video_id)
            chunks = await split_audio_to_chunks(audio_path, video_id)
            logger.info("{video_id}: завершено разделение на {n} чанков", video_id=video_id, n=len(chunks))

            logger.info("{video_id}: транскрипция...", video_id=video_id)
            transcript = await transcribe_chunks(chunks)
            logger.info("{video_id}: завершена транскрипция", video_id=video_id)

            logger.info("{video_id}: анализ транскрипта...", video_id=video_id)
            analysis = await analyze_transcript(transcript)
            logger.info("{video_id}: завершен анализ транскрипта", video_id=video_id)

            logger.info("{video_id}: сохранение отчета...", video_id=video_id)
            save_report(analysis, report_path)
            logger.info("{video_id}: завершено сохранение отчета", video_id=video_id)

            logger.info("{video_id}: отправление отчета...", video_id=video_id)
            await message.answer_document(FSInputFile(report_path))
            logger.info("{video_id}: завершено отправление отчета", video_id=video_id)

            logger.info("Завершена обработка видео {video_id}", video_id=video_id)

        except Exception:
            logger.exception(
                "Ошибка при обработке видео {video_id} от пользователя {user_id} ({name}, @{username})",
                video_id=video_id,
                user_id=user.id,
                name=user.full_name,
                username=user.username or "без username"
            )

        finally:
            logger.info("{video_id}: очистка временных файлов...", video_id=video_id)
            cleanup_files(video_path, audio_path, report_path, *chunks)
            logger.info("{video_id}: завершена очистка временных файлов", video_id=video_id)