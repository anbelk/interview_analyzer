import io
from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR

client = TestClient(app)

def test_full_pipeline(monkeypatch):
    async def fake_transcribe_video(fp):
        return "fake transcript"

    def fake_analyze_transcript(fp):
        return {
            "company": "TestCorp",
            "position": "Data Scientist",
            "vacancy_description": "Анализ данных",
            "questions": [{"text": "Что такое ML?", "topic": "ML-теория", "answer": "Метод обучения"}]
        }

    monkeypatch.setattr("app.main.transcribe_video", fake_transcribe_video)
    monkeypatch.setattr("app.main.analyze_transcript", fake_analyze_transcript)

    file_content = b"fake video content"
    files = {"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
    response = client.post("/full_pipeline", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    xlsx_file = UPLOAD_DIR / "test.xlsx"
    assert xlsx_file.exists()
