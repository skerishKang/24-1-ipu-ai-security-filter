from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    type: str
    label: str
    start: int
    end: int
    score: str
    note: str


@dataclass(frozen=True)
class Replacement:
    type: str
    original: str
    replaced: str
    reason: str


@dataclass(frozen=True)
class Report:
    total_detections: int
    risk_level: str
    strategy: str
    review_status: str


@dataclass(frozen=True)
class SessionMapping:
    session_id: str
    original: str
    replaced: str
    type: str


def detection_to_dict(detection: Detection) -> dict[str, str | int]:
    return {
        "type": detection.type,
        "label": detection.label,
        "start": detection.start,
        "end": detection.end,
        "score": detection.score,
        "note": detection.note,
    }


def replacement_to_dict(replacement: Replacement) -> dict[str, str]:
    return {
        "type": replacement.type,
        "original": replacement.original,
        "replaced": replacement.replaced,
        "reason": replacement.reason,
    }


def report_to_dict(report: Report) -> dict[str, str | int]:
    return {
        "total_detections": report.total_detections,
        "risk_level": report.risk_level,
        "strategy": report.strategy,
        "review_status": report.review_status,
    }
