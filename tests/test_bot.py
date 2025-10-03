import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from pathlib import Path

from bot.bot import process_video, DOWNLOADS_DIR

class FakeVideo:
    file_unique_id = "fake123"
    file_id = "fake_id"

    async def download(self, destination):
        Path(destination).write_bytes(b"FAKE_VIDEO_BYTES")

class FakeMessage:
    video = FakeVideo()

    async def answer(self, text):
        print("Bot answer:", text)

    async def answer_document(self, document):
        assert isinstance(document.file, BytesIO)
        print("Bot sent document:", document.filename)

@pytest.mark.asyncio
@patch("bot.bot.bot.download", new_callable=AsyncMock)
@patch("bot.bot.client.audio.transcriptions.create", new_callable=AsyncMock)
@patch("bot.bot.client.chat.completions.create", new_callable=AsyncMock)
async def test_process_video(mock_chat, mock_transcribe, mock_download):
    async def fake_download(file, destination):
        Path(destination).write_bytes(b"FAKE_VIDEO_BYTES")
    mock_download.side_effect = fake_download

    mock_transcribe.return_value.text = "тест транскрипта"

    fake_choice = MagicMock()
    fake_choice.message.content = '{"company":"TestCorp","position":"Data Scientist","vacancy_description":"Описание","questions":[{"text":"Вопрос?","topic":"ML-теория","answer":"Ответ"}]}'
    mock_chat.return_value.choices = [fake_choice]

    msg = FakeMessage()

    await process_video(msg)

    assert mock_transcribe.called
    assert mock_chat.called
    assert mock_download.called

    video_path = DOWNLOADS_DIR / f"{msg.video.file_unique_id}.mp4"
    assert not video_path.exists()
