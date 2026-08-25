"""Reproducibility manifest builder for benchmark runs."""

from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ReproducibilityManifest:
    seed: int
    corpus_version: str
    schema_version: str
    git_sha: str
    git_dirty: bool
    python_version: str
    platform: str
    command: str
    execution_timestamp_utc: str
    engine_version_note: str = "engine imported read-only from repository at git_sha"
    extra_dependencies: dict[str, str] = field(default_factory=dict)


def resolve_git_state(repo_root: str) -> tuple[str, bool]:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "benchmark", "engine"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return sha, bool(status.stdout.strip())
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"git state unavailable: {exc}") from exc


def build_manifest(
    repo_root: str,
    seed: int,
    corpus_version: str,
    schema_version: str,
    command: str,
    timestamp_utc: str,
) -> ReproducibilityManifest:
    sha, dirty = resolve_git_state(repo_root)
    return ReproducibilityManifest(
        seed=seed,
        corpus_version=corpus_version,
        schema_version=schema_version,
        git_sha=sha,
        git_dirty=dirty,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        command=command,
        execution_timestamp_utc=timestamp_utc,
    )


def manifest_to_dict(manifest: ReproducibilityManifest) -> dict[str, object]:
    return asdict(manifest)
