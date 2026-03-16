#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ToolCandidate:
    name: str
    command: str
    available: bool
    strategy: str
    notes: str


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def detect_candidates() -> list[ToolCandidate]:
    soffice_available = command_exists("soffice") or command_exists("libreoffice")
    hwp5txt_available = command_exists("hwp5txt")
    tesseract_available = command_exists("tesseract")
    pdftoppm_available = command_exists("pdftoppm")

    return [
        ToolCandidate(
            name="libreoffice-headless",
            command="soffice",
            available=soffice_available,
            strategy="preferred-local-converter",
            notes=(
                "가장 현실적인 1차 후보. .hwp -> .pdf 또는 .docx 변환 뒤 기존 parser 경로 재사용. "
                "현재 환경에서는 명령이 보이지 않으면 운영 설치가 필요하다."
            ),
        ),
        ToolCandidate(
            name="pyhwp-hwp5txt",
            command="hwp5txt",
            available=hwp5txt_available,
            strategy="text-only-extractor",
            notes=(
                "본문 텍스트 추출에는 유용하지만 레이아웃 보존은 약하다. "
                "manual-preview 목적에는 충분할 수 있으나 운영 설치 검토가 필요하다."
            ),
        ),
        ToolCandidate(
            name="pdf-ocr-fallback-chain",
            command="pdftoppm+tesseract",
            available=tesseract_available and pdftoppm_available,
            strategy="secondary-fallback",
            notes=(
                ".hwp를 직접 읽는 도구가 없을 때, 외부 변환으로 PDF를 만든 뒤 현재 OCR fallback 경로를 재사용하는 차선책."
            ),
        ),
        ToolCandidate(
            name="manual-convert-to-hwpx",
            command="hancom-or-user-conversion",
            available=True,
            strategy="current-safe-default",
            notes=(
                "현재 제품 기본 전략. 사용자가 .hwp를 .hwpx/.pdf/.docx/.txt 중 하나로 변환한 뒤 업로드하도록 안내한다."
            ),
        ),
    ]


def detect_runtime() -> dict[str, bool]:
    return {
        "soffice": command_exists("soffice"),
        "libreoffice": command_exists("libreoffice"),
        "hwp5txt": command_exists("hwp5txt"),
        "tesseract": command_exists("tesseract"),
        "pdftoppm": command_exists("pdftoppm"),
        "pdftocairo": command_exists("pdftocairo"),
    }


def print_text_report(candidates: list[ToolCandidate], runtime: dict[str, bool]) -> None:
    print("IPU HWP conversion probe")
    print("")
    print("Runtime")
    for name, available in runtime.items():
        print(f"- {name}: {'yes' if available else 'no'}")

    print("")
    print("Candidates")
    for candidate in candidates:
        print(f"- {candidate.name}")
        print(f"  command: {candidate.command}")
        print(f"  available: {'yes' if candidate.available else 'no'}")
        print(f"  strategy: {candidate.strategy}")
        print(f"  notes: {candidate.notes}")


def main() -> int:
    runtime = detect_runtime()
    candidates = detect_candidates()

    if "--json" in sys.argv:
        payload = {
            "runtime": runtime,
            "candidates": [asdict(candidate) for candidate in candidates],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print_text_report(candidates, runtime)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
