#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    ok: bool
    required: bool
    detail: str


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def build_checks(root: Path) -> list[DependencyCheck]:
    backend_dir = root / "backend"
    frontend_dir = root / "frontend"

    checks = [
        DependencyCheck(
            name="backend-dir",
            ok=backend_dir.is_dir(),
            required=True,
            detail=str(backend_dir),
        ),
        DependencyCheck(
            name="frontend-dir",
            ok=frontend_dir.is_dir(),
            required=True,
            detail=str(frontend_dir),
        ),
        DependencyCheck(
            name="python3",
            ok=command_exists("python3") or command_exists("python"),
            required=True,
            detail="python3 or python",
        ),
        DependencyCheck(
            name="node",
            ok=command_exists("node"),
            required=True,
            detail="frontend smoke/live integration runner",
        ),
        DependencyCheck(
            name="uvicorn-venv",
            ok=(
                (backend_dir / ".venv" / "bin" / "python").exists()
                or (backend_dir / ".venv-win" / "Scripts" / "python.exe").exists()
            ),
            required=False,
            detail="preferred backend runtime; fallback python is still allowed",
        ),
        DependencyCheck(
            name="tesseract",
            ok=command_exists("tesseract"),
            required=False,
            detail="scan PDF OCR fallback",
        ),
        DependencyCheck(
            name="pdftoppm",
            ok=command_exists("pdftoppm"),
            required=False,
            detail="scan PDF rasterization for OCR fallback",
        ),
        DependencyCheck(
            name="pdftocairo",
            ok=command_exists("pdftocairo"),
            required=False,
            detail="optional PDF rasterization helper",
        ),
    ]
    return checks


def print_report(checks: list[DependencyCheck]) -> None:
    print("IPU demo-stack dependency check")
    print("")
    for check in checks:
        status = "OK" if check.ok else ("WARN" if not check.required else "MISSING")
        required = "required" if check.required else "optional"
        print(f"- {check.name}: {status} ({required})")
        print(f"  {check.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local dependencies for the IPU demo stack.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any required dependency is missing.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    checks = build_checks(root)
    print_report(checks)

    missing_required = [check for check in checks if check.required and not check.ok]
    if missing_required and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
