"""Corpus data contracts and validation for the B63 R0 benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field

from benchmark.corpus.taxonomy import (
    ALL_PHI_LABELS,
    LABEL_CLASS,
    UTILITY_TYPES,
    risk_tier_for,
)


class CorpusValidationError(ValueError):
    """Raised when a generated or loaded corpus case fails validation."""


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    label: str
    span_id: str


@dataclass(frozen=True)
class UtilitySpan:
    start: int
    end: int
    utility_type: str
    span_id: str


@dataclass(frozen=True)
class RelationPair:
    diagnosis_span_id: str
    treatment_span_id: str


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    subset: str
    text: str
    spans: tuple[Span, ...] = field(default=())
    utility_spans: tuple[UtilitySpan, ...] = field(default=())
    relations: tuple[RelationPair, ...] = field(default=())
    event_order_markers: tuple[str, ...] = field(default=())
    has_quasi_combination: bool = False
    variant_kind: str = "base"
    parent_case_id: str | None = None
    template_id: str = ""
    synthetic: bool = True


@dataclass(frozen=True)
class CorpusManifest:
    synthetic_only: bool
    corpus_version: str
    schema_version: str
    seed: int
    base_case_count: int
    adversarial_case_count: int
    total_case_count: int
    subset_counts: dict[str, int]


def validate_case(case: BenchmarkCase) -> None:
    _validate_synthetic_marker(case)
    _validate_unique_ids(case)
    _validate_labels(case)
    _validate_span_bounds(case)
    _validate_no_phi_overlap(case)
    _validate_utility_spans(case)
    _validate_negative_subset(case)


def validate_corpus(cases: list[BenchmarkCase]) -> None:
    if not cases:
        raise CorpusValidationError("corpus is empty")
    seen_ids: set[str] = set()
    for case in cases:
        if case.case_id in seen_ids:
            raise CorpusValidationError(f"duplicate case id: {case.case_id}")
        seen_ids.add(case.case_id)
        validate_case(case)


def _validate_synthetic_marker(case: BenchmarkCase) -> None:
    if not case.synthetic:
        raise CorpusValidationError(f"case {case.case_id} lacks synthetic marker")


def _validate_unique_ids(case: BenchmarkCase) -> None:
    phi_ids = [span.span_id for span in case.spans]
    util_ids = [span.span_id for span in case.utility_spans]
    combined = phi_ids + util_ids
    if len(combined) != len(set(combined)):
        raise CorpusValidationError(f"case {case.case_id} has duplicate span ids")


def _validate_labels(case: BenchmarkCase) -> None:
    for span in case.spans:
        if span.label not in ALL_PHI_LABELS:
            raise CorpusValidationError(
                f"case {case.case_id} has unknown PHI label {span.label}"
            )
    for span in case.utility_spans:
        if span.utility_type not in UTILITY_TYPES:
            raise CorpusValidationError(
                f"case {case.case_id} has unknown utility type {span.utility_type}"
            )


def _validate_span_bounds(case: BenchmarkCase) -> None:
    length = len(case.text)
    for span in case.spans:
        if span.start < 0 or span.end > length or span.start >= span.end:
            raise CorpusValidationError(
                f"case {case.case_id} span {span.span_id} out of bounds"
            )
    for span in case.utility_spans:
        if span.start < 0 or span.end > length or span.start >= span.end:
            raise CorpusValidationError(
                f"case {case.case_id} utility span {span.span_id} out of bounds"
            )


def _validate_no_phi_overlap(case: BenchmarkCase) -> None:
    ordered = sorted(case.spans, key=lambda item: (item.start, item.end))
    for left, right in zip(ordered, ordered[1:]):
        if right.start < left.end:
            raise CorpusValidationError(
                f"case {case.case_id} has overlapping PHI spans "
                f"{left.span_id}/{right.span_id}"
            )


def _validate_utility_spans(case: BenchmarkCase) -> None:
    ordered = sorted(case.utility_spans, key=lambda item: (item.start, item.end))
    for left, right in zip(ordered, ordered[1:]):
        if right.start < left.end:
            raise CorpusValidationError(
                f"case {case.case_id} has overlapping utility spans "
                f"{left.span_id}/{right.span_id}"
            )
    for util in ordered:
        for phi in case.spans:
            if util.start < phi.end and phi.start < util.end:
                raise CorpusValidationError(
                    f"case {case.case_id} utility span {util.span_id} overlaps "
                    f"PHI span {phi.span_id}"
                )


def _validate_negative_subset(case: BenchmarkCase) -> None:
    if case.subset == "negative" and case.spans:
        raise CorpusValidationError(
            f"negative case {case.case_id} must not carry PHI spans"
        )


def span_class(label: str) -> str:
    return LABEL_CLASS[label]


def span_risk_tier(label: str) -> str:
    return risk_tier_for(label)


def case_to_dict(case: BenchmarkCase) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "subset": case.subset,
        "text": case.text,
        "spans": [
            {
                "start": span.start,
                "end": span.end,
                "label": span.label,
                "span_id": span.span_id,
                "phi_class": span_class(span.label),
                "risk_tier": span_risk_tier(span.label),
            }
            for span in case.spans
        ],
        "utility_spans": [
            {
                "start": span.start,
                "end": span.end,
                "utility_type": span.utility_type,
                "span_id": span.span_id,
            }
            for span in case.utility_spans
        ],
        "relations": [
            {
                "diagnosis_span_id": rel.diagnosis_span_id,
                "treatment_span_id": rel.treatment_span_id,
            }
            for rel in case.relations
        ],
        "event_order_markers": list(case.event_order_markers),
        "has_quasi_combination": case.has_quasi_combination,
        "variant_kind": case.variant_kind,
        "parent_case_id": case.parent_case_id,
        "template_id": case.template_id,
        "synthetic": case.synthetic,
    }


def corpus_to_dict(manifest: CorpusManifest, cases: list[BenchmarkCase]) -> dict[str, object]:
    return {
        "manifest": {
            "synthetic_only": manifest.synthetic_only,
            "corpus_version": manifest.corpus_version,
            "schema_version": manifest.schema_version,
            "seed": manifest.seed,
            "base_case_count": manifest.base_case_count,
            "adversarial_case_count": manifest.adversarial_case_count,
            "total_case_count": manifest.total_case_count,
            "subset_counts": dict(sorted(manifest.subset_counts.items())),
        },
        "cases": [case_to_dict(case) for case in cases],
    }
