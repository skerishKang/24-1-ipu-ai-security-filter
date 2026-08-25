"""Clinical utility retention metrics.

Retention(category) = share of gold utility spans of that category whose
verbatim text still appears in the transformed output. This measures textual
preservation of clinically important content, not downstream task quality.
"""

from __future__ import annotations

from benchmark.adapters.base import CaseRunResult
from benchmark.corpus.schema import BenchmarkCase
from benchmark.corpus.taxonomy import UTILITY_TYPES


def category_retention(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
    category: str,
) -> tuple[float, int, int]:
    kept = 0
    total = 0
    for case, result in cases_results:
        for span in case.utility_spans:
            if span.utility_type != category:
                continue
            total += 1
            if case.text[span.start : span.end] in result.transformed_text:
                kept += 1
    rate = kept / total if total else 0.0
    return rate, kept, total


def all_category_retentions(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> dict[str, tuple[float, int, int]]:
    return {category: category_retention(cases_results, category) for category in UTILITY_TYPES}


def relation_preservation(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> tuple[float, int, int]:
    """Share of diagnosis-treatment relations where both endpoint texts survive."""
    total = 0
    preserved = 0
    span_by_id: dict[str, tuple[int, int]] = {}
    for case, result in cases_results:
        span_by_id.clear()
        for span in case.utility_spans:
            span_by_id[span.span_id] = (span.start, span.end)
        for relation in case.relations:
            total += 1
            diagnosis_range = span_by_id.get(relation.diagnosis_span_id)
            treatment_range = span_by_id.get(relation.treatment_span_id)
            if diagnosis_range is None or treatment_range is None:
                continue
            diagnosis_text = case.text[diagnosis_range[0] : diagnosis_range[1]]
            treatment_text = case.text[treatment_range[0] : treatment_range[1]]
            if diagnosis_text in result.transformed_text and treatment_text in result.transformed_text:
                preserved += 1
    rate = preserved / total if total else 0.0
    return rate, preserved, total


def event_ordering_preservation(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> tuple[float, int, int]:
    """Share of event-ordering cases where every ordered marker survives."""
    total = 0
    preserved = 0
    for case, result in cases_results:
        if not case.event_order_markers:
            continue
        total += 1
        if all(marker in result.transformed_text for marker in case.event_order_markers):
            preserved += 1
    rate = preserved / total if total else 0.0
    return rate, preserved, total


UTILITY_CATEGORIES = UTILITY_TYPES
