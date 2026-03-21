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


class ManualPreviewLocalRewriteApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"
        os.environ["IPU_SESSION_STORE_PATH"] = str(db_path)
        os.environ["IPU_SESSION_STORE_KIND"] = "sqlite"
        get_manual_preview_service.cache_clear()
        self.app = create_app()
        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        get_manual_preview_service.cache_clear()
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

        restore_response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": body["session_id"],
                "replaced_text": body["replaced_text"],
            },
        )

        self.assertEqual(restore_response.status_code, 200)
        restore_body = restore_response.json()
        self.assertEqual(restore_body["restored_text"], payload["content"])
        self.assertTrue(restore_body["restored"])


if __name__ == "__main__":
    unittest.main()
