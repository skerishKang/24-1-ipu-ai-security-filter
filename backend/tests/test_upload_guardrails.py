"""Tests for upload guardrails: upload size limits and concurrency semaphore."""

from __future__ import annotations

import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx
from fastapi import UploadFile

from app.core.settings import BackendSettings, UnsafePublicResponseModeError, get_settings
from app.main import create_app
from app.api.routes.manual_mode import get_manual_preview_service
from app.api.routes import manual_mode as manual_mode_module
from app.main import limiter as main_limiter
from app.services.manual_preview_service import ManualPreviewService


def _reset_rate_limiters() -> None:
    """Clear accumulated rate-limit hits so tests don't leak across classes."""
    manual_mode_module.limiter._storage.reset()
    main_limiter._storage.reset()


def _make_wav_bytes(duration_seconds: float = 0.1) -> bytes:
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * int(16000 * duration_seconds))
    return buf.getvalue()


class SettingsUploadGuardrailTest(unittest.TestCase):
    """Unit tests for BackendSettings upload guardrail helpers."""

    def test_dev_local_default_is_100mb(self):
        settings = BackendSettings(
            session_store_kind="sqlite",
            session_store_path=Path("/tmp/test.db"),
            session_ttl_seconds=900,
            audio_transcriber_kind="placeholder",
            whisper_model_name="small",
            whisper_model_dir=None,
            whisper_language=None,
            whisper_task="transcribe",
            whisper_use_gpu=False,
            ollama_enabled=False,
            ollama_base_url="",
            ollama_model="",
            manual_preview_response_mode="full",
            deployment_env="dev-local",
            upload_max_bytes=104_857_600,
            public_upload_max_bytes=20_971_520,
            upload_max_concurrency=8,
        )
        self.assertFalse(settings.is_public_deployment())
        self.assertEqual(settings.effective_upload_max_bytes(), 104_857_600)

    def test_production_env_uses_public_limit(self):
        for env in ("production", "prod", "ops", "ops-target"):
            settings = BackendSettings(
                session_store_kind="sqlite",
                session_store_path=Path("/tmp/test.db"),
                session_ttl_seconds=900,
                audio_transcriber_kind="placeholder",
                whisper_model_name="small",
                whisper_model_dir=None,
                whisper_language=None,
                whisper_task="transcribe",
                whisper_use_gpu=False,
                ollama_enabled=False,
                ollama_base_url="",
                ollama_model="",
                manual_preview_response_mode="minimized",
                deployment_env=env,
                upload_max_bytes=104_857_600,
                public_upload_max_bytes=20_971_520,
                upload_max_concurrency=8,
            )
            self.assertTrue(settings.is_public_deployment(), f"{env} should be public")
            self.assertEqual(settings.effective_upload_max_bytes(), 20_971_520)

    def test_env_override_upload_max_bytes(self):
        with patch.dict(os.environ, {"IPU_UPLOAD_MAX_BYTES": "52428800"}):
            settings = get_settings()
            self.assertEqual(settings.upload_max_bytes, 52_428_800)

    def test_env_override_public_upload_max_bytes(self):
        with patch.dict(os.environ, {"IPU_PUBLIC_UPLOAD_MAX_BYTES": "10485760"}):
            settings = get_settings()
            self.assertEqual(settings.public_upload_max_bytes, 10_485_760)

    def test_env_override_upload_max_concurrency(self):
        with patch.dict(os.environ, {"IPU_UPLOAD_MAX_CONCURRENCY": "2"}):
            settings = get_settings()
            self.assertEqual(settings.upload_max_concurrency, 2)

    def test_env_override_deployment_env_requires_minimized_response_mode(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "ops",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            settings = get_settings()
            self.assertTrue(settings.is_public_deployment())
            self.assertEqual(settings.manual_preview_response_mode, "minimized")

    def test_public_deployment_rejects_full_response_mode(self):
        for env in ("production", "prod", "ops", "ops-target"):
            with self.subTest(env=env):
                with patch.dict(os.environ, {
                    "IPU_DEPLOYMENT_ENV": env,
                    "IPU_ALLOWED_ORIGINS": "http://example.com",
                    "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "full",
                }):
                    with self.assertRaises(UnsafePublicResponseModeError):
                        get_settings()

    def test_create_app_rejects_public_deployment_with_full_response_mode(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "ops",
            "IPU_ALLOWED_ORIGINS": "http://example.com",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "full",
        }):
            with self.assertRaises(UnsafePublicResponseModeError):
                create_app()

    def test_create_app_allows_public_deployment_with_minimized_response_mode(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "ops",
            "IPU_ALLOWED_ORIGINS": "http://example.com",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            app = create_app()
            self.assertIsNotNone(app)


class UploadSizeLimitApiTest(unittest.IsolatedAsyncioTestCase):
    """Integration tests for upload size limits via the API."""

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
            "IPU_UPLOAD_MAX_CONCURRENCY": "8",
        })
        self._env_patcher.start()
        _reset_rate_limiters()

        self.app = create_app()
        service = ManualPreviewService()
        self.app.state.manual_preview_service = service
        self.app.dependency_overrides[get_manual_preview_service] = lambda request=None: service

        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()
        self._env_patcher.stop()
        self.temp_dir.cleanup()

    async def test_dev_mode_accepts_file_under_100mb(self):
        """Dev-local mode should accept files up to 100MB."""
        small_content = b"hello world " * 100
        resp = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={"file": ("test.txt", small_content, "text/plain")},
            data={"policy": "default"},
        )
        self.assertEqual(resp.status_code, 200)

    async def test_dev_mode_rejects_file_over_100mb(self):
        """Dev-local mode should reject files over 100MB."""
        large_content = b"x" * (104_857_600 + 1)
        resp = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={"file": ("big.txt", large_content, "text/plain")},
            data={"policy": "default"},
        )
        self.assertEqual(resp.status_code, 413)


