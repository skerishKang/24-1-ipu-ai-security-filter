from __future__ import annotations

import asyncio
from dataclasses import dataclass
import importlib
import io
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Protocol, TYPE_CHECKING
import wave

if TYPE_CHECKING:
    from fastapi import UploadFile
else:
    UploadFile = Any

from app.core.exceptions import ProcessingLimitExceededError
from app.services.upload_reader import read_limited_upload

MAX_AUDIO_UPLOAD_BYTES = 104_857_600
MAX_AUDIO_DURATION_SECONDS = 60
FFPROBE_TIMEOUT_SECONDS = 10
AUDIO_DURATION_PROBER_ENV = "IPU_AUDIO_DURATION_PROBER"
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".webm"}
SUPPORTED_WAV_CONTENT_TYPES = {"audio/wav", "audio/x-wav", "audio/wave"}
LOGGER = logging.getLogger("uvicorn.error")


@dataclass(frozen=True)
class TranscribedAudio:
    text: str
    content_type: str
    filename: str
    engine_name: str


class AudioTranscriber(Protocol):
    async def transcribe(self, file: UploadFile) -> TranscribedAudio: ...


class BaseAudioTranscriber:
    def __init__(self, max_upload_bytes: int = MAX_AUDIO_UPLOAD_BYTES) -> None:
        self.max_upload_bytes = max_upload_bytes

    async def _read_validated_audio(self, file: UploadFile) -> tuple[str, str, bytes]:
        filename = file.filename or "uploaded-audio"
        suffix = Path(filename).suffix.lower()
        content_type = file.content_type or "application/octet-stream"

        if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
            raise ValueError("현재 manual-preview 음성 업로드는 .wav, .mp3, .m4a, .mp4, .webm 파일만 고려합니다.")

        file_size = getattr(file, "size", None)
        if file_size is not None and file_size > self.max_upload_bytes:
            raise ValueError(f"현재 manual-preview 음성 업로드는 {self.max_upload_bytes // (1024 * 1024)}MB 이하 파일만 고려합니다.")

        raw = await read_limited_upload(
            file,
            self.max_upload_bytes,
            error_factory=lambda: ValueError(
                f"현재 manual-preview 음성 업로드는 {self.max_upload_bytes // (1024 * 1024)}MB 이하 파일만 고려합니다."
            ),
        )

        if suffix == ".wav" or content_type in SUPPORTED_WAV_CONTENT_TYPES:
            self._validate_wav_duration(raw)
        else:
            self._validate_non_wav_duration(raw, suffix)

        return filename, content_type, raw

    def _validate_wav_duration(self, raw: bytes) -> None:
        try:
            with wave.open(io.BytesIO(raw), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                if rate == 0:
                    raise ValueError("WAV 파일을 해석할 수 없습니다.")
                duration = frames / rate
        except (wave.Error, EOFError, OSError) as error:
            raise ValueError("WAV 파일을 해석할 수 없습니다.") from error

        if duration > MAX_AUDIO_DURATION_SECONDS:
            raise ProcessingLimitExceededError(
                f"WAV audio duration {duration:.1f} seconds exceeds the processing limit of {MAX_AUDIO_DURATION_SECONDS} seconds."
            )

    def _validate_non_wav_duration(self, raw: bytes, suffix: str) -> None:
        prober = os.getenv(AUDIO_DURATION_PROBER_ENV, "none").strip().lower()
        if prober in {"", "none", "disabled"}:
            return
        if prober != "ffprobe":
            raise ValueError(f"Unsupported audio duration prober: {prober}")
        duration = self._probe_duration_with_ffprobe(raw, suffix)
        if duration > MAX_AUDIO_DURATION_SECONDS:
            raise ProcessingLimitExceededError(
                f"Audio duration {duration:.1f} seconds exceeds the processing limit of {MAX_AUDIO_DURATION_SECONDS} seconds."
            )

    def _probe_duration_with_ffprobe(self, raw: bytes, suffix: str) -> float:
        if shutil.which("ffprobe") is None:
            raise ValueError("ffprobe is required for non-WAV audio duration validation.")
        with tempfile.NamedTemporaryFile(suffix=suffix or ".audio", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(raw)
        try:
            completed = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(tmp_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=FFPROBE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            raise ProcessingLimitExceededError(
                f"ffprobe exceeded the processing timeout of {FFPROBE_TIMEOUT_SECONDS} seconds."
            ) from error
        except subprocess.CalledProcessError as error:
            raise ValueError("ffprobe could not read the audio duration.") from error
        finally:
            tmp_path.unlink(missing_ok=True)

        try:
            payload = json.loads(completed.stdout or "{}")
            duration = float(payload.get("format", {}).get("duration", 0))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("ffprobe returned an invalid audio duration.") from error
        if duration <= 0:
            raise ValueError("ffprobe returned an invalid audio duration.")
        return duration


class PlaceholderAudioTranscriber(BaseAudioTranscriber):
    def __init__(self, max_upload_bytes: int = MAX_AUDIO_UPLOAD_BYTES) -> None:
        super().__init__(max_upload_bytes=max_upload_bytes)

    async def transcribe(self, file: UploadFile) -> TranscribedAudio:
        await self._read_validated_audio(file)
        raise NotImplementedError(
            "음성 STT는 아직 연결되지 않았습니다. 로컬 STT 엔진을 연결하면 이 경로에서 manual-preview로 이어집니다."
        )


class WhisperAudioTranscriber(BaseAudioTranscriber):
    def __init__(
        self,
        *,
        model_name: str = "small",
        model_dir: Path | None = None,
        language: str | None = None,
        task: str = "transcribe",
        use_gpu: bool = True,
        max_upload_bytes: int = MAX_AUDIO_UPLOAD_BYTES,
    ) -> None:
        super().__init__(max_upload_bytes=max_upload_bytes)
        self.model_name = model_name
        self.model_dir = model_dir
        self.language = language
        self.task = task
        self.use_gpu = use_gpu
        self._model = None

    async def transcribe(self, file: UploadFile) -> TranscribedAudio:
        filename, content_type, raw = await self._read_validated_audio(file)
        text = await asyncio.to_thread(self._transcribe_bytes, raw, filename)
        if not text.strip():
            raise ValueError("음성 파일에서 전사 결과를 얻지 못했습니다.")
        return TranscribedAudio(
            text=text.strip(),
            content_type=content_type,
            filename=filename,
            engine_name=f"whisper:{self.model_name}",
        )

    def _transcribe_bytes(self, raw: bytes, filename: str) -> str:
        whisper = importlib.import_module("whisper")
        torch = importlib.import_module("torch")

        if self._model is None:
            device = "cuda" if self.use_gpu and torch.cuda.is_available() else "cpu"
            download_root = str(self.model_dir) if self.model_dir else None
            LOGGER.info(
                "manual_preview_audio_transcriber loading whisper model name=%s device=%s model_dir=%s",
                self.model_name,
                device,
                download_root or "",
            )
            self._model = whisper.load_model(self.model_name, device=device, download_root=download_root)

        suffix = Path(filename).suffix.lower() or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(raw)

        try:
            options: dict[str, object] = {
                "task": self.task,
                "verbose": False,
            }
            if self.language:
                options["language"] = self.language
            result = self._model.transcribe(str(tmp_path), **options)
            return str(result.get("text", "")).strip()
        finally:
            tmp_path.unlink(missing_ok=True)
