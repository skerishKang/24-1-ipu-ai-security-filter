import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import httpx
from fastapi import HTTPException

from app.api.routes.manual_mode import get_manual_preview_service
from app.api.schemas.manual_preview import (
    MAX_RESTORE_SESSION_ID_LENGTH,
    MAX_RESTORE_TEXT_LENGTH,
    MAX_RESTORE_TOKEN_LENGTH,
)
from app.core.auth import hash_api_key, optional_auth_owner_hash
from app.core.exceptions import RestoreTokenError
from app.main import create_app
from app.services.manual_preview_service import ManualPreviewService


class ManualPreviewRestoreLimitTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"
        os.environ["IPU_SESSION_STORE_PATH"] = str(db_path)
        os.environ["IPU_SESSION_STORE_KIND"] = "sqlite"
        os.environ["IPU_AUDIO_TRANSCRIBER"] = "placeholder"
        self.app = create_app()
        service = ManualPreviewService()
        self.app.state.manual_preview_service = service
        self.app.dependency_overrides[get_manual_preview_service] = lambda request=None: service

        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        self.app.dependency_overrides.clear()
        os.environ.pop("IPU_SESSION_STORE_PATH", None)
        os.environ.pop("IPU_SESSION_STORE_KIND", None)
        os.environ.pop("IPU_AUDIO_TRANSCRIBER", None)
        self.temp_dir.cleanup()

    async def _create_preview(self) -> dict:
        response = await self.client.post(
            "/api/v1/mode/manual-preview",
            json={
                "content": "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
                "content_type": "text",
                "policy": "strict_token",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    async def test_restore_rejects_over_limit_replaced_text(self) -> None:
        preview = await self._create_preview()

        response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": preview["session_id"],
                "restore_token": preview["restore_token"],
                "replaced_text": "x" * (MAX_RESTORE_TEXT_LENGTH + 1),
            },
        )

        self.assertEqual(response.status_code, 422)

    async def test_restore_rejects_over_limit_session_id(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": "s" * (MAX_RESTORE_SESSION_ID_LENGTH + 1),
                "restore_token": "token",
                "replaced_text": "[EMAIL_01]",
            },
        )

        self.assertEqual(response.status_code, 422)

    async def test_restore_rejects_over_limit_restore_token(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": "ipu-restore-limit-test",
                "restore_token": "t" * (MAX_RESTORE_TOKEN_LENGTH + 1),
                "replaced_text": "[EMAIL_01]",
            },
        )

        self.assertEqual(response.status_code, 422)

    async def test_restore_token_can_restore_multiple_texts_within_session_ttl(self) -> None:
        preview = await self._create_preview()
        restore_payload = {
            "session_id": preview["session_id"],
            "restore_token": preview["restore_token"],
        }

        current_restore = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                **restore_payload,
                "replaced_text": preview["replaced_text"],
            },
        )
        self.assertEqual(current_restore.status_code, 200)
        self.assertTrue(current_restore.json()["restored"])

        ai_response_restore = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                **restore_payload,
                "replaced_text": f"외부 응답: {preview['replaced_text']}",
            },
        )

        self.assertEqual(ai_response_restore.status_code, 200)
        self.assertTrue(ai_response_restore.json()["restored"])
        self.assertIn("contact@ipu.co.kr", ai_response_restore.json()["restored_text"])

    async def test_restore_requires_matching_owner_hash(self) -> None:
        service = self.app.state.manual_preview_service
        payload = {
            "content": "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
            "content_type": "text",
            "policy": "strict_token",
        }
        request_model = service._build_response.__globals__["ManualPreviewRequest"](**payload)
        preview = service.build_preview(request_model, owner_hash="owner-a")

        restore_model = service._build_response.__globals__["ManualRestoreRequest"](
            session_id=preview.session_id,
            restore_token=preview.restore_token,
            replaced_text=preview.replaced_text,
        )

        with self.assertRaises(RestoreTokenError):
            service.restore_preview(restore_model, owner_hash="owner-b")

        restored = service.restore_preview(restore_model, owner_hash="owner-a")
        self.assertTrue(restored.restored)
        self.assertIn("contact@ipu.co.kr", restored.restored_text)

    async def test_public_auth_dependency_requires_valid_header_when_configured(self) -> None:
        secret = "valid-test-secret"
        settings = SimpleNamespace(
            is_public_deployment=lambda: True,
            api_key_hash=hash_api_key(secret),
        )
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings)))

        self.assertEqual(optional_auth_owner_hash(request, secret), settings.api_key_hash)

        with self.assertRaises(HTTPException) as missing_ctx:
            optional_auth_owner_hash(request, None)
        self.assertEqual(missing_ctx.exception.status_code, 401)

        with self.assertRaises(HTTPException) as wrong_ctx:
            optional_auth_owner_hash(request, "other-test-secret")
        self.assertEqual(wrong_ctx.exception.status_code, 403)

    async def test_auth_dependency_preserves_dev_local_and_unconfigured_public_behavior(self) -> None:
        dev_settings = SimpleNamespace(
            is_public_deployment=lambda: False,
            api_key_hash=None,
        )
        dev_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=dev_settings)))
        self.assertEqual(optional_auth_owner_hash(dev_request, None), "dev-local")

        public_settings = SimpleNamespace(
            is_public_deployment=lambda: True,
            api_key_hash=None,
        )
        public_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=public_settings)))
        self.assertEqual(optional_auth_owner_hash(public_request, None), "public-unconfigured")


if __name__ == "__main__":
    unittest.main()
