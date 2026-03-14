from __future__ import annotations

import logging
from datetime import datetime, timezone
from random import choices
from string import ascii_lowercase, digits
from time import monotonic

from fastapi import UploadFile

from engine.src.manual_preview_engine import ManualPreviewEngine

from app.api.schemas.manual_preview import (
    DetectionItem,
    ManualPreviewReport,
    ManualPreviewRequest,
    ManualPreviewResponse,
    PolicyName,
    ReplacementItem,
)

logger = logging.getLogger("uvicorn.error")
MAX_TEXT_FILE_BYTES = 1_048_576


class ManualPreviewService:
    def __init__(self) -> None:
        self.engine = ManualPreviewEngine()

    def build_preview(self, payload: ManualPreviewRequest) -> ManualPreviewResponse:
        session_id = self._create_session_id()
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

        return ManualPreviewResponse(
            session_id=str(engine_result["session_id"]),
            original_text=str(engine_result["original_text"]),
            replaced_text=str(engine_result["replaced_text"]),
            detections=[
                DetectionItem(**item) for item in engine_result["detections"]
            ],
            replacements=[
                ReplacementItem(**item) for item in engine_result["replacements"]
            ],
            report=ManualPreviewReport(**engine_result["report"]),
            copy_ready_prompt=str(engine_result["copy_ready_prompt"]),
        )

    def _create_session_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        suffix = "".join(choices(ascii_lowercase + digits, k=6))
        return f"ipu-{timestamp}-{suffix}"

    async def build_file_preview(
        self,
        file: UploadFile,
        policy: PolicyName = "default",
    ) -> ManualPreviewResponse:
        session_id = self._create_session_id()
        content_type = file.content_type or "text/plain"
        started_at = monotonic()
        self._log_request_started(
            request_type="file",
            session_id=session_id,
            policy=policy,
            content_type=content_type,
        )

        try:
            content = await self._read_text_file(file)
            strategy = self._resolve_strategy(policy)
            engine_result = self.engine.manual_preview(
                content=content,
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

        return ManualPreviewResponse(
            session_id=str(engine_result["session_id"]),
            original_text=str(engine_result["original_text"]),
            replaced_text=str(engine_result["replaced_text"]),
            detections=[
                DetectionItem(**item) for item in engine_result["detections"]
            ],
            replacements=[
                ReplacementItem(**item) for item in engine_result["replacements"]
            ],
            report=ManualPreviewReport(**engine_result["report"]),
            copy_ready_prompt=str(engine_result["copy_ready_prompt"]),
        )

    def _resolve_strategy(self, policy: PolicyName) -> str:
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

    async def _read_text_file(self, file: UploadFile) -> str:
        filename = file.filename or "uploaded.txt"
        content_type = file.content_type or "text/plain"
        file_size = getattr(file, "size", None)

        if not filename.lower().endswith(".txt"):
            raise ValueError("현재 manual-preview 파일 업로드는 .txt 파일만 지원합니다.")

        if content_type not in {"text/plain", "application/octet-stream"}:
            raise ValueError("현재 manual-preview 파일 업로드는 text/plain 만 지원합니다.")

        if file_size is not None and file_size > MAX_TEXT_FILE_BYTES:
            raise ValueError("현재 manual-preview 파일 업로드는 1MB 이하의 .txt 파일만 지원합니다.")

        raw = await file.read()
        if len(raw) > MAX_TEXT_FILE_BYTES:
            raise ValueError("현재 manual-preview 파일 업로드는 1MB 이하의 .txt 파일만 지원합니다.")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("UTF-8 텍스트 파일만 지원합니다.") from error

        if not text.strip():
            raise ValueError("비어 있는 텍스트 파일은 처리할 수 없습니다.")

        return text
