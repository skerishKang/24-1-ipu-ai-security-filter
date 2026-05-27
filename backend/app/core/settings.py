from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PUBLIC_DEPLOYMENT_ENVS = {"production", "prod", "ops", "ops-target"}
SAFE_PUBLIC_RESPONSE_MODE = "minimized"


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
    ollama_enabled: bool
    ollama_base_url: str
    ollama_model: str
    manual_preview_response_mode: str
    deployment_env: str
    upload_max_bytes: int
    public_upload_max_bytes: int
    upload_max_concurrency: int
    api_key_hash: str | None

    def is_public_deployment(self) -> bool:
        return self.deployment_env in PUBLIC_DEPLOYMENT_ENVS

    def effective_upload_max_bytes(self) -> int:
        if self.is_public_deployment():
            return self.public_upload_max_bytes
        return self.upload_max_bytes


class UnsafePublicResponseModeError(RuntimeError):
    """Raised when a public deployment would expose full manual-preview responses."""


class MissingPublicApiKeyHashError(RuntimeError):
    """Raised when public deployment has no configured API key hash boundary."""


def _validate_positive_int(env_name: str, default_val: int, *, min_value: int = 1) -> int:
    raw_val = os.getenv(env_name)
    if raw_val is None:
        return default_val
    raw_val_str = raw_val.strip()
    try:
        val = int(raw_val_str)
    except ValueError as e:
        raise ValueError(f"Invalid integer value for {env_name}: '{raw_val_str}'") from e
    if val < min_value:
        raise ValueError(f"{env_name} must be greater than or equal to {min_value}, got: {val}")
    return val


def resolve_deployment_env() -> str:
    val = (
        os.getenv("IPU_DEPLOYMENT_ENV")
        or os.getenv("IPU_ENV")
        or os.getenv("APP_ENV")
        or "dev-local"
    )
    return val.strip().lower()


def validate_public_response_mode(deployment_env: str, manual_preview_response_mode: str) -> None:
    if deployment_env not in PUBLIC_DEPLOYMENT_ENVS:
        return
    if manual_preview_response_mode == SAFE_PUBLIC_RESPONSE_MODE:
        return
    raise UnsafePublicResponseModeError(
        "IPU_MANUAL_PREVIEW_RESPONSE_MODE must be set to minimized for public/ops deployments. "
        f"deployment_env={deployment_env} response_mode={manual_preview_response_mode}"
    )


def validate_public_api_key_hash(deployment_env: str, api_key_hash: str | None) -> None:
    if deployment_env not in PUBLIC_DEPLOYMENT_ENVS:
        return
    if api_key_hash:
        return
    raise MissingPublicApiKeyHashError(
        "IPU_API_KEY_HASH must be set for public/ops deployments. "
        f"deployment_env={deployment_env}"
    )


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
    audio_transcriber_kind = os.getenv("IPU_AUDIO_TRANSCRIBER", "placeholder").strip().lower() or "placeholder"
    whisper_model_name = os.getenv("IPU_WHISPER_MODEL_NAME", "small").strip() or "small"
    whisper_model_dir = default_whisper_model_dir if default_whisper_model_dir.exists() else None
    whisper_language = os.getenv("IPU_WHISPER_LANGUAGE", "auto").strip().lower() or "auto"
    if whisper_language in {"auto", "automatic"}:
        whisper_language = None
    whisper_task = os.getenv("IPU_WHISPER_TASK", "transcribe").strip().lower() or "transcribe"
    whisper_use_gpu = os.getenv("IPU_WHISPER_USE_GPU", "true").strip().lower() not in {"0", "false", "no"}
    ollama_enabled = os.getenv("IPU_OLLAMA_ENABLED", "false").strip().lower() not in {"0", "false", "no"}
    ollama_base_url = os.getenv("IPU_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
    ollama_model = os.getenv("IPU_OLLAMA_MODEL", "qwen2.5:7b-instruct").strip() or "qwen2.5:7b-instruct"
    manual_preview_response_mode = (
        os.getenv("IPU_MANUAL_PREVIEW_RESPONSE_MODE", "full").strip().lower() or "full"
    )
    deployment_env = resolve_deployment_env()
    api_key_hash = os.getenv("IPU_API_KEY_HASH", "").strip() or None
    validate_public_response_mode(deployment_env, manual_preview_response_mode)
    validate_public_api_key_hash(deployment_env, api_key_hash)
    upload_max_bytes = _validate_positive_int(
        "IPU_UPLOAD_MAX_BYTES",
        104_857_600,
        min_value=1_048_576,
    )
    public_upload_max_bytes = _validate_positive_int(
        "IPU_PUBLIC_UPLOAD_MAX_BYTES",
        20_971_520,
        min_value=1_048_576,
    )
    upload_max_concurrency = _validate_positive_int(
        "IPU_UPLOAD_MAX_CONCURRENCY",
        8,
        min_value=1,
    )

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
        ollama_enabled=ollama_enabled,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        manual_preview_response_mode=manual_preview_response_mode,
        deployment_env=deployment_env,
        upload_max_bytes=upload_max_bytes,
        public_upload_max_bytes=public_upload_max_bytes,
        upload_max_concurrency=upload_max_concurrency,
        api_key_hash=api_key_hash,
    )
