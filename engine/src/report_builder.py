from __future__ import annotations

from engine.src.contracts import Detection, Replacement, Report


class ReportBuilder:
    def build_report(
        self,
        detections: list[Detection],
        replacements: list[Replacement],
        strategy: str = "strict_token",
    ) -> Report:
        total = max(len(detections), len(replacements))
        risk_level = "low-risk"
        if total >= 3:
            risk_level = "high-risk"
        elif total > 0:
            risk_level = "moderate-risk"

        return Report(
            total_detections=total,
            risk_level=risk_level,
            strategy=strategy,
            review_status="review-required" if total else "clean",
        )
