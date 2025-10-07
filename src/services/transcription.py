import subprocess
from pathlib import Path
from openai import AsyncOpenAI
from src.config import DOWNLOADS_DIR

client = AsyncOpenAI()

async def convert_video_to_mp3(video_path: Path, audio_path: Path):
    subprocess.run([
            "ffmpeg", "-i", str(video_path), "-vn",
            "-acodec", "mp3", "-ar", "16000", "-ac", "1", "-y", str(audio_path)
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

async def split_audio_to_chunks(audio_path: Path, video_id: str):
    subprocess.run([
            "ffmpeg", "-i", str(audio_path), "-f", "segment",
            "-segment_time", "600", "-c", "copy",
            str(DOWNLOADS_DIR / f"{video_id}_chunk_%03d.mp3")
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    chunks = sorted(DOWNLOADS_DIR.glob(f"{video_id}_chunk_*.mp3"))
    return chunks

async def transcribe_chunks(chunks):
    transcripts = []
    for chunk_file in chunks:
        with open(chunk_file, "rb") as f:
            resp = await client.audio.transcriptions.create(
                file=f, model="gpt-4o-transcribe"
            )
        transcripts.append(resp.text)
    return "\n".join(transcripts)