class PublicModeUploadLimitTest(unittest.IsolatedAsyncioTestCase):
    """Test that public/ops deployment uses lower upload limits."""

    async def asyncSetUp(self):
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"

        self._env_patcher = patch.dict(os.environ, {
            "IPU_SESSION_STORE_PATH": str(db_path),
            "IPU_SESSION_STORE_KIND": "sqlite",
            "IPU_AUDIO_TRANSCRIBER": "placeholder",
            "IPU_DEPLOYMENT_ENV": "ops",
            "IPU_UPLOAD_MAX_BYTES": "104857600",
            "IPU_PUBLIC_UPLOAD_MAX_BYTES": "20971520",
            "IPU_UPLOAD_MAX_CONCURRENCY": "8",
            "IPU_ALLOWED_ORIGINS": "http://localhost:4241",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        })
        self._env_patcher.start()
        _reset_rate_limiters()

        self.app = create_app()
        service = ManualPreviewService()
        self.app.state.manual_preview_service = service
        self.app.dependency_overrides[get_manual_preview_service] = lambda request=None: service

        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()
        self._env_patcher.stop()
        self.temp_dir.cleanup()

    async def test_ops_mode_accepts_file_under_20mb(self):
        content = b"hello " * 100
        resp = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={"file": ("small.txt", content, "text/plain")},
            data={"policy": "default"},
        )
        self.assertEqual(resp.status_code, 200)

    async def test_ops_mode_rejects_file_over_20mb(self):
        """Ops mode should reject files exceeding the 20MB public limit."""
        over_20mb = b"x" * (20_971_520 + 1)
        resp = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={"file": ("big.txt", over_20mb, "text/plain")},
            data={"policy": "default"},
        )
        self.assertEqual(resp.status_code, 413)


class UploadConcurrencyGuardTest(unittest.IsolatedAsyncioTestCase):
    """Test that the concurrency limiter rejects excess upload requests."""

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
            "IPU_UPLOAD_MAX_CONCURRENCY": "1",
        })
        self._env_patcher.start()
        _reset_rate_limiters()

        self.app = create_app()
        service = ManualPreviewService()
        self.app.state.manual_preview_service = service
        self.app.dependency_overrides[get_manual_preview_service] = lambda request=None: service

        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()
        self._env_patcher.stop()
        self.temp_dir.cleanup()

    async def test_concurrency_exceeded_returns_503_file(self):
        """When limiter is full, file upload should return 503."""
        service = self.app.state.manual_preview_service

        # Manually acquire the limiter slot to simulate full concurrency
        self.assertTrue(await service._upload_limiter.try_acquire())
        try:
            resp = await self.client.post(
                "/api/v1/mode/manual-preview/file",
                files={"file": ("test.txt", b"hello", "text/plain")},
                data={"policy": "default"},
            )
            self.assertEqual(resp.status_code, 503)
            body = resp.json()
            self.assertIn("동시 처리", body["detail"])
        finally:
            await service._upload_limiter.release()

    async def test_concurrency_exceeded_returns_503_audio(self):
        """When limiter is full, audio upload should return 503."""
        service = self.app.state.manual_preview_service

        self.assertTrue(await service._upload_limiter.try_acquire())
        try:
            wav_bytes = _make_wav_bytes(0.1)
            resp = await self.client.post(
                "/api/v1/mode/manual-preview/audio",
                files={"file": ("test.wav", wav_bytes, "audio/wav")},
                data={"policy": "default"},
            )
            self.assertEqual(resp.status_code, 503)
        finally:
            await service._upload_limiter.release()

    async def test_concurrency_allows_after_release(self):
        """After limiter is released, upload should succeed."""
        service = self.app.state.manual_preview_service

        # Acquire and release immediately — next request should work
        self.assertTrue(await service._upload_limiter.try_acquire())
        await service._upload_limiter.release()

        resp = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            data={"policy": "default"},
        )
        self.assertEqual(resp.status_code, 200)


class UploadConcurrencyLimiterTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for UploadConcurrencyLimiter."""

    async def test_acquire_and_release_flow(self):
        from app.services.manual_preview_service import UploadConcurrencyLimiter
        limiter = UploadConcurrencyLimiter(max_concurrency=2)

        # 1. 첫 acquire 성공
        self.assertTrue(await limiter.try_acquire())
        self.assertEqual(limiter._active, 1)

        self.assertTrue(await limiter.try_acquire())
        self.assertEqual(limiter._active, 2)

        # 2. max 초과 acquire 실패
        self.assertFalse(await limiter.try_acquire())
        self.assertEqual(limiter._active, 2)

        # 3. release 후 acquire 성공
        await limiter.release()
        self.assertEqual(limiter._active, 1)
        self.assertTrue(await limiter.try_acquire())
        self.assertEqual(limiter._active, 2)

        # 4. release를 중복 호출해도 active count가 음수로 내려가지 않음
        await limiter.release()
        await limiter.release()
        await limiter.release()
        await limiter.release()
        self.assertEqual(limiter._active, 0)


class ExistingTestsNotBrokenTest(unittest.IsolatedAsyncioTestCase):
    """Verify that existing file/audio parser limit constants are preserved."""

    async def test_file_parser_max_upload_bytes_still_100mb(self):
        from app.services.file_parser import MAX_UPLOAD_FILE_BYTES
        self.assertEqual(MAX_UPLOAD_FILE_BYTES, 104_857_600)

    async def test_audio_max_upload_bytes_still_100mb(self):
        from app.services.audio_transcriber import MAX_AUDIO_UPLOAD_BYTES
        self.assertEqual(MAX_AUDIO_UPLOAD_BYTES, 104_857_600)

    async def test_audio_max_duration_still_60s(self):
        from app.services.audio_transcriber import MAX_AUDIO_DURATION_SECONDS
        self.assertEqual(MAX_AUDIO_DURATION_SECONDS, 60)


class DeploymentEnvironmentPriorityTest(unittest.TestCase):
    """Tests for prioritizing IPU_DEPLOYMENT_ENV, IPU_ENV, and APP_ENV."""

    def test_deployment_env_priority_ipu_deployment_env(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "production",
            "IPU_ENV": "dev-local",
            "APP_ENV": "dev-local",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            settings = get_settings()
            self.assertEqual(settings.deployment_env, "production")
            self.assertTrue(settings.is_public_deployment())

    def test_deployment_env_priority_ipu_env(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "",
            "IPU_ENV": "production",
            "APP_ENV": "dev-local",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            settings = get_settings()
            self.assertEqual(settings.deployment_env, "production")
            self.assertTrue(settings.is_public_deployment())

    def test_deployment_env_priority_app_env(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "",
            "IPU_ENV": "",
            "APP_ENV": "production",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            settings = get_settings()
            self.assertEqual(settings.deployment_env, "production")
            self.assertTrue(settings.is_public_deployment())

    def test_deployment_env_no_env_defaults_to_dev_local(self):
        with patch.dict(os.environ, {
            "IPU_DEPLOYMENT_ENV": "",
            "IPU_ENV": "",
            "APP_ENV": ""
        }):
            settings = get_settings()
            self.assertEqual(settings.deployment_env, "dev-local")
            self.assertFalse(settings.is_public_deployment())


class CorsDeploymentSettingsTest(unittest.TestCase):
    """Tests for CORS allowed origins behavior under different deployment environments."""

    def test_ops_stage_without_allowed_origins_raises_error(self):
        # When APP_ENV=production but IPU_ALLOWED_ORIGINS is not set, create_app should fail
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "IPU_ALLOWED_ORIGINS": "",
            "IPU_DEPLOYMENT_ENV": "",
            "IPU_ENV": "",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            with self.assertRaises(RuntimeError) as ctx:
                create_app()
            self.assertIn("IPU_ALLOWED_ORIGINS must be set", str(ctx.exception))

    def test_ops_stage_with_allowed_origins_starts_successfully(self):
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "IPU_ALLOWED_ORIGINS": "http://example.com,http://localhost:3000",
            "IPU_DEPLOYMENT_ENV": "",
            "IPU_ENV": "",
            "IPU_MANUAL_PREVIEW_RESPONSE_MODE": "minimized",
        }):
            app = create_app()
            self.assertIsNotNone(app)


class UploadGuardrailSettingsValidationTest(unittest.TestCase):
    """Tests for validating upload guardrail settings values."""

    def test_upload_max_bytes_invalid_values(self):
        for invalid_val in ("5000", "1000000", "0", "-5", "abc", ""):
            with patch.dict(os.environ, {"IPU_UPLOAD_MAX_BYTES": invalid_val}):
                with self.assertRaises(ValueError):
                    get_settings()

    def test_public_upload_max_bytes_invalid_values(self):
        for invalid_val in ("2000", "1000000", "0", "-10", "xyz", ""):
            with patch.dict(os.environ, {"IPU_PUBLIC_UPLOAD_MAX_BYTES": invalid_val}):
                with self.assertRaises(ValueError):
                    get_settings()

    def test_upload_max_concurrency_invalid_values(self):
        for invalid_val in ("0", "-1", "foo", ""):
            with patch.dict(os.environ, {"IPU_UPLOAD_MAX_CONCURRENCY": invalid_val}):
                with self.assertRaises(ValueError):
                    get_settings()

    def test_valid_positive_values_succeed(self):
        with patch.dict(os.environ, {
            "IPU_UPLOAD_MAX_BYTES": "1048576",
            "IPU_PUBLIC_UPLOAD_MAX_BYTES": "2097152",
            "IPU_UPLOAD_MAX_CONCURRENCY": "4"
        }):
            settings = get_settings()
            self.assertEqual(settings.upload_max_bytes, 1048576)
            self.assertEqual(settings.public_upload_max_bytes, 2097152)
            self.assertEqual(settings.upload_max_concurrency, 4)
