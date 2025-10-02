from fastapi import FastAPI, BackgroundTasks
from app.services.transcription import transcribe_video
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Interview Analyzer")

@app.post("/process/{filename}")
async def process_video(filename: str, background_tasks: BackgroundTasks):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        return {"error": "File not found"}

    background_tasks.add_task(transcription_task, file_path)

    return {"message": f"Video {filename} is being processed"}

async def transcription_task(file_path: Path):
    try:
        transcript = await transcribe_video(file_path)
        output_file = file_path.with_suffix(".txt")
        output_file.write_text(transcript, encoding="utf-8")
        print(f"Transcription saved to {output_file}")
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
