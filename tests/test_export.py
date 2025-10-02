from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR
import json

client = TestClient(app)

def test_export_analysis(tmp_path):
    data = {
        "company": "TestCorp",
        "position": "Data Scientist",
        "vacancy_description": "Анализ данных",
        "questions": [{"text": "Что такое ML?", "topic": "ML-теория", "answer": "Метод обучения"}]
    }
    json_file = UPLOAD_DIR / "fake.json"
    json_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    response = client.get("/export/fake")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
