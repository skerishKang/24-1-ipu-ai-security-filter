#!/usr/bin/env python3
from __future__ import annotations

import importlib
from shutil import which


PYTHON_CANDIDATES = (
    "pyannote.audio",
    "whisperx",
    "speechbrain",
    "resemblyzer",
    "vosk",
)

CLI_CANDIDATES = (
    "ffmpeg",
    "python3",
)


def main() -> None:
    print("== CLI tools ==")
    for name in CLI_CANDIDATES:
        resolved = which(name)
        print(f"{name}: {'found at ' + resolved if resolved else 'missing'}")

    print()
    print("== Python diarization candidates ==")
    for module_name in PYTHON_CANDIDATES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - probe script only
            print(f"{module_name}: missing ({type(exc).__name__})")
        else:
            print(f"{module_name}: installed")


if __name__ == "__main__":
    main()
