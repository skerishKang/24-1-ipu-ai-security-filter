from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from random import choices
from string import ascii_lowercase, digits
from time import monotonic

from fastapi import UploadFile

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.src.session_store import InMemorySessionStore, SessionStore, SQLiteSessionStore
from engine.src.local_rewriter import OllamaLocalRewriter, PlaceholderLocalRewriter

from app.api.schemas.manual_preview import (
    DetectionItem,
    ManualRestoreRequest,
    ManualRestoreResponse,
    ManualPreviewReport,
    ManualPreviewReadiness,
    ManualPreviewRequest,
    ManualPreviewResponse,
    PolicyName,
    ReplacementItem,
)
from app.core.exceptions import RestoreTokenError
from app.core.settings import get_settings
from app.services.audio_transcriber import (
    AudioTranscriber,
    PlaceholderAudioTranscriber,
    WhisperAudioTranscriber,
)
from app.services.file_parser import DefaultFileParser, FileParser

logger = logging.getLogger("uvicorn.error")


class ManualPreviewService:
    def __init__(
        self,
        session_store: SessionStore | None = None,
        file_parser: FileParser | None = None,
        audio_transcriber: AudioTranscriber | None = None,
        local_rewriter=None,
    ) -> None:
        self.session_store = session_store or self._build_session_store()
        self.file_parser = file_parser or DefaultFileParser()
        self.audio_transcriber = audio_transcriber or self._build_audio_transcriber()
        self.local_rewriter = local_rewriter or self._build_local_rewriter()
        self.engine = ManualPreviewEngine(
            session_store=self.session_store,
            local_rewriter=self.local_rewriter,
        )

    def build_preview(self, payload: ManualPreviewRequest) -> ManualPreviewResponse:
        session_id = self._create_session_id()
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

    def restore_preview(self, payload: ManualRestoreRequest) -> ManualRestoreResponse:
        token_hash = self._hash_restore_token(payload.restore_token)
        if not self.session_store.verify_restore_token_hash(payload.session_id, token_hash):
            logger.warning("manual_preview_restore_denied session_id=%s", payload.session_id)
            raise RestoreTokenError()

        restored_text = self.engine.restore(
            content=payload.replaced_text,
            session_id=payload.session_id,
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
    ) -> ManualPreviewResponse:
        session_id = self._create_session_id()
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

    async def build_audio_preview(
        self,
        file: UploadFile,
        policy: PolicyName = "default",
    ) -> ManualPreviewResponse:
        session_id = self._create_session_id()
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
        settings = get_settings()
        if settings.session_store_kind == "memory":
            return InMemorySessionStore(ttl_seconds=settings.session_ttl_seconds)
        return SQLiteSessionStore(
            db_path=settings.session_store_path,
            ttl_seconds=settings.session_ttl_seconds,
        )

    def _build_audio_transcriber(self) -> AudioTranscriber:
        settings = get_settings()
        if settings.audio_transcriber_kind == "placeholder":
            return PlaceholderAudioTranscriber()
        if settings.audio_transcriber_kind != "whisper":
            logger.warning(
                "manual_preview_audio_transcriber_unknown kind=%s fallback=placeholder",
                settings.audio_transcriber_kind,
            )
            return PlaceholderAudioTranscriber()
        return WhisperAudioTranscriber(
            model_name=settings.whisper_model_name,
            model_dir=settings.whisper_model_dir,
            language=settings.whisper_language,
            task=settings.whisper_task,
            use_gpu=settings.whisper_use_gpu,
        )

    def _build_local_rewriter(self):
        settings = get_settings()
        if not settings.ollama_enabled:
            logger.info("Ollama disabled, using placeholder local rewriter")
            return PlaceholderLocalRewriter()
        try:
            return OllamaLocalRewriter(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
        except Exception:
            logger.warning("Failed to initialize OllamaLocalRewriter, using placeholder")
            return PlaceholderLocalRewriter()

    def _build_response(self, engine_result: dict, restore_token: str) -> ManualPreviewResponse:
        return ManualPreviewResponse(
            session_id=str(engine_result["session_id"]),
            restore_token=restore_token,
            original_text=str(engine_result["original_text"]),
            replaced_text=str(engine_result["replaced_text"]),
            detections=[
                DetectionItem(**item) for item in engine_result["detections"]
            ],
            replacements=[
                ReplacementItem(**item) for item in engine_result["replacements"]
            ],
            report=ManualPreviewReport(**engine_result["report"]),
            readiness=ManualPreviewReadiness(**engine_result["readiness"]),
            copy_ready_prompt=str(engine_result["copy_ready_prompt"]),
        )
