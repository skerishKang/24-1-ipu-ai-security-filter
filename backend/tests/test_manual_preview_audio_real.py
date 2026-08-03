from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from app.api.routes.manual_mode import get_manual_preview_service
from app.main import create_app

DEFAULT_SAMPLE_PATH = Path(
    os.getenv(
        "IPU_REAL_WHISPER_SMOKE_SAMPLE",
        "/mnt/g/Ddrive/BatangD/task/workdiary/49-1-padiem-rnd/data/datasets/rvc_speaker_001/speaker_001/1_20240821_gJ5IX1jty3E_[ENG] 카리나의 여름 취향 A-Z까지 다 모았다! l 에스파 l 카리나 ㅣ톡톡 인터뷰_(Vocals)_seg0000.wav",
    )
)


@unittest.skipUnless(
    os.getenv("IPU_RUN_REAL_AUDIO_SMOKE", "").strip() == "1",
    "set IPU_RUN_REAL_AUDIO_SMOKE=1 to run real whisper API smoke",
)
class ManualPreviewAudioRealSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"
        os.environ["IPU_SESSION_STORE_PATH"] = str(db_path)
        os.environ["IPU_SESSION_STORE_KIND"] = "sqlite"
        os.environ["IPU_AUDIO_TRANSCRIBER"] = "whisper"
        get_manual_preview_service.cache_clear()
        self.app = create_app()
        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            timeout=120.0,
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        get_manual_preview_service.cache_clear()
        os.environ.pop("IPU_SESSION_STORE_PATH", None)
        os.environ.pop("IPU_SESSION_STORE_KIND", None)
        os.environ.pop("IPU_AUDIO_TRANSCRIBER", None)
        self.temp_dir.cleanup()

    async def test_manual_preview_audio_real_whisper_smoke(self) -> None:
        self.assertTrue(DEFAULT_SAMPLE_PATH.exists(), f"missing sample audio: {DEFAULT_SAMPLE_PATH}")

        # Opt-in real-whisper smoke reads a local sample file synchronously
        # before issuing the request; this is test fixture setup, not an
        # application code path.
        with DEFAULT_SAMPLE_PATH.open("rb") as handle:  # noqa: ASYNC230
            response = await self.client.post(
                "/api/v1/mode/manual-preview/audio",
                files={
                    "file": (
                        DEFAULT_SAMPLE_PATH.name,
                        handle.read(),
                        "audio/wav",
                    )
                },
                data={"policy": "default"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["original_text"].strip())
        self.assertGreaterEqual(body["report"]["total_detections"], 0)
        self.assertIn("report", body)
        self.assertIn("copy_ready_prompt", body)


if __name__ == "__main__":
    unittest.main()
