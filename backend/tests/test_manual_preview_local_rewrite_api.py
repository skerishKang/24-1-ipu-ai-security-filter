import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes.manual_mode import get_manual_preview_service
from app.main import create_app
from app.services.manual_preview_service import ManualPreviewService
from engine.src.local_rewriter import PlaceholderLocalRewriter


class ManualPreviewLocalRewriteApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"
        os.environ["IPU_SESSION_STORE_PATH"] = str(db_path)
        os.environ["IPU_SESSION_STORE_KIND"] = "sqlite"
        self.app = create_app()
        self.app.state.manual_preview_service = ManualPreviewService()
        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        os.environ.pop("IPU_SESSION_STORE_PATH", None)
        os.environ.pop("IPU_SESSION_STORE_KIND", None)
        self.temp_dir.cleanup()

    async def test_local_rewrite_policy_returns_generalized_text_and_restores(self) -> None:
        payload = {
            "content": "홍길동 이사는 contact@ipu.co.kr 와 010-1234-5678 연락처를 포함한 계약 메모를 검토합니다.",
            "content_type": "text",
            "policy": "local_rewrite",
        }

        response = await self.client.post("/api/v1/mode/manual-preview", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["report"]["strategy"], "local_rewrite")
        self.assertNotIn("[EMAIL", body["replaced_text"])
        self.assertNotIn("[PHONE", body["replaced_text"])
        self.assertTrue(body["replacements"])
        self.assertTrue(body["restore_token"])

        restore_response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": body["session_id"],
                "restore_token": body["restore_token"],
                "replaced_text": body["replaced_text"],
            },
        )

        self.assertEqual(restore_response.status_code, 200)
        restore_body = restore_response.json()
        self.assertEqual(restore_body["restored_text"], payload["content"])
        self.assertTrue(restore_body["restored"])

    async def test_restore_rejects_invalid_restore_token(self) -> None:
        payload = {
            "content": "홍길동 이사는 contact@ipu.co.kr 와 010-1234-5678 연락처를 포함한 계약 메모를 검토합니다.",
            "content_type": "text",
            "policy": "local_rewrite",
        }

        response = await self.client.post("/api/v1/mode/manual-preview", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["restore_token"])

        restore_response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": body["session_id"],
                "restore_token": "invalid-restore-token",
                "replaced_text": body["replaced_text"],
            },
        )

        self.assertEqual(restore_response.status_code, 403)

    def test_ollama_disabled_falls_back_to_placeholder(self) -> None:
        os.environ["IPU_OLLAMA_ENABLED"] = "false"
        try:
            service = ManualPreviewService()
            self.assertIsInstance(service.local_rewriter, PlaceholderLocalRewriter)
        finally:
            os.environ.pop("IPU_OLLAMA_ENABLED", None)

    def test_remote_ollama_base_url_falls_back_to_placeholder(self) -> None:
        os.environ["IPU_OLLAMA_ENABLED"] = "true"
        os.environ["IPU_OLLAMA_BASE_URL"] = "http://192.168.0.10:11434"
        try:
            service = ManualPreviewService()
            self.assertIsInstance(service.local_rewriter, PlaceholderLocalRewriter)
        finally:
            os.environ.pop("IPU_OLLAMA_ENABLED", None)
            os.environ.pop("IPU_OLLAMA_BASE_URL", None)


if __name__ == "__main__":
    unittest.main()
