from __future__ import annotations

from engine.src.contracts import (
    Detection,
    Replacement,
    detection_to_dict,
    replacement_to_dict,
    report_to_dict,
)
from engine.src.detector import RegexDetector
from engine.src.report_builder import ReportBuilder
from engine.src.replacer import TokenReplacer
from engine.src.restorer import SessionRestorer
from engine.src.session_store import InMemorySessionStore


class ManualPreviewEngine:
    def __init__(self, session_store: InMemorySessionStore | None = None) -> None:
        self.session_store = session_store or InMemorySessionStore()
        self.detector = RegexDetector()
        self.replacer = TokenReplacer(self.session_store)
        self.restorer = SessionRestorer(self.session_store)
        self.report_builder = ReportBuilder()

    def detect(
        self,
        content: str,
        content_type: str = "text",
        policy: str = "default",
    ) -> list[dict[str, str | int | float]]:
        detections = self.detector.detect(content, content_type=content_type, policy=policy)
        return [detection_to_dict(item) for item in detections]

    def replace(
        self,
        content: str,
        detections: list[dict[str, str | int | float]],
        session_id: str,
        strategy: str = "strict_token",
    ) -> tuple[str, list[dict[str, str]]]:
        typed_detections = self.detector.detect(content) if not detections else [
            self._coerce_detection(item) for item in detections
        ]
        replaced_text, replacements = self.replacer.replace(
            content=content,
            detections=typed_detections,
            session_id=session_id,
            strategy=strategy,
        )
        return replaced_text, [replacement_to_dict(item) for item in replacements]

    def restore(self, content: str, session_id: str) -> str:
        return self.restorer.restore(content, session_id)

    def build_report(
        self,
        detections: list[dict[str, str | int | float]],
        replacements: list[dict[str, str]],
        strategy: str = "strict_token",
    ) -> dict[str, str | int]:
        typed_detections = [self._coerce_detection(item) for item in detections]
        typed_replacements = [self._coerce_replacement(item) for item in replacements]
        report = self.report_builder.build_report(
            detections=typed_detections,
            replacements=typed_replacements,
            strategy=strategy,
        )
        return report_to_dict(report)

    def manual_preview(
        self,
        content: str,
        session_id: str,
        content_type: str = "text",
        policy: str = "default",
        strategy: str | None = None,
    ) -> dict[str, object]:
        effective_strategy = self._resolve_strategy(policy=policy, strategy=strategy)
        detections = self.detect(content, content_type=content_type, policy=policy)
        replaced_text, replacements = self.replace(
            content=content,
            detections=detections,
            session_id=session_id,
            strategy=effective_strategy,
        )
        report = self.build_report(detections, replacements, strategy=effective_strategy)
        return {
            "session_id": session_id,
            "original_text": content,
            "replaced_text": replaced_text,
            "detections": detections,
            "replacements": replacements,
            "report": report,
            "copy_ready_prompt": self._build_copy_ready_prompt(replaced_text, report),
        }

    def _resolve_strategy(self, policy: str, strategy: str | None) -> str:
        if strategy is not None:
            return strategy
        if policy == "strict_token":
            return "strict_token"
        return "alias"

    def _build_copy_ready_prompt(
        self,
        replaced_text: str,
        report: dict[str, str | int],
    ) -> str:
        return "\n".join(
            [
                "[IPU Manual Mode Prompt]",
                "아래 내용은 민감정보가 세션 기반 토큰으로 치환된 상태입니다.",
                "토큰을 유지한 채 문맥만 분석하고, 토큰의 실제 의미를 추정하지 마세요.",
                "",
                "[Security Review]",
                f"risk_level: {report['risk_level']}",
                f"review_status: {report['review_status']}",
                "",
                "[Redacted Input]",
                replaced_text,
            ]
        )

    def _coerce_detection(self, item: dict[str, str | int | float]):
        return Detection(
            type=str(item["type"]),
            label=str(item["label"]),
            start=int(item["start"]),
            end=int(item["end"]),
            score=float(item["score"]),
            note=str(item["note"]),
        )

    def _coerce_replacement(self, item: dict[str, str]):
        return Replacement(
            type=item["type"],
            original=item["original"],
            replaced=item["replaced"],
            reason=item["reason"],
        )
