from __future__ import annotations

import asyncio
import io
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from app.services.audio_transcriber import WhisperAudioTranscriber


DEFAULT_SAMPLE_PATH = Path(
    os.getenv(
        "IPU_REAL_WHISPER_SMOKE_SAMPLE",
        "/mnt/g/Ddrive/BatangD/task/workdiary/49-1-padiem-rnd/data/datasets/rvc_speaker_001/speaker_001/1_20240821_gJ5IX1jty3E_[ENG] 카리나의 여름 취향 A-Z까지 다 모았다! l 에스파 l 카리나 ㅣ톡톡 인터뷰_(Vocals)_seg0000.wav",
    )
)
DEFAULT_MODEL_DIR = Path(
    os.getenv(
        "IPU_WHISPER_MODEL_DIR",
        "G:/Ddrive/BatangD/task/workdiary/48. 2024_성장지원/New_dev/models/whisper",
    )
).expanduser()


class LocalUploadFile:
    def __init__(self, path: Path, content_type: str = "audio/wav") -> None:
        self.filename = path.name
        self.content_type = content_type
        self.size = path.stat().st_size
        self._buffer = io.BytesIO(path.read_bytes())

    async def read(self) -> bytes:
        self._buffer.seek(0)
        return self._buffer.read()


async def main() -> None:
    sample_path = DEFAULT_SAMPLE_PATH
    if not sample_path.exists():
        raise SystemExit(f"sample audio not found: {sample_path}")

    whisper_language = os.getenv("IPU_WHISPER_LANGUAGE", "auto").strip().lower()
    transcriber = WhisperAudioTranscriber(
        model_name=os.getenv("IPU_WHISPER_MODEL_NAME", "small"),
        model_dir=DEFAULT_MODEL_DIR if DEFAULT_MODEL_DIR.exists() else None,
        language=None if whisper_language in {"auto", "automatic"} else whisper_language,
        task=os.getenv("IPU_WHISPER_TASK", "transcribe"),
        use_gpu=os.getenv("IPU_WHISPER_USE_GPU", "true").strip().lower() not in {"0", "false", "no"},
    )

    upload = LocalUploadFile(sample_path)
    result = await transcriber.transcribe(upload)

    print(f"sample: {sample_path}")
    print(f"engine: {result.engine_name}")
    print(f"text_length: {len(result.text)}")
    print("text:")
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
