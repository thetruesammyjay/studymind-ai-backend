"""Tests for VoiceService."""

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.voice_service import VoiceService


@pytest.fixture
def mock_gemini():
    gemini = MagicMock()
    gemini.transcribe = AsyncMock(return_value="hello world")
    return gemini


@pytest.fixture
def voice_service(mock_gemini):
    return VoiceService(mock_gemini)


class TestTranscribeAudio:
    @pytest.mark.asyncio
    async def test_plain_base64(self, voice_service, mock_gemini):
        raw = b"fake audio bytes"
        b64 = base64.b64encode(raw).decode()
        result = await voice_service.transcribe_audio(b64)
        assert result == "hello world"
        mock_gemini.transcribe.assert_awaited_once_with(raw)

    @pytest.mark.asyncio
    async def test_data_uri_header_stripped(self, voice_service, mock_gemini):
        raw = b"fake audio bytes"
        b64 = base64.b64encode(raw).decode()
        data_uri = f"data:audio/webm;base64,{b64}"
        result = await voice_service.transcribe_audio(data_uri)
        assert result == "hello world"
        mock_gemini.transcribe.assert_awaited_once_with(raw)

    @pytest.mark.asyncio
    async def test_propagates_errors(self, mock_gemini):
        mock_gemini.transcribe = AsyncMock(side_effect=RuntimeError("API down"))
        service = VoiceService(mock_gemini)
        with pytest.raises(RuntimeError, match="API down"):
            await service.transcribe_audio(base64.b64encode(b"data").decode())
