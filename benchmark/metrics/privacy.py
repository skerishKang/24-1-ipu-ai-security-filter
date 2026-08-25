"""Privacy metrics: entity-level, span-level, transformation, and context.

Label equivalence maps gold taxonomy labels to the prediction types each
system may emit for them. The table is generous toward baselines (e.g. gold
HOSPITAL_NAME accepts generic ORG detections) so no system is credited or
penalized by naming alone. It is part of the recorded schema version.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmark.adapters.base import CaseRunResult, Prediction
from benchmark.corpus.schema import BenchmarkCase, Span
from benchmark.corpus.taxonomy import (
    DIRECT_CLASS,
    LABEL_CLASS,
    RISK_TIER_HIGH,
)

LABEL_EQUIVALENCE: dict[str, frozenset[str]] = {
    "PATIENT_NAME": frozenset({"PERSON"}),
    "GUARDIAN_NAME": frozenset({"PERSON"}),
    "CLINICIAN_NAME": frozenset({"PERSON"}),
    "PHONE": frozenset({"PHONE"}),
    "EMAIL": frozenset({"EMAIL"}),
    "RRN": frozenset({"RESIDENT_REGISTRATION_NUMBER", "NATIONAL_ID", "RRN"}),
    "FOREIGN_REG_NUMBER": frozenset({"FOREIGN_REGISTRATION_NUMBER", "NATIONAL_ID", "FOREIGN_REG_NUMBER"}),
    "MRN": frozenset({"MRN", "GENERIC_ID"}),
    "INSURANCE_NUMBER": frozenset({"INSURANCE_NUMBER", "ACCOUNT_NUMBER", "GENERIC_ID"}),
    "CLINICIAN_ID": frozenset({"CLINICIAN_ID", "GENERIC_ID"}),
    "ADDRESS": frozenset({"ADDRESS"}),
    "HOSPITAL_NAME": frozenset({"HOSPITAL_NAME", "ORG"}),
    "WARD_DEPARTMENT": frozenset({"WARD_DEPARTMENT"}),
    "ORDER_ID": frozenset({"ORDER_ID", "GENERIC_ID"}),
    "EXACT_TIMESTAMP": frozenset({"EXACT_TIMESTAMP"}),
    "AGE": frozenset({"QUASI_AGE"}),
    "SEX": frozenset({"QUASI_SEX"}),
    "RARE_DISEASE": frozenset({"QUASI_RARE_DISEASE"}),
    "RARE_PROCEDURE": frozenset({"QUASI_RARE_PROCEDURE"}),
    "DETAILED_REGION": frozenset({"QUASI_DETAILED_REGION"}),
    "OCCUPATION": frozenset({"QUASI_OCCUPATION"}),
    "ADMIT_DISCHARGE_DATE": frozenset({"QUASI_ADMIT_DISCHARGE_DATE"}),
    "UNIQUE_EVENT": frozenset({"QUASI_UNIQUE_EVENT"}),
}

QUASI_TYPE_TO_GOLD: dict[str, str] = {
    "QUASI_AGE": "AGE",
    "QUASI_SEX": "SEX",
    "QUASI_RARE_DISEASE": "RARE_DISEASE",
    "QUASI_RARE_PROCEDURE": "RARE_PROCEDURE",
    "QUASI_DETAILED_REGION": "DETAILED_REGION",
    "QUASI_OCCUPATION": "OCCUPATION",
    "QUASI_ADMIT_DISCHARGE_DATE": "ADMIT_DISCHARGE_DATE",
    "QUASI_UNIQUE_EVENT": "UNIQUE_EVENT",
}


@dataclass(frozen=True)
class EntityMetrics:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int


def prf(tp: int, fp: int, fn: int) -> EntityMetrics:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return EntityMetrics(precision=precision, recall=recall, f1=f1, tp=tp, fp=fp, fn=fn)


def f_beta(precision: float, recall: float, beta: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    beta_sq = beta * beta
    return (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)


def _dedupe(predictions: tuple[Prediction, ...] | list[Prediction]) -> list[Prediction]:
    seen: set[tuple[str, int, int]] = set()
    unique: list[Prediction] = []
    for prediction in predictions:
        key = (prediction.type, prediction.start, prediction.end)
        if key not in seen:
            seen.add(key)
            unique.append(prediction)
    return sorted(unique, key=lambda item: (item.start, item.end, item.type))


def _accepted(gold_label: str, prediction_type: str) -> bool:
    return prediction_type in LABEL_EQUIVALENCE.get(gold_label, frozenset({gold_label}))


def _match_exact(
    golds: list[Span], predictions: list[Prediction]
) -> list[tuple[Span, Prediction]]:
    """Exact matching requires identical boundaries plus an equivalent label.

    Several gold labels share one prediction type, so matching resolves via a
    greedy left-to-right scan with each gold usable at most once.
    """
    pairs: list[tuple[Span, Prediction]] = []
    used: set[int] = set()
    for prediction in predictions:
        for gold_position, gold in enumerate(golds):
            if gold_position in used:
                continue
            if gold.start == prediction.start and gold.end == prediction.end and _accepted(gold.label, prediction.type):
                pairs.append((gold, prediction))
                used.add(gold_position)
                break
    return pairs


def _match_overlap(
    golds: list[Span], predictions: list[Prediction]
) -> list[tuple[Span, Prediction]]:
    pairs: list[tuple[Span, Prediction]] = []
    used: set[int] = set()
    for prediction in predictions:
        best_gold_position = -1
        best_overlap = 0
        for gold_position, gold in enumerate(golds):
            if gold_position in used:
                continue
            if not _accepted(gold.label, prediction.type):
                continue
            overlap = min(gold.end, prediction.end) - max(gold.start, prediction.start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_gold_position = gold_position
        if best_overlap > 0:
            pairs.append((golds[best_gold_position], prediction))
            used.add(best_gold_position)
    return pairs


def entity_metrics(
    gold_spans: tuple[Span, ...],
    predictions: tuple[Prediction, ...] | list[Prediction],
    *,
    mode: str = "exact",
    phi_class: str | None = None,
    risk_tier_high_only: bool = False,
) -> EntityMetrics:
    """Entity P/R/F1 over gold spans filtered by class/tier when requested."""
    from benchmark.corpus.taxonomy import risk_tier_for

    golds = [
        span
        for span in gold_spans
        if (phi_class is None or LABEL_CLASS[span.label] == phi_class)
        and (not risk_tier_high_only or risk_tier_for(span.label) == RISK_TIER_HIGH)
    ]
    unique_predictions = _dedupe(predictions)
    matcher = _match_exact if mode == "exact" else _match_overlap
    pairs = matcher(golds, unique_predictions)
    return prf(len(pairs), len(unique_predictions) - len(pairs), len(golds) - len(pairs))


def high_risk_f2(
    gold_spans: tuple[Span, ...],
    predictions: tuple[Prediction, ...] | list[Prediction],
    *,
    mode: str = "exact",
) -> float:
    metrics = entity_metrics(gold_spans, predictions, mode=mode, risk_tier_high_only=True)
    return f_beta(metrics.precision, metrics.recall, beta=2.0)


# ---------------------------------------------------------------------------
# Transformation metrics (verbatim-presence conservative proxies)
# ---------------------------------------------------------------------------


def residual_span_texts(case: BenchmarkCase, transformed_text: str) -> list[Span]:
    needle_source = case.text
    return [
        span
        for span in case.spans
        if needle_source[span.start : span.end] in transformed_text
    ]


def residual_direct_phi_rate(cases_results: list[tuple[BenchmarkCase, CaseRunResult]]) -> tuple[float, int, int]:
    total_direct = 0
    residual_direct = 0
    for case, result in cases_results:
        residuals = residual_span_texts(case, result.transformed_text)
        direct_residuals = [s for s in residuals if LABEL_CLASS[s.label] == DIRECT_CLASS]
        total_direct += sum(1 for s in case.spans if LABEL_CLASS[s.label] == DIRECT_CLASS)
        residual_direct += len(direct_residuals)
    rate = residual_direct / total_direct if total_direct else 0.0
    return rate, residual_direct, total_direct


def residual_high_risk_phi_rate(cases_results: list[tuple[BenchmarkCase, CaseRunResult]]) -> tuple[float, int, int]:
    total = 0
    residual = 0
    for case, result in cases_results:
        residuals = residual_span_texts(case, result.transformed_text)
        high_residuals = [s for s in residuals if _is_high_risk(s)]
        total += sum(1 for s in case.spans if _is_high_risk(s))
        residual += len(high_residuals)
    rate = residual / total if total else 0.0
    return rate, residual, total


def transform_escape_rate(cases_results: list[tuple[BenchmarkCase, CaseRunResult]]) -> tuple[float, int, int]:
    documents = [pair for pair in cases_results if any(_is_high_risk(s) for s in pair[0].spans)]
    escaped = 0
    for case, result in documents:
        residuals = residual_span_texts(case, result.transformed_text)
        if any(_is_high_risk(s) for s in residuals):
            escaped += 1
    rate = escaped / len(documents) if documents else 0.0
    return rate, escaped, len(documents)


def _is_high_risk(span: Span) -> bool:
    from benchmark.corpus.taxonomy import risk_tier_for

    return risk_tier_for(span.label) == RISK_TIER_HIGH


# ---------------------------------------------------------------------------
# Context metrics
# ---------------------------------------------------------------------------


def _correct_quasi_categories(case: BenchmarkCase, result: CaseRunResult) -> set[str]:
    detected: set[str] = set()
    for prediction in _dedupe(result.predictions):
        gold_label = QUASI_TYPE_TO_GOLD.get(prediction.type)
        if gold_label is None:
            continue
        for span in case.spans:
            if span.label == gold_label and span.start < prediction.end and prediction.start < span.end:
                detected.add(gold_label)
                break
    return detected


def quasi_combination_detection_rate(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> tuple[float, int, int]:
    flagged = [(case, result) for case, result in cases_results if case.has_quasi_combination]
    hits = 0
    for case, result in flagged:
        if len(_correct_quasi_categories(case, result)) >= 2:
            hits += 1
    rate = hits / len(flagged) if flagged else 0.0
    return rate, hits, len(flagged)


def contextual_reidentification_risk_experimental(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> tuple[float, int]:
    """EXPERIMENTAL proxy: mean fraction of quasi categories left verbatim.

    Label semantics are unstable; treat this number as exploratory only.
    """
    scores: list[float] = []
    for case, result in cases_results:
        quasi_spans = [s for s in case.spans if LABEL_CLASS[s.label] == "quasi"]
        if not quasi_spans:
            continue
        categories_present = {s.label for s in quasi_spans}
        residuals = residual_span_texts(case, result.transformed_text)
        categories_surviving = {s.label for s in residuals} & categories_present
        scores.append(len(categories_surviving) / len(categories_present))
    mean = sum(scores) / len(scores) if scores else 0.0
    return mean, len(scores)


def residual_rate_by_label(
    cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> dict[str, dict[str, int | float]]:
    """Per-gold-label residual breakdown (verbatim-presence proxy)."""
    totals: dict[str, int] = {}
    survivors: dict[str, int] = {}
    for case, result in cases_results:
        residual_set = {span.span_id for span in residual_span_texts(case, result.transformed_text)}
        for span in case.spans:
            totals[span.label] = totals.get(span.label, 0) + 1
            if span.span_id in residual_set:
                survivors[span.label] = survivors.get(span.label, 0) + 1
    breakdown: dict[str, dict[str, int | float]] = {}
    for label in sorted(totals):
        total = totals[label]
        survived = survivors.get(label, 0)
        breakdown[label] = {
            "total": total,
            "survived": survived,
            "rate": round(survived / total, 4) if total else 0.0,
        }
    return breakdown


def negative_false_positive_stats(
    negative_cases_results: list[tuple[BenchmarkCase, CaseRunResult]],
) -> dict[str, float]:
    documents_with_fp = sum(1 for _, result in negative_cases_results if result.predictions)
    total_predictions = sum(len(result.predictions) for _, result in negative_cases_results)
    count = len(negative_cases_results)
    return {
        "documents_with_predictions": float(documents_with_fp),
        "document_fp_rate": documents_with_fp / count if count else 0.0,
        "mean_predictions_per_document": total_predictions / count if count else 0.0,
    }
