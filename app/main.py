from fastapi import FastAPI, BackgroundTasks
from app.services.transcription import transcribe_video
from pathlib import Path
from app.services.analyzer import analyze_transcript
import json

UPLOAD_DIR = Path("uploads")

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

@app.post("/analyze/{filename}")
async def analyze_video(filename: str):
    transcript_file = UPLOAD_DIR / f"{filename}.txt"
    if not transcript_file.exists():
        return {"error": "Transcript not found. Please run /process first."}

    try:
        analysis = analyze_transcript(transcript_file)
    except Exception as e:
        return {"error": str(e)}

    output_file = UPLOAD_DIR / f"{filename}.json"
    output_file.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"message": f"Analysis saved to {output_file}", "result": analysis}
