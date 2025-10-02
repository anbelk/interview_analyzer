import os
import sys
from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

client = TestClient(app)

def test_process_video_endpoint(tmp_path):
    test_file = tmp_path / "test.mp4"
    test_file.write_bytes(b"fake video content")
    
    target = UPLOAD_DIR / "test.mp4"
    target.write_bytes(test_file.read_bytes())

    response = client.post("/process/test.mp4")
    assert response.status_code == 200
    assert "is being processed" in response.json()["message"]
