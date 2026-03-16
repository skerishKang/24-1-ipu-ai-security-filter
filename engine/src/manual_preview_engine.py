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
from engine.src.session_store import InMemorySessionStore, SessionStore


class ManualPreviewEngine:
    def __init__(self, session_store: SessionStore | None = None) -> None:
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
        detections: list[dict[str, str | int | float]] | None,
        session_id: str,
        strategy: str = "strict_token",
    ) -> tuple[str, list[dict[str, str]]]:
        typed_detections = (
            self.detector.detect(content)
            if detections is None
            else [self._coerce_detection(item) for item in detections]
        )
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
        task_type: str | None = None,
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
        readiness = self.check_send_readiness(replaced_text, detections, report, task_type)
        return {
            "session_id": session_id,
            "original_text": content,
            "replaced_text": replaced_text,
            "detections": detections,
            "replacements": replacements,
            "report": report,
            "task_type": task_type,
            "readiness": readiness,
            "copy_ready_prompt": self._build_copy_ready_prompt(replaced_text, report, task_type),
        }

    def _resolve_strategy(self, policy: str, strategy: str | None) -> str:
        if strategy is not None:
            return strategy
        if policy == "strict_token":
            return "strict_token"
        return "alias"

    TASK_GUIDES = {
        "summarize": "아래 문서의 핵심 내용을 3~5문장 이내로 요약해 주세요.",
        "risk_review": "아래 문서에서 확인되는 잠재적 리스크와 문제점을 검토하고 정리해 주세요.",
        "action_items": "아래 문서에서 수행해야 할 작업이나 액션 아이템을 추출해 주세요.",
    }

    RESPONSE_FORMAT_GUIDES = {
        "summarize": "요약은 bullet point 형태ではなく、단락으로 작성해 주세요.",
        "risk_review": "리스크 검토는 항목별로 (1) 리스크 내용 (2) 심각도 (3) 권장 조치 형태로 작성해 주세요.",
        "action_items": "액션 아이템은 체크리스트 형태로 작성해 주세요.",
    }

    def _build_copy_ready_prompt(
        self,
        replaced_text: str,
        report: dict[str, str | int],
        task_type: str | None = None,
    ) -> str:
        lines = [
            "[IPU Manual Mode Prompt]",
            "아래 내용은 민감정보가 세션 기반 토큰으로 치환된 상태입니다.",
            "토큰을 유지한 채 문맥만 분석하고, 토큰의 실제 의미를 추정하지 마세요.",
            "",
            "[Security Review]",
            f"risk_level: {report['risk_level']}",
            f"review_status: {report['review_status']}",
            "",
        ]
        
        if task_type and task_type in self.TASK_GUIDES:
            lines.extend([
                "[Task]",
                self.TASK_GUIDES[task_type],
                "",
                "[Response Format]",
                self.RESPONSE_FORMAT_GUIDES[task_type],
                "",
            ])
        
        lines.extend([
            "[Redacted Input]",
            replaced_text,
        ])
        
        return "\n".join(lines)

    def check_send_readiness(
        self,
        replaced_text: str,
        detections: list[dict],
        report: dict[str, str | int],
        task_type: str | None = None,
    ) -> dict[str, object]:
        total_detections = len(detections)
        risk_level = report.get("risk_level", "low-risk")
        review_status = report.get("review_status", "clean")
        
        remaining_risks = []
        
        if total_detections == 0:
            ready_to_send = True
            status = "pass"
            reason = "탐지된 민감정보가 없습니다. 외부 전송이 안전합니다."
        elif review_status == "clean":
            ready_to_send = True
            status = "pass"
            reason = "검토 상태가 clean입니다."
        elif risk_level == "high-risk":
            ready_to_send = False
            status = "fail"
            remaining_risks = [d["type"] for d in detections]
            reason = f"높은 위험도(high-risk)로 탐지된 {total_detections}개의 민감정보를 먼저 검토해야 합니다."
        elif risk_level == "moderate-risk":
            ready_to_send = False
            status = "review-required"
            remaining_risks = [d["type"] for d in detections]
            reason = f"중간 위험도(moderate-risk)로 {total_detections}개의 민감정보가 탐지되었습니다. 전송 전 검토가 필요합니다."
        else:
            ready_to_send = False
            status = "review-required"
            remaining_risks = [d["type"] for d in detections]
            reason = f"{total_detections}개의 민감정보가 탐지되었습니다. 전송 전 검토가 필요합니다."
        
        return {
            "ready_to_send": ready_to_send,
            "review_status": status,
            "reason": reason,
            "remaining_risks": list(set(remaining_risks)),
            "detection_count": total_detections,
            "risk_level": risk_level,
        }

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
