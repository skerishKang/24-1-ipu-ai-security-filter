"""Real ASGI concurrent request tests for upload guardrails."""

from __future__ import annotations

import asyncio
import io
import os
import unittest
import wave
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import httpx
from app.api.routes import manual_mode as manual_mode_module
from app.api.routes.manual_mode import get_manual_preview_service
from app.main import create_app
from app.main import limiter as main_limiter
from app.services.audio_transcriber import TranscribedAudio
from app.services.file_parser import ParsedFileContent
from app.services.manual_preview_service import ManualPreviewService
from fastapi import UploadFile


def _reset_rate_limiters() -> None:
    """Clear accumulated rate-limit hits so tests don't leak across classes."""
    manual_mode_module.limiter._storage.reset()
    main_limiter._storage.reset()


class FakeSlowFileParser:
    """Fake file parser that blocks parsing until release_event is set."""

    def __init__(self, started_event: asyncio.Event, release_event: asyncio.Event):
        self.started_event = started_event
        self.release_event = release_event

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        self.started_event.set()
        await self.release_event.wait()
        return ParsedFileContent(
            content="parsed test file content",
            normalized_content_type="text/plain",
            filename=file.filename or "test.txt",
        )


class FakeSlowAudioTranscriber:
    """Fake audio transcriber that blocks transcription until release_event is set."""

    def __init__(self, started_event: asyncio.Event, release_event: asyncio.Event):
        self.started_event = started_event
        self.release_event = release_event

    async def transcribe(self, file: UploadFile) -> TranscribedAudio:
        self.started_event.set()
        await self.release_event.wait()
        return TranscribedAudio(
            text="transcribed test audio text",
            content_type=file.content_type or "audio/wav",
            filename=file.filename or "test.wav",
            engine_name="fake-slow-whisper",
        )


class RealConcurrentUploadGuardrailTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"

        self._env_patcher = patch.dict(os.environ, {
            "IPU_SESSION_STORE_PATH": str(db_path),
            "IPU_SESSION_STORE_KIND": "sqlite",
            "IPU_AUDIO_TRANSCRIBER": "placeholder",
            "IPU_DEPLOYMENT_ENV": "dev-local",
            "IPU_UPLOAD_MAX_BYTES": "104857600",
            "IPU_PUBLIC_UPLOAD_MAX_BYTES": "20971520",
            "IPU_UPLOAD_MAX_CONCURRENCY": "1",  # limit to 1 concurrent request
        })
        self._env_patcher.start()
        _reset_rate_limiters()

        self.started_event = asyncio.Event()
        self.release_event = asyncio.Event()

    async def asyncTearDown(self):
        self._env_patcher.stop()
        self.temp_dir.cleanup()

    async def test_concurrent_file_uploads(self):
        fake_parser = FakeSlowFileParser(self.started_event, self.release_event)

        app = create_app()
        service = ManualPreviewService(file_parser=fake_parser)
        app.state.manual_preview_service = service
        app.dependency_overrides[get_manual_preview_service] = lambda request=None: service

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Start first file upload task (will block on release_event)
            upload_task1 = asyncio.create_task(
                client.post(
                    "/api/v1/mode/manual-preview/file",
                    files={"file": ("test.txt", b"some content", "text/plain")},
                    data={"policy": "default"},
                )
            )

            # Wait until the first request actually enters the fake parser
            await self.started_event.wait()

            # Execute second concurrent file upload request (should fail immediately with 503)
            resp2 = await client.post(
                "/api/v1/mode/manual-preview/file",
                files={"file": ("test2.txt", b"another content", "text/plain")},
                data={"policy": "default"},
            )
            self.assertEqual(resp2.status_code, 503)
            body = resp2.json()
            self.assertIn("동시 처리", body["detail"])

            # Release the first request
            self.release_event.set()

            # First request should now finish successfully with 200
            resp1 = await upload_task1
            self.assertEqual(resp1.status_code, 200)
            self.assertIn("parsed test file content", resp1.json()["replaced_text"])

    async def test_concurrent_audio_uploads(self):
        fake_transcriber = FakeSlowAudioTranscriber(self.started_event, self.release_event)

        app = create_app()
        service = ManualPreviewService(audio_transcriber=fake_transcriber)
        app.state.manual_preview_service = service
        app.dependency_overrides[get_manual_preview_service] = lambda request=None: service

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Generate valid WAV bytes
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00\x00" * int(16000 * 0.1))
            wav_bytes = wav_buf.getvalue()

            # Start first audio upload task (will block on release_event)
            upload_task1 = asyncio.create_task(
                client.post(
                    "/api/v1/mode/manual-preview/audio",
                    files={"file": ("test.wav", wav_bytes, "audio/wav")},
                    data={"policy": "default"},
                )
            )

            # Wait until the first request actually enters the fake transcriber
            await self.started_event.wait()

            # Execute second concurrent audio upload request (should fail immediately with 503)
            resp2 = await client.post(
                "/api/v1/mode/manual-preview/audio",
                files={"file": ("test2.wav", wav_bytes, "audio/wav")},
                data={"policy": "default"},
            )
            self.assertEqual(resp2.status_code, 503)
            body = resp2.json()
            self.assertIn("동시 처리", body["detail"])

            # Release the first request
            self.release_event.set()

            # First request should now finish successfully with 200
            resp1 = await upload_task1
            self.assertEqual(resp1.status_code, 200)
            self.assertIn("transcribed test audio text", resp1.json()["replaced_text"])
