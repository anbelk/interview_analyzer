import subprocess
import asyncio
from pathlib import Path
from faster_whisper import WhisperModel
from src.config import DOWNLOADS_DIR

async def convert_video_to_mp3(video_path: Path, audio_path: Path):
    await asyncio.to_thread(
        subprocess.run,
        [
            "ffmpeg", "-i", str(video_path), "-vn",
            "-acodec", "mp3", "-ar", "16000", "-ac", "1", "-y", str(audio_path)
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

async def split_audio_to_chunks(audio_path: Path, video_id: str):
    await asyncio.to_thread(
        subprocess.run,
        [
            "ffmpeg", "-i", str(audio_path), "-f", "segment",
            "-segment_time", "600", "-c", "copy",
            str(DOWNLOADS_DIR / f"{video_id}chunk%03d.mp3")
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    chunks = sorted(DOWNLOADS_DIR.glob(f"{video_id}chunk*.mp3"))
    return chunks

def _transcribe_sync(chunks: list[Path]) -> str:
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    
    transcripts = []
    for chunk_file in chunks:
        segments, info = model.transcribe(str(chunk_file), beam_size=5)
        chunk_transcript = "".join(segment.text for segment in segments)
        transcripts.append(chunk_transcript)
        
    return "\n".join(transcripts)

async def transcribe_chunks(chunks: list[Path]) -> str:
    loop = asyncio.get_running_loop()
    full_transcript = await loop.run_in_executor(None, _transcribe_sync, chunks)
    return full_transcript