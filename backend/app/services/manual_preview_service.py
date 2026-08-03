from __future__ import annotations

import asyncio
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from random import choices
from string import ascii_lowercase, digits
from time import monotonic

from fastapi import UploadFile

from app.api.schemas.manual_preview import (
    DetectionItem,
    ManualPreviewReadiness,
    ManualPreviewReport,
    ManualPreviewRequest,
    ManualPreviewResponse,
    ManualRestoreRequest,
    ManualRestoreResponse,
    PolicyName,
    ReplacementItem,
    RewriteMetadata,
)
from app.core.exceptions import RestoreTokenError
from app.core.settings import get_settings
from app.services.audio_transcriber import (
    AudioTranscriber,
    PlaceholderAudioTranscriber,
    WhisperAudioTranscriber,
)
from app.services.file_parser import DefaultFileParser, FileParser
from engine.src.local_rewriter import OllamaLocalRewriter, PlaceholderLocalRewriter
from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.src.session_store import (
    InMemorySessionStore,
    SessionStore,
    SQLiteSessionStore,
)

logger = logging.getLogger("uvicorn.error")


class UploadConcurrencyLimiter:
    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self._active = 0
        self._lock = asyncio.Lock()

    async def try_acquire(self) -> bool:
        async with self._lock:
            if self._active >= self.max_concurrency:
                return False
            self._active += 1
            return True

    async def release(self) -> None:
        async with self._lock:
            if self._active > 0:
                self._active -= 1


class UploadConcurrencyExceededError(Exception):
    """Raised when too many upload requests are being processed concurrently."""

    def __init__(self, max_concurrency: int) -> None:
        self.max_concurrency = max_concurrency
        super().__init__(
            f"현재 처리 중인 업로드가 많습니다. 잠시 후 다시 시도해 주세요. (최대 동시 처리: {max_concurrency})"
        )


class ManualPreviewService:
    def __init__(
        self,
        session_store: SessionStore | None = None,
        file_parser: FileParser | None = None,
        audio_transcriber: AudioTranscriber | None = None,
        local_rewriter=None,
        settings=None,
    ) -> None:
        self.settings = settings or get_settings()
        self.session_store = session_store or self._build_session_store()
        self.file_parser = file_parser or DefaultFileParser(
            max_upload_bytes=self.settings.effective_upload_max_bytes(),
        )
        self.audio_transcriber = audio_transcriber or self._build_audio_transcriber()
        self.local_rewriter = local_rewriter or self._build_local_rewriter()
        self.engine = ManualPreviewEngine(
            session_store=self.session_store,
            local_rewriter=self.local_rewriter,
        )
        self._upload_limiter = UploadConcurrencyLimiter(self.settings.upload_max_concurrency)

    def build_preview(self, payload: ManualPreviewRequest, owner_hash: str = "dev-local") -> ManualPreviewResponse:
        session_id = self._create_session_id()
        self.session_store.save_owner_hash(session_id, owner_hash)
        restore_token = self._create_restore_token(session_id)
        strategy = self._resolve_strategy(payload.policy)
        started_at = monotonic()
        self._log_request_started(
            request_type="text",
            session_id=session_id,
            policy=payload.policy,
            content_type=payload.content_type,
        )

        try:
            engine_result = self.engine.manual_preview(
                content=payload.content,
                session_id=session_id,
                content_type=payload.content_type,
                policy=payload.policy,
                strategy=strategy,
                task_type=payload.task_type,
            )
        except Exception as error:
            self._log_request_failed(
                request_type="text",
                session_id=session_id,
                policy=payload.policy,
                content_type=payload.content_type,
                processing_ms=self._processing_ms(started_at),
                error=error,
            )
            raise

        self._log_request_succeeded(
            request_type="text",
            session_id=session_id,
            policy=payload.policy,
            content_type=payload.content_type,
            detection_count=len(engine_result["detections"]),
            replacement_count=len(engine_result["replacements"]),
            report_strategy=str(engine_result["report"]["strategy"]),
            processing_ms=self._processing_ms(started_at),
        )

        return self._build_response(engine_result, restore_token=restore_token)

    def restore_preview(self, payload: ManualRestoreRequest, owner_hash: str = "dev-local") -> ManualRestoreResponse:
        token_hash = self._hash_restore_token(payload.restore_token)
        if not self.session_store.verify_restore_token_hash(payload.session_id, token_hash):
            logger.warning("manual_preview_restore_denied session_id=%s", payload.session_id)
            raise RestoreTokenError()
        if not self.session_store.verify_owner_hash(payload.session_id, owner_hash):
            logger.warning("manual_preview_restore_owner_denied session_id=%s", payload.session_id)
            raise RestoreTokenError()

        restored_text = self.engine.restore(
            content=payload.replaced_text,
            session_id=payload.session_id,
            token=payload.restore_token,
            owner_hash=owner_hash,
        )
        return ManualRestoreResponse(
            session_id=payload.session_id,
            restored_text=restored_text,
            restored=restored_text != payload.replaced_text,
        )

    def _create_session_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        suffix = "".join(choices(ascii_lowercase + digits, k=6))
        return f"ipu-{timestamp}-{suffix}"

    def _create_restore_token(self, session_id: str) -> str:
        restore_token = secrets.token_urlsafe(32)
        self.session_store.save_restore_token_hash(
            session_id,
            self._hash_restore_token(restore_token),
        )
        return restore_token

    def _hash_restore_token(self, restore_token: str) -> str:
        return hashlib.sha256(restore_token.encode("utf-8")).hexdigest()

    async def build_file_preview(
        self,
        file: UploadFile,
        policy: PolicyName = "default",
        owner_hash: str = "dev-local",
    ) -> ManualPreviewResponse:
        if not await self._upload_limiter.try_acquire():
            raise UploadConcurrencyExceededError(self.settings.upload_max_concurrency)

        try:
            session_id = self._create_session_id()
            self.session_store.save_owner_hash(session_id, owner_hash)
            restore_token = self._create_restore_token(session_id)
            content_type = file.content_type or "text/plain"
            started_at = monotonic()
            self._log_request_started(
                request_type="file",
                session_id=session_id,
                policy=policy,
                content_type=content_type,
            )

            try:
                parsed_file = await self.file_parser.parse(file)
                strategy = self._resolve_strategy(policy)
                engine_result = self.engine.manual_preview(
                    content=parsed_file.content,
                    session_id=session_id,
                    content_type="text",
                    policy=policy,
                    strategy=strategy,
                )
            except Exception as error:
                self._log_request_failed(
                    request_type="file",
                    session_id=session_id,
                    policy=policy,
                    content_type=content_type,
                    processing_ms=self._processing_ms(started_at),
                    error=error,
                )
                raise

            self._log_request_succeeded(
                request_type="file",
                session_id=session_id,
                policy=policy,
                content_type=content_type,
                detection_count=len(engine_result["detections"]),
                replacement_count=len(engine_result["replacements"]),
                report_strategy=str(engine_result["report"]["strategy"]),
                processing_ms=self._processing_ms(started_at),
            )

            return self._build_response(engine_result, restore_token=restore_token)
        finally:
            await self._upload_limiter.release()

    async def build_audio_preview(
        self,
        file: UploadFile,
        policy: PolicyName = "default",
        owner_hash: str = "dev-local",
    ) -> ManualPreviewResponse:
        if not await self._upload_limiter.try_acquire():
            raise UploadConcurrencyExceededError(self.settings.upload_max_concurrency)

        try:
            session_id = self._create_session_id()
            self.session_store.save_owner_hash(session_id, owner_hash)
            restore_token = self._create_restore_token(session_id)
            content_type = file.content_type or "application/octet-stream"
            started_at = monotonic()
            self._log_request_started(
                request_type="audio",
                session_id=session_id,
                policy=policy,
                content_type=content_type,
            )

            try:
                transcribed_audio = await self.audio_transcriber.transcribe(file)
                strategy = self._resolve_strategy(policy)
                engine_result = self.engine.manual_preview(
                    content=transcribed_audio.text,
                    session_id=session_id,
                    content_type="text",
                    policy=policy,
                    strategy=strategy,
                )
            except Exception as error:
                self._log_request_failed(
                    request_type="audio",
                    session_id=session_id,
                    policy=policy,
                    content_type=content_type,
                    processing_ms=self._processing_ms(started_at),
                    error=error,
                )
                raise

            self._log_request_succeeded(
                request_type="audio",
                session_id=session_id,
                policy=policy,
                content_type=content_type,
                detection_count=len(engine_result["detections"]),
                replacement_count=len(engine_result["replacements"]),
                report_strategy=str(engine_result["report"]["strategy"]),
                processing_ms=self._processing_ms(started_at),
            )

            return self._build_response(engine_result, restore_token=restore_token)
        finally:
            await self._upload_limiter.release()

    def _resolve_strategy(self, policy: PolicyName) -> str:
        if policy == "local_rewrite":
            return "local_rewrite"
        if policy == "strict_token":
            return "strict_token"
        return "alias"

    def _log_request_started(
        self,
        request_type: str,
        session_id: str,
        policy: str,
        content_type: str,
    ) -> None:
        logger.info(
            "manual_preview_started request_type=%s policy=%s content_type=%s session_id=%s",
            request_type,
            policy,
            content_type,
            session_id,
        )

    def _log_request_succeeded(
        self,
        request_type: str,
        session_id: str,
        policy: str,
        content_type: str,
        detection_count: int,
        replacement_count: int,
        report_strategy: str,
        processing_ms: int,
    ) -> None:
        logger.info(
            "manual_preview_succeeded request_type=%s policy=%s content_type=%s session_id=%s detection_count=%s replacement_count=%s report_strategy=%s processing_ms=%s",
            request_type,
            policy,
            content_type,
            session_id,
            detection_count,
            replacement_count,
            report_strategy,
            processing_ms,
        )

    def _log_request_failed(
        self,
        request_type: str,
        session_id: str,
        policy: str,
        content_type: str,
        processing_ms: int,
        error: Exception,
    ) -> None:
        if isinstance(error, ValueError):
            logger.warning(
                "manual_preview_failed request_type=%s policy=%s content_type=%s session_id=%s error_type=%s processing_ms=%s",
                request_type,
                policy,
                content_type,
                session_id,
                error.__class__.__name__,
                processing_ms,
            )
            return

        logger.exception(
            "manual_preview_failed request_type=%s policy=%s content_type=%s session_id=%s error_type=%s processing_ms=%s",
            request_type,
            policy,
            content_type,
            session_id,
            error.__class__.__name__,
            processing_ms,
        )

    def _processing_ms(self, started_at: float) -> int:
        return int((monotonic() - started_at) * 1000)

    def _build_session_store(self) -> SessionStore:
        if self.settings.session_store_kind == "memory":
            return InMemorySessionStore(ttl_seconds=self.settings.session_ttl_seconds)
        return SQLiteSessionStore(
            db_path=self.settings.session_store_path,
            ttl_seconds=self.settings.session_ttl_seconds,
        )

    def _build_audio_transcriber(self) -> AudioTranscriber:
        max_bytes = self.settings.effective_upload_max_bytes()
        if self.settings.audio_transcriber_kind == "placeholder":
            return PlaceholderAudioTranscriber(max_upload_bytes=max_bytes)
        if self.settings.audio_transcriber_kind != "whisper":
            logger.warning(
                "manual_preview_audio_transcriber_unknown kind=%s fallback=placeholder",
                self.settings.audio_transcriber_kind,
            )
            return PlaceholderAudioTranscriber(max_upload_bytes=max_bytes)
        return WhisperAudioTranscriber(
            model_name=self.settings.whisper_model_name,
            model_dir=self.settings.whisper_model_dir,
            language=self.settings.whisper_language,
            task=self.settings.whisper_task,
            use_gpu=self.settings.whisper_use_gpu,
            max_upload_bytes=max_bytes,
        )

    def _build_local_rewriter(self):
        if not self.settings.ollama_enabled:
            logger.info("Ollama disabled, using placeholder local rewriter")
            return PlaceholderLocalRewriter()
        try:
            return OllamaLocalRewriter(
                base_url=self.settings.ollama_base_url,
                model=self.settings.ollama_model,
            )
        except Exception:
            logger.warning("Failed to initialize OllamaLocalRewriter, using placeholder")
            return PlaceholderLocalRewriter()

    def _build_response(self, engine_result: dict, restore_token: str) -> ManualPreviewResponse:
        minimized = self.settings.manual_preview_response_mode == "minimized"
        raw_metadata = engine_result.get("rewrite_metadata")
        if raw_metadata:
            rewrite_metadata = RewriteMetadata(**raw_metadata)
        else:
            rewrite_metadata = None
        return ManualPreviewResponse(
            session_id=str(engine_result["session_id"]),
            restore_token=restore_token,
            original_text="" if minimized else str(engine_result["original_text"]),
            replaced_text=str(engine_result["replaced_text"]),
            detections=self._build_detection_items(engine_result["detections"], minimized=minimized),
            replacements=self._build_replacement_items(engine_result["replacements"], minimized=minimized),
            report=ManualPreviewReport(**engine_result["report"]),
            rewrite_metadata=rewrite_metadata,
            readiness=ManualPreviewReadiness(**engine_result["readiness"]),
            copy_ready_prompt=str(engine_result["copy_ready_prompt"]),
        )

    def _build_detection_items(self, detections: list[dict], minimized: bool) -> list[DetectionItem]:
        return [
            DetectionItem(
                **{
                    **item,
                    "label": "" if minimized else item.get("label", ""),
                }
            )
            for item in detections
        ]

    def _build_replacement_items(self, replacements: list[dict], minimized: bool) -> list[ReplacementItem]:
        return [
            ReplacementItem(
                **{
                    **item,
                    "original": "" if minimized else item.get("original", ""),
                }
            )
            for item in replacements
        ]
