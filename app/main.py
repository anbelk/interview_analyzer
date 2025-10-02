import json
import shutil
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.services.transcription import transcribe_video
from app.services.analyzer import analyze_transcript
from app.services.exporter import export_to_xlsx

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

@app.get("/export/{filename}")
async def export_analysis(filename: str):
    json_file = UPLOAD_DIR / f"{filename}.json"
    if not json_file.exists():
        return {"error": "JSON analysis not found. Please run /analyze first."}

    xlsx_file = UPLOAD_DIR / f"{filename}.xlsx"
    data = json.loads(json_file.read_text(encoding="utf-8"))
    export_to_xlsx(data, xlsx_file)

    return FileResponse(path=xlsx_file, filename=f"{filename}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/full_pipeline")
async def full_pipeline(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    transcript = await transcribe_video(file_path)
    transcript_file = file_path.with_suffix(".txt")
    transcript_file.write_text(transcript, encoding="utf-8")

    analysis = analyze_transcript(transcript_file)
    json_file = file_path.with_suffix(".json")
    json_file.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    xlsx_file = file_path.with_suffix(".xlsx")
    export_to_xlsx(analysis, xlsx_file)

    return FileResponse(
        path=xlsx_file,
        filename=f"{file.filename}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
