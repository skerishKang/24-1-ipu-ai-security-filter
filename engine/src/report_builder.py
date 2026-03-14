from __future__ import annotations

from engine.src.contracts import Detection, Replacement, Report

_MODERATE_THRESHOLD = 1
_HIGH_THRESHOLD = 3


class ReportBuilder:
    def build_report(
        self,
        detections: list[Detection],
        replacements: list[Replacement],
        strategy: str = "strict_token",
    ) -> Report:
        total = max(len(detections), len(replacements))
        risk_level = "low-risk"
        if total >= _HIGH_THRESHOLD:
            risk_level = "high-risk"
        elif total >= _MODERATE_THRESHOLD:
            risk_level = "moderate-risk"

        return Report(
            total_detections=total,
            risk_level=risk_level,
            strategy=strategy,
            review_status="review-required" if total else "clean",
        )
