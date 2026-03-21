from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.tests.document_corpus_registry import DOCUMENT_CORPUS_SAMPLES


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
    text = str(preview["replaced_text"])
    return "[" in text and "]" in text


def main() -> None:
    engine = ManualPreviewEngine()

    print("IPU Document Corpus Comparison")
    print("=" * 132)
    print(
        "| sample_id | category | chars | strict det. | local det. | strict safe | local safe | "
        "strict restore | local restore | local tokenless |"
    )
    print(
        "| --- | --- | ---: | ---: | ---: | :---: | :---: | :---: | :---: | :---: |"
    )

    for sample in DOCUMENT_CORPUS_SAMPLES:
        text = (PROJECT_ROOT / sample.relative_path).read_text(encoding="utf-8").strip()
        strict_session = f"corpus-strict-{sample.sample_id}"
        local_session = f"corpus-local-{sample.sample_id}"

        strict_preview = engine.manual_preview(
            content=text,
            session_id=strict_session,
            policy="strict_token",
        )
        local_preview = engine.manual_preview(
            content=text,
            session_id=local_session,
            policy="local_rewrite",
        )

        strict_safe = not contains_original_leak(strict_preview)
        local_safe = not contains_original_leak(local_preview)
        strict_restore = restore_is_lossless(engine, strict_session, strict_preview)
        local_restore = restore_is_lossless(engine, local_session, local_preview)
        local_tokenless = not has_tokenized_output(local_preview)

        print(
            f"| {sample.sample_id} | {sample.category} | {len(text)} | "
            f"{len(strict_preview['detections'])} | {len(local_preview['detections'])} | "
            f"{to_mark(strict_safe)} | {to_mark(local_safe)} | "
            f"{to_mark(strict_restore)} | {to_mark(local_restore)} | {to_mark(local_tokenless)} |"
        )

    print()
    print("Notes:")
    print("- safe = replaced_text no longer contains original detected span labels")
    print("- restore = session restore round-trip stayed lossless")
    print("- local tokenless = local_rewrite output avoided bracket tokens")


def to_mark(value: bool) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    main()
