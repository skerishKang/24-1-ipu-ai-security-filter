from __future__ import annotations

from typing import Any

from engine.src.contracts import (
    Detection,
    Replacement,
    SessionMapping,
    detection_to_dict,
    replacement_to_dict,
    report_to_dict,
)
from engine.src.detector import RegexDetector
from engine.src.local_rewriter import OllamaLocalRewriter, PlaceholderLocalRewriter
from engine.src.replacer import TokenReplacer
from engine.src.report_builder import ReportBuilder
from engine.src.restorer import SessionRestorer
from engine.src.session_store import InMemorySessionStore, SessionStore


class ManualPreviewEngine:
    TASK_GUIDES = {
        "summarize": "아래 문서를 3~5문장으로 요약해 주세요.",
        "risk_review": "아래 문서에서 확인되는 주요 리스크와 검토 포인트를 정리해 주세요.",
        "action_items": "아래 문서에서 실행이 필요한 액션 아이템만 추려 주세요.",
    }

    RESPONSE_FORMAT_GUIDES = {
        "summarize": "핵심만 bullet point 형태로 간결하게 작성해 주세요.",
        "risk_review": "항목별로 리스크 내용, 심각도, 권장 조치를 구분해 작성해 주세요.",
        "action_items": "체크리스트 형태로 짧고 명확하게 작성해 주세요.",
    }

    def __init__(
        self,
        session_store: SessionStore | None = None,
        local_rewriter: Any | None = None,
    ) -> None:
        self.session_store = session_store or InMemorySessionStore()
        self.detector = RegexDetector()
        self.replacer = TokenReplacer(self.session_store)
        self.restorer = SessionRestorer(self.session_store)
        self.report_builder = ReportBuilder()
        self.local_rewriter = local_rewriter or PlaceholderLocalRewriter()

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
        if detections is not None and len(detections) == 0:
            # Defense-in-depth: the strict-residual scan is run in
            # ``manual_preview`` but a direct ``replace()`` call with an empty
            # list would skip it and yield ``ready_to_send=true``. Refuse
            # explicitly so callers cannot weaponize this path.
            raise ValueError(
                "replace() requires either detections=None (auto-detect) or a "
                "non-empty detection list; empty lists are not accepted"
            )
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

    def replace_with_local_rewrite(
        self,
        content: str,
        detections: list[dict[str, str | int | float]] | None,
        session_id: str,
    ) -> tuple[str, list[dict[str, str]], dict[str, object]]:
        typed_detections = (
            self.detector.detect(content, policy="strict_token")
            if detections is None
            else [self._coerce_detection(item) for item in detections]
        )
        rewrite_result = self.local_rewriter.rewrite(content, typed_detections)
        replaced_text = self._apply_custom_replacements(
            content=content,
            detections=typed_detections,
            replacements=rewrite_result.replacements,
            session_id=session_id,
        )
        metadata = {
            "engine": self.local_rewriter.engine_name,
            "used_fallback": rewrite_result.used_fallback,
        }
        return (
            replaced_text,
            [replacement_to_dict(item) for item in rewrite_result.replacements],
            metadata,
        )

    def restore(
        self,
        content: str,
        session_id: str,
        *,
        token: str,
        owner_hash: str,
    ) -> str:
        return self.restorer.restore(
            content,
            session_id,
            token=token,
            owner_hash=owner_hash,
        )

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
        detection_policy = "strict_token" if policy == "local_rewrite" else policy
        detections = self.detect(content, content_type=content_type, policy=detection_policy)
        strict_readiness_detections = self.detect(content, content_type=content_type, policy="strict_token")
        strict_residual_detections = self._find_strict_residual_detections(
            strict_detections=strict_readiness_detections,
            displayed_detections=detections,
        )
        rewrite_metadata: dict[str, object] = {}
        if detections:
            if effective_strategy == "local_rewrite":
                replaced_text, replacements, rewrite_metadata = self.replace_with_local_rewrite(
                    content=content,
                    detections=detections,
                    session_id=session_id,
                )
            else:
                replaced_text, replacements = self.replace(
                    content=content,
                    detections=detections,
                    session_id=session_id,
                    strategy=effective_strategy,
                )
        else:
            # No detections: return the original content untouched. This is the
            # legitimate "nothing to mask" path and is distinct from the bypass
            # attempt (an empty detection list passed to ``replace()``), which
            # ``replace()`` now refuses explicitly.
            replaced_text = content
            replacements = []
            rewrite_metadata = {}
        report = self.build_report(detections, replacements, strategy=effective_strategy)
        readiness = self.check_send_readiness(
            replaced_text,
            detections,
            report,
            task_type,
            strict_residual_detections=strict_residual_detections,
        )
        return {
            "session_id": session_id,
            "original_text": content,
            "replaced_text": replaced_text,
            "detections": detections,
            "replacements": replacements,
            "report": report,
            "rewrite_metadata": rewrite_metadata,
            "task_type": task_type,
            "readiness": readiness,
            "copy_ready_prompt": self._build_copy_ready_prompt(replaced_text, report, task_type),
        }

    def _resolve_strategy(self, policy: str, strategy: str | None) -> str:
        if strategy is not None:
            return strategy
        if policy == "local_rewrite":
            return "local_rewrite"
        if policy == "strict_token":
            return "strict_token"
        return "alias"

    def _find_strict_residual_detections(
        self,
        strict_detections: list[dict[str, str | int | float]],
        displayed_detections: list[dict[str, str | int | float]],
    ) -> list[dict[str, str | int | float]]:
        residual: list[dict[str, str | int | float]] = []
        for strict_detection in strict_detections:
            if any(self._detections_overlap(strict_detection, displayed_detection) for displayed_detection in displayed_detections):
                continue
            residual.append(strict_detection)
        return residual

    def _detections_overlap(
        self,
        left: dict[str, str | int | float],
        right: dict[str, str | int | float],
    ) -> bool:
        return int(left["start"]) < int(right["end"]) and int(right["start"]) < int(left["end"])

    def _apply_custom_replacements(
        self,
        content: str,
        detections: list[Detection],
        replacements: list[Replacement],
        session_id: str,
    ) -> str:
        replaced_text = content
        planned: list[tuple[int, int, str]] = []

        for detection, replacement in zip(detections, replacements, strict=True):
            planned.append((detection.start, detection.end, replacement.replaced))
            self.session_store.save_mapping(
                session_id,
                SessionMapping(
                    session_id=session_id,
                    original=detection.label,
                    replaced=replacement.replaced,
                    type=detection.type,
                ),
            )

        # Defensive non-overlap check: if a caller hands us already-coerced
        # detections that overlap, the right-to-left slice below would
        # produce a string whose length disagrees with the layout the
        # restorer expects. Drop the offending spans and warn so a
        # regression in the upstream detector does not silently corrupt
        # the user's content.
        planned.sort(key=lambda item: item[0])
        non_overlapping: list[tuple[int, int, str]] = []
        last_end = -1
        for start, end, value in planned:
            if start < last_end:
                continue
            non_overlapping.append((start, end, value))
            last_end = end
        planned = non_overlapping

        for start, end, value in sorted(planned, key=lambda item: item[0], reverse=True):
            replaced_text = replaced_text[:start] + value + replaced_text[end:]

        return replaced_text

    def _build_copy_ready_prompt(
        self,
        replaced_text: str,
        report: dict[str, str | int],
        task_type: str | None = None,
    ) -> str:
        lines = [
            "[IPU External Transfer Text]",
            "아래 내용은 민감정보가 비식별 처리된 상태입니다.",
            "토큰이나 일반화 표현의 실제 원문을 추정하지 말고, 현재 보이는 텍스트만 기준으로 작업해 주세요.",
            "",
            "[Review Status]",
            f"risk_level: {report['risk_level']}",
            f"review_status: {report['review_status']}",
            "",
        ]

        if task_type and task_type in self.TASK_GUIDES:
            lines.extend([
                "[Requested Task]",
                self.TASK_GUIDES[task_type],
                "",
                "[Response Format]",
                self.RESPONSE_FORMAT_GUIDES[task_type],
                "",
            ])

        lines.extend([
            "[Sanitized Text]",
            replaced_text,
        ])

        return "\n".join(lines)

    def check_send_readiness(
        self,
        replaced_text: str,
        detections: list[dict],
        report: dict[str, str | int],
        task_type: str | None = None,
        *,
        strict_residual_detections: list[dict] | None = None,
    ) -> dict[str, object]:
        strict_residual_detections = strict_residual_detections or []
        display_detection_count = len(detections)
        strict_residual_count = len(strict_residual_detections)
        total_detections = display_detection_count + strict_residual_count
        risk_level = report.get("risk_level", "low-risk")
        review_status = report.get("review_status", "clean")

        remaining_risks: list[str] = []

        if strict_residual_count:
            residual_risk_level = "high-risk" if strict_residual_count >= 3 else "moderate-risk"
            if risk_level == "high-risk" or residual_risk_level == "high-risk":
                risk_level = "high-risk"
                status = "fail"
            else:
                risk_level = "moderate-risk"
                status = "review-required"
            ready_to_send = False
            remaining_risks = [d["type"] for d in detections] + [d["type"] for d in strict_residual_detections]
            reason = f"strict residual scan에서 {strict_residual_count}개의 추가 민감정보가 탐지되었습니다. 전달 전 검토가 필요합니다."
        elif total_detections == 0:
            ready_to_send = True
            status = "pass"
            reason = "탐지된 민감정보가 없습니다. 현재 상태로 전달 가능합니다."
        elif review_status == "clean":
            ready_to_send = True
            status = "pass"
            reason = "검토 상태가 clean입니다."
        elif risk_level == "high-risk":
            ready_to_send = False
            status = "fail"
            remaining_risks = [d["type"] for d in detections]
            reason = f"high-risk 상태로 {total_detections}개의 민감정보가 탐지되었습니다. 전달 전 추가 검토가 필요합니다."
        elif risk_level == "moderate-risk":
            ready_to_send = False
            status = "review-required"
            remaining_risks = [d["type"] for d in detections]
            reason = f"moderate-risk 상태로 {total_detections}개의 민감정보가 탐지되었습니다. 전달 전 검토가 필요합니다."
        else:
            ready_to_send = False
            status = "review-required"
            remaining_risks = [d["type"] for d in detections]
            reason = f"{total_detections}개의 민감정보가 탐지되었습니다. 전달 전 검토가 필요합니다."

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
