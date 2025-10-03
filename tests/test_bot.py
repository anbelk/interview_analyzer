import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from pathlib import Path

import bot.bot as bot_module

class FakeVideo:
    file_unique_id = "fake123"
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
@patch("app.bot.client.audio.transcriptions.create", new_callable=AsyncMock)
@patch("app.bot.client.chat.completions.create", new_callable=AsyncMock)
async def test_process_video(mock_chat, mock_transcribe):
    mock_transcribe.return_value.text = "тест транскрипта"
    
    fake_choice = MagicMock()
    fake_choice.message.content = '{"company":"TestCorp","position":"Data Scientist","vacancy_description":"Описание","questions":[{"text":"Вопрос?","topic":"ML-теория","answer":"Ответ"}]}'
    mock_chat.return_value.choices = [fake_choice]

    msg = FakeMessage()

    await bot_module.process_video(msg)

    assert mock_transcribe.called
    assert mock_chat.called

    video_path = bot_module.DOWNLOADS_DIR / f"{msg.video.file_unique_id}.mp4"
    assert not video_path.exists()
