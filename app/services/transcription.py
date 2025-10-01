import asyncio
from pathlib import Path
from openai import OpenAI

client = OpenAI()

async def transcribe_video(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: client.audio.transcriptions.create(
            file=open(file_path, "rb"),
            model="whisper-1"
        )
    )
    return result.text
