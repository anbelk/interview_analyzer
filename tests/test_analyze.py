import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR

client = TestClient(app)

def test_analyze_video(monkeypatch, tmp_path):
    transcript_file = UPLOAD_DIR / "fake.txt"
    transcript_file.write_text("Пример транскрипта собеседования.", encoding="utf-8")

    def fake_analyze_transcript(_):
        return {
            "company": "TestCorp",
            "position": "Data Scientist",
            "vacancy_description": "Анализ данных и ML",
            "questions": [
                {
                    "text": "Что такое регрессия?",
                    "topic": "ML-теория",
                    "answer": "Метод предсказания численных значений"
                }
            ]
        }

    monkeypatch.setattr("app.main.analyze_transcript", fake_analyze_transcript)

    response = client.post("/analyze/fake")
    assert response.status_code == 200
    print(response.json())
    result = response.json()["result"]
    assert result["company"] == "TestCorp"
    assert result["position"] == "Data Scientist"
    assert len(result["questions"]) == 1
