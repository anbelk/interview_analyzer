from dotenv import load_dotenv
import asyncio
from pathlib import Path
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from loguru import logger
from openai import AsyncOpenAI
from bot.utils import generate_xlsx_from_analysis
import json
import os

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

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Пришли видео, и я верну XLSX с анализом.")

@dp.message(F.video)
async def process_video(message: types.Message):
    video_id = message.video.file_unique_id
    await message.answer("Видео получено, начинаю обработку...")

    video_path = DOWNLOADS_DIR / f"{video_id}.mp4"
    await bot.download(file=message.video.file_id, destination=video_path)
    logger.info("[Video {}] Сохранено на диск: {}", video_id, video_path)

    try:
        transcripts = []
        chunk_size = 24 * 1024 * 1024

        with open(video_path, "rb") as f:
            chunk_index = 1
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_bio = BytesIO(chunk)
                resp = await client.audio.transcriptions.create(
                    file=chunk_bio,
                    model="gpt-4o-transcribe"
                )
                transcripts.append(resp.text)
                logger.info("[Video {}] Чанк {} транскрибирован", video_id, chunk_index)
                chunk_index += 1

        full_transcript = "\n".join(transcripts)
        logger.info("[Video {}] Все чанки транскрибированы", video_id)

        prompt = PROMPT_TEMPLATE + f"\nТранскрипт:\n{full_transcript}"
        analysis_resp = await client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        analysis_text = analysis_resp.choices[0].message.content.strip()
        analysis = json.loads(analysis_text)
        logger.info("[Video {}] LLM-анализ завершен", video_id)

        xlsx_bytes = generate_xlsx_from_analysis(analysis)
        xlsx_bytes.seek(0)
        await message.answer_document(
            FSInputFile(xlsx_bytes, filename=f"report_{video_id}.xlsx")
        )
        logger.info("[Video {}] Отправка XLSX завершена", video_id)

    except Exception as e:
        logger.exception("[Video {}] Ошибка при обработке: {}", video_id, e)
        await message.answer(f"Произошла ошибка при обработке видео {video_id}: {e}")

    finally:
        video_path.unlink(missing_ok=True)

async def main():
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
