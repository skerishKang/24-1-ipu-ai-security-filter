from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackendSettings:
    session_store_kind: str
    session_store_path: Path
    session_ttl_seconds: int
    audio_transcriber_kind: str
    whisper_model_name: str
    whisper_model_dir: Path | None
    whisper_language: str | None
    whisper_task: str
    whisper_use_gpu: bool


def get_settings() -> BackendSettings:
    root_dir = Path(__file__).resolve().parents[3]
    default_store_path = root_dir / "data" / "runtime" / "manual_preview_sessions.sqlite3"
    default_whisper_model_dir = Path(
        os.getenv("IPU_WHISPER_MODEL_DIR", "~/.ipu/whisper-models")
    ).expanduser()
    session_store_kind = os.getenv("IPU_SESSION_STORE_KIND", "sqlite").strip().lower() or "sqlite"
    session_store_path = Path(
        os.getenv("IPU_SESSION_STORE_PATH", str(default_store_path))
    ).expanduser()
    session_ttl_seconds = int(os.getenv("IPU_SESSION_TTL_SECONDS", "900"))
    audio_transcriber_kind = os.getenv("IPU_AUDIO_TRANSCRIBER", "whisper").strip().lower() or "whisper"
    whisper_model_name = os.getenv("IPU_WHISPER_MODEL_NAME", "small").strip() or "small"
    whisper_model_dir = default_whisper_model_dir if default_whisper_model_dir.exists() else None
    whisper_language = os.getenv("IPU_WHISPER_LANGUAGE", "auto").strip().lower() or "auto"
    if whisper_language in {"auto", "automatic"}:
        whisper_language = None
    whisper_task = os.getenv("IPU_WHISPER_TASK", "transcribe").strip().lower() or "transcribe"
    whisper_use_gpu = os.getenv("IPU_WHISPER_USE_GPU", "true").strip().lower() not in {"0", "false", "no"}

    return BackendSettings(
        session_store_kind=session_store_kind,
        session_store_path=session_store_path,
        session_ttl_seconds=session_ttl_seconds,
        audio_transcriber_kind=audio_transcriber_kind,
        whisper_model_name=whisper_model_name,
        whisper_model_dir=whisper_model_dir,
        whisper_language=whisper_language,
        whisper_task=whisper_task,
        whisper_use_gpu=whisper_use_gpu,
    )
