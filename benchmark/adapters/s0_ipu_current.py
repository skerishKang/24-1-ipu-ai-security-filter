"""S0 = IPU_CURRENT adapter.

Read-only usage of the existing production engine interfaces:
``RegexDetector.detect(policy="strict_token")`` and
``ManualPreviewEngine.manual_preview`` for token replacement.
No production code path is modified.
"""

from __future__ import annotations

from benchmark.adapters.base import Prediction, SystemAdapter


class S0IpuCurrentAdapter(SystemAdapter):
    system_id = "S0_IPU_CURRENT"

    def __init__(self) -> None:
        from engine.src.detector import RegexDetector
        from engine.src.manual_preview_engine import ManualPreviewEngine

        self._detector = RegexDetector()
        self._engine = ManualPreviewEngine()

    def detect(self, text: str) -> list[Prediction]:
        detections = self._detector.detect(text, content_type="text", policy="strict_token")
        return [
            Prediction(type=item.type, start=int(item.start), end=int(item.end))
            for item in detections
        ]

    def transform(self, text: str, case_key: str) -> str:
        preview = self._engine.manual_preview(
            content=text,
            session_id=f"b63r0-s0-{case_key}",
            content_type="text",
            policy="strict_token",
        )
        return str(preview["replaced_text"])
