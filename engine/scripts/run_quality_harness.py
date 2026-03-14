from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.tests.quality_samples import QUALITY_SAMPLES, QualitySample


def main() -> None:
    engine = ManualPreviewEngine()

    print("IPU Engine Quality Harness")
    print("=" * 80)

    for sample in QUALITY_SAMPLES:
        print(f"\n[{sample.sample_id}] {sample.description}")
        print(f"- sample_group: {sample.sample_group}")
        print(f"- minimum_detections: {sample.minimum_detections}")
        print(f"- expected_types: {', '.join(sample.expected_types) if sample.expected_types else '-'}")
        if sample.observation_note:
            print(f"- observation_note: {sample.observation_note}")

        for policy in ("default", "strict_token"):
            preview = engine.manual_preview(
                content=sample.content,
                session_id=f"quality-script-{sample.sample_id}-{policy}",
                policy=policy,
            )
            detection_types = ", ".join(item["type"] for item in preview["detections"]) or "-"
            replacement_tokens = ", ".join(item["replaced"] for item in preview["replacements"]) or "-"

            print(f"  policy={policy}")
            print(f"    baseline_status={summarize_baseline_status(sample, preview)}")
            print(f"    detections={len(preview['detections'])} [{detection_types}]")
            print(f"    replacements={len(preview['replacements'])} [{replacement_tokens}]")
            print(
                "    report="
                f"strategy:{preview['report']['strategy']} "
                f"risk:{preview['report']['risk_level']} "
                f"review:{preview['report']['review_status']}"
            )
            print(f"    replaced_text={preview['replaced_text']}")


def summarize_baseline_status(sample: QualitySample, preview: dict[str, object]) -> str:
    if sample.sample_group != "baseline":
        return "observe-detections-present" if preview["detections"] else "observe-no-detections"

    detected_types = {item["type"] for item in preview["detections"]}
    missing_types = [item for item in sample.expected_types if item not in detected_types]

    if len(preview["detections"]) < sample.minimum_detections:
        return "needs-more-detections"
    if missing_types:
        return f"missing:{','.join(missing_types)}"
    return "baseline-pass"


if __name__ == "__main__":
    main()
