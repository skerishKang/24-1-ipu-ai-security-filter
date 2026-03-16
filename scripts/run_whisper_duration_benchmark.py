from __future__ import annotations

import asyncio
import io
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from app.services.audio_transcriber import WhisperAudioTranscriber


DEFAULT_SOURCE_AUDIO = Path(
    os.getenv(
        "IPU_AUDIO_BENCHMARK_SOURCE",
        "/mnt/g/Ddrive/BatangD/task/workdiary/49-1-padiem-rnd/data/datasets/rvc_speaker_001/speaker_001/1_20240821_gJ5IX1jty3E_[ENG] 카리나의 여름 취향 A-Z까지 다 모았다! l 에스파 l 카리나 ㅣ톡톡 인터뷰_(Vocals).wav",
    )
)
DEFAULT_MODEL_DIR = Path(
    os.getenv(
        "IPU_WHISPER_MODEL_DIR",
        "G:/Ddrive/BatangD/task/workdiary/48. 2024_성장지원/New_dev/models/whisper",
    )
).expanduser()
DURATIONS = (15, 30)


class LocalUploadFile:
    def __init__(self, path: Path, content_type: str = "audio/wav") -> None:
        self.filename = path.name
        self.content_type = content_type
        self.size = path.stat().st_size
        self._buffer = io.BytesIO(path.read_bytes())

    async def read(self) -> bytes:
        self._buffer.seek(0)
        return self._buffer.read()


def build_transcriber() -> WhisperAudioTranscriber:
    whisper_language = os.getenv("IPU_WHISPER_LANGUAGE", "auto").strip().lower()
    return WhisperAudioTranscriber(
        model_name=os.getenv("IPU_WHISPER_MODEL_NAME", "small"),
        model_dir=DEFAULT_MODEL_DIR if DEFAULT_MODEL_DIR.exists() else None,
        language=None if whisper_language in {"auto", "automatic"} else whisper_language,
        task=os.getenv("IPU_WHISPER_TASK", "transcribe"),
        use_gpu=os.getenv("IPU_WHISPER_USE_GPU", "true").strip().lower() not in {"0", "false", "no"},
    )


def slice_audio(source_audio: Path, duration_seconds: int, target_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio),
            "-t",
            str(duration_seconds),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(target_path),
        ],
        check=True,
        capture_output=True,
    )


async def benchmark_duration(transcriber: WhisperAudioTranscriber, sample_path: Path) -> tuple[float, str]:
    upload = LocalUploadFile(sample_path)
    started_at = time.perf_counter()
    result = await transcriber.transcribe(upload)
    elapsed = time.perf_counter() - started_at
    return elapsed, result.text.strip()


async def main() -> None:
    if not DEFAULT_SOURCE_AUDIO.exists():
        raise SystemExit(f"source audio not found: {DEFAULT_SOURCE_AUDIO}")

    transcriber = build_transcriber()
    print(f"source: {DEFAULT_SOURCE_AUDIO}")
    print(f"model: {transcriber.model_name}")

    with tempfile.TemporaryDirectory(prefix="ipu-audio-bench-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        for duration in DURATIONS:
            sample_path = tmpdir_path / f"sample_{duration}s.wav"
            slice_audio(DEFAULT_SOURCE_AUDIO, duration, sample_path)
            elapsed, text = await benchmark_duration(transcriber, sample_path)
            print(f"duration_seconds: {duration}")
            print(f"elapsed_seconds: {elapsed:.3f}")
            print(f"text_length: {len(text)}")
            print(f"text_preview: {text[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
