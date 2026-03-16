from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
FAST_VENV_SCRIPT = ROOT_DIR / "scripts" / "ensure_fast_backend_venv.sh"


def resolve_python() -> str:
    return sys.executable


def ensure_module_available(python_executable: str, module_name: str, env: dict[str, str] | None = None) -> None:
    probe = subprocess.run(
        [python_executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
        env=env,
    )
    if probe.returncode == 0:
        return
    raise SystemExit(
        f"{module_name} is not installed in {python_executable}. "
        f"Install it first or use a Python environment that already has both backend deps and whisper."
    )


def build_api_smoke_env() -> dict[str, str]:
    env = os.environ.copy()
    if not FAST_VENV_SCRIPT.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join([str(ROOT_DIR), existing] if existing else [str(ROOT_DIR)])
        return env

    result = subprocess.run(
        [str(FAST_VENV_SCRIPT),],
        check=True,
        capture_output=True,
        text=True,
    )
    fast_python = result.stdout.strip()
    site_packages = subprocess.run(
        [
            fast_python,
            "-c",
            "import site; print('\\n'.join(site.getsitepackages()))",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().splitlines()
    existing = env.get("PYTHONPATH", "")
    merged_parts = [str(ROOT_DIR), *site_packages]
    if existing:
        merged_parts.append(existing)
    merged = os.pathsep.join(merged_parts)
    env["PYTHONPATH"] = merged
    return env


def main() -> None:
    env = build_api_smoke_env()
    env["IPU_RUN_REAL_AUDIO_SMOKE"] = "1"
    python_executable = resolve_python()
    ensure_module_available(python_executable, "fastapi", env)
    ensure_module_available(python_executable, "whisper", env)
    subprocess.run(
        [python_executable, "-m", "unittest", "tests.test_manual_preview_audio_real"],
        cwd=str(BACKEND_DIR),
        env=env,
        check=True,
    )


if __name__ == "__main__":
    main()
