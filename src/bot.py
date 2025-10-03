from dotenv import load_dotenv
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from loguru import logger
from openai import AsyncOpenAI
from src.utils import generate_xlsx_from_analysis
import json
import os
import subprocess

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

PROMPT_TEMPLATE = """
Ты получаешь транскрипт технического интервью программиста.
Верни JSON:
{
    "company": "Название компании",
    "position": "Название должности",
    "vacancy_description": "Краткое описание",
    "questions": [
        {"text": "...", "topic": "...", "answer": "..."}
    ]
}
"""

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    logger.info("Получена команда /start от пользователя: {}", message.from_user.id)
    await message.answer("Привет! Пришли видео, и я верну XLSX с анализом.")

@dp.message(F.video)
async def process_video(message: types.Message):
    video_id = message.video.file_unique_id
    await message.answer("Видео получено, начинаю обработку...")

    video_path = DOWNLOADS_DIR / f"{video_id}.mp4"
    await bot.download(file=message.video.file_id, destination=video_path)
    logger.info("[Video {}] Сохранено на диск: {}", video_id, video_path)

    audio_path = DOWNLOADS_DIR / f"{video_id}.mp3"

    try:
        # Конвертация видео в mp3
        subprocess.run([
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-acodec", "mp3",
            "-ar", "16000",
            "-ac", "1",
            "-y", str(audio_path)
        ], check=True)
        logger.info("[Video {}] Конвертация в MP3 завершена: {}", video_id, audio_path)

        # Разбиваем на чанки по 10 минут (в downloads)
        chunk_files = []
        subprocess.run([
            "ffmpeg",
            "-i", str(audio_path),
            "-f", "segment",
            "-segment_time", "600",
            "-c", "copy",
            str(DOWNLOADS_DIR / f"{video_id}_chunk_%03d.mp3")
        ], check=True)

        chunk_files = sorted(DOWNLOADS_DIR.glob(f"{video_id}_chunk_*.mp3"))
        logger.info("[Video {}] Аудио разбито на {} чанков", video_id, len(chunk_files))

        # Транскрибируем каждый чанк
        transcripts = []
        for chunk_file in chunk_files:
            logger.info("[Video {}] Транскрибируем {}", video_id, chunk_file)
            with open(chunk_file, "rb") as f:
                resp = await client.audio.transcriptions.create(
                    file=f,
                    model="gpt-4o-transcribe"
                )
            transcripts.append(resp.text)

        full_transcript = "\n".join(transcripts)
        logger.info("[Video {}] Все чанки транскрибированы", video_id)

        # LLM-анализ
        prompt = PROMPT_TEMPLATE + f"\nТранскрипт:\n{full_transcript}"
        analysis_resp = await client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        analysis_text = analysis_resp.choices[0].message.content.strip()
        analysis = json.loads(analysis_text)
        logger.info("[Video {}] LLM-анализ завершен", video_id)

        # Генерация XLSX в папку reports
        xlsx_path = REPORTS_DIR / f"report_{video_id}.xlsx"
        with open(xlsx_path, "wb") as f:
            f.write(generate_xlsx_from_analysis(analysis).getbuffer())

        # Отправка XLSX
        await message.answer_document(FSInputFile(xlsx_path))
        logger.info("[Video {}] Отправка XLSX завершена", video_id)

    except Exception as e:
        logger.exception("[Video {}] Ошибка при обработке: {}", video_id, e)
        await message.answer(f"Произошла ошибка при обработке видео {video_id}: {e}")

    finally:
        # Очистка всех файлов после отправки
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        xlsx_path.unlink(missing_ok=True)
        for f in DOWNLOADS_DIR.glob(f"{video_id}_chunk_*.mp3"):
            f.unlink(missing_ok=True)

async def main():
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
