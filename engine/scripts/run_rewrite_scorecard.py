from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.tests.rewrite_comparison_samples import REWRITE_COMPARISON_SAMPLES


def contains_original_leak(preview: dict[str, object]) -> bool:
    replaced_text = str(preview["replaced_text"])
    for item in preview["detections"]:
        original = str(item["label"]).strip()
        if original and original in replaced_text:
            return True
    return False


def restore_is_lossless(engine: ManualPreviewEngine, session_id: str, preview: dict[str, object]) -> bool:
    restored = engine.restore(str(preview["replaced_text"]), session_id)
    return restored == str(preview["original_text"])


def has_tokenized_output(preview: dict[str, object]) -> bool:
    return "[" in str(preview["replaced_text"]) and "]" in str(preview["replaced_text"])


def main() -> None:
    engine = ManualPreviewEngine()

    print("IPU Rewrite Scorecard")
    print("=" * 110)
    print(
        "| sample_id | strict detections | local detections | strict leak | local leak | "
        "strict restore | local restore | local tokenless |"
    )
    print(
        "| --- | ---: | ---: | :---: | :---: | :---: | :---: | :---: |"
    )

    for sample in REWRITE_COMPARISON_SAMPLES:
        strict_session = f"scorecard-strict-{sample.sample_id}"
        local_session = f"scorecard-local-{sample.sample_id}"

        strict_preview = engine.manual_preview(
            content=sample.content,
            session_id=strict_session,
            policy="strict_token",
        )
        local_preview = engine.manual_preview(
            content=sample.content,
            session_id=local_session,
            policy="local_rewrite",
        )

        strict_leak = contains_original_leak(strict_preview)
        local_leak = contains_original_leak(local_preview)
        strict_restore = restore_is_lossless(engine, strict_session, strict_preview)
        local_restore = restore_is_lossless(engine, local_session, local_preview)
        local_tokenless = not has_tokenized_output(local_preview)

        print(
            f"| {sample.sample_id} | "
            f"{len(strict_preview['detections'])} | "
            f"{len(local_preview['detections'])} | "
            f"{to_mark(strict_leak is False)} | "
            f"{to_mark(local_leak is False)} | "
            f"{to_mark(strict_restore)} | "
            f"{to_mark(local_restore)} | "
            f"{to_mark(local_tokenless)} |"
        )

    print()
    print("Interpretation:")
    print("- strict/local leak = yes means no original sensitive span remained in replaced_text")
    print("- restore = yes means session-based restore remained lossless")
    print("- local tokenless = yes means local_rewrite produced generalized text instead of bracket tokens")


def to_mark(value: bool) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    main()
