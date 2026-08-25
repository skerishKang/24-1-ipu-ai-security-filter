"""Privacy metric correctness tests (including zero-division and duplicates)."""

from __future__ import annotations

import unittest

from benchmark.adapters.base import CaseRunResult, Prediction
from benchmark.corpus.schema import BenchmarkCase, Span
from benchmark.metrics.privacy import (
    contextual_reidentification_risk_experimental,
    entity_metrics,
    f_beta,
    negative_false_positive_stats,
    prf,
    quasi_combination_detection_rate,
    residual_direct_phi_rate,
    transform_escape_rate,
)


def _case(spans: tuple[Span, ...], *, text: str = "가나다라마바사아자차", combo: bool = False) -> BenchmarkCase:
    return BenchmarkCase(
        case_id="t-case",
        subset="direct",
        text=text,
        spans=spans,
        has_quasi_combination=combo,
        synthetic=True,
    )


class PrfMathTest(unittest.TestCase):
    def test_perfect_scores(self) -> None:
        metrics = prf(tp=5, fp=0, fn=0)
        self.assertEqual(1.0, metrics.precision)
        self.assertEqual(1.0, metrics.recall)
        self.assertEqual(1.0, metrics.f1)

    def test_zero_division_returns_zero(self) -> None:
        for tp, fp, fn in ((0, 0, 0), (0, 0, 3), (0, 4, 0)):
            metrics = prf(tp=tp, fp=fp, fn=fn)
            self.assertEqual(0.0, metrics.precision)
            self.assertEqual(0.0, metrics.recall)
            self.assertEqual(0.0, metrics.f1)

    def test_known_values(self) -> None:
        metrics = prf(tp=2, fp=2, fn=2)
        self.assertAlmostEqual(0.5, metrics.precision)
        self.assertAlmostEqual(0.5, metrics.recall)
        self.assertAlmostEqual(0.5, metrics.f1)

    def test_f2_weights_recall(self) -> None:
        value = f_beta(precision=0.5, recall=1.0, beta=2.0)
        expected = 5 * 0.5 * 1.0 / (4 * 0.5 + 1.0)
        self.assertAlmostEqual(expected, value)


class EntityMetricsTest(unittest.TestCase):
    def test_exact_match(self) -> None:
        case = _case(
            (
                Span(start=0, end=3, label="PATIENT_NAME", span_id="s1"),
                Span(start=8, end=20, label="PHONE", span_id="s2"),
            )
        )
        predictions = [Prediction(type="PERSON", start=0, end=3), Prediction(type="PHONE", start=8, end=20)]
        exact = entity_metrics(case.spans, predictions, mode="exact")
        self.assertEqual((2, 0, 0), (exact.tp, exact.fp, exact.fn))

    def test_boundary_shift_fails_exact_passes_overlap(self) -> None:
        spans = (Span(start=0, end=10, label="PHONE", span_id="s1"),)
        shifted = [Prediction(type="PHONE", start=1, end=11)]
        exact = entity_metrics(spans, shifted, mode="exact")
        self.assertEqual(0, exact.tp)
        overlap = entity_metrics(spans, shifted, mode="overlap")
        self.assertEqual(1, overlap.tp)

    def test_label_mismatch_is_not_credit(self) -> None:
        spans = (Span(start=0, end=10, label="MRN", span_id="s1"),)
        predictions = [Prediction(type="PHONE", start=0, end=10)]
        metrics = entity_metrics(spans, predictions, mode="overlap")
        self.assertEqual((0, 1, 1), (metrics.tp, metrics.fp, metrics.fn))

    def test_equivalence_table_credits_generic_baseline_types(self) -> None:
        spans = (Span(start=0, end=13, label="RRN", span_id="s1"),)
        predictions = [Prediction(type="NATIONAL_ID", start=0, end=13)]
        metrics = entity_metrics(spans, predictions, mode="exact")
        self.assertEqual(1, metrics.tp)

    def test_duplicate_predictions_counted_once(self) -> None:
        spans = (Span(start=0, end=10, label="PHONE", span_id="s1"),)
        duplicated = [
            Prediction(type="PHONE", start=0, end=10),
            Prediction(type="PHONE", start=0, end=10),
        ]
        metrics = entity_metrics(spans, duplicated, mode="exact")
        self.assertEqual(1, metrics.tp)
        self.assertEqual(0, metrics.fp)


class TransformationMetricsTest(unittest.TestCase):
    def test_residual_rate_counts_verbatim_survivors(self) -> None:
        case = _case(
            (Span(start=0, end=3, label="PATIENT_NAME", span_id="s1"),),
            text="김예찬 기록",
        )
        escaped_result = CaseRunResult(transformed_text="김예찬 기록")
        cleaned_result = CaseRunResult(transformed_text="[PERSON_01] 기록")
        rate, residual, total = residual_direct_phi_rate([(case, escaped_result)])
        self.assertEqual(1.0, rate)
        self.assertEqual((1, 1), (residual, total))
        rate, residual, total = residual_direct_phi_rate([(case, cleaned_result)])
        self.assertEqual(0.0, rate)

    def test_escape_rate_over_documents(self) -> None:
        first = _case((Span(start=0, end=3, label="PATIENT_NAME", span_id="s1"),), text="김예찬 기록")
        second = _case(
            (Span(start=6, end=18, label="PHONE", span_id="s2"),),
            text="기록 010-1111-2222",
        )
        results = [
            (first, CaseRunResult(transformed_text="[PERSON] 기록")),
            (second, CaseRunResult(transformed_text="기록 010-1111-2222")),
        ]
        rate, escaped, docs = transform_escape_rate(results)
        self.assertEqual((0.5, 1, 2), (rate, escaped, docs))

    def test_empty_inputs_are_zero_not_crash(self) -> None:
        rate, residual, total = residual_direct_phi_rate([])
        self.assertEqual((0.0, 0, 0), (rate, residual, total))


class ContextMetricsTest(unittest.TestCase):
    def test_qicdr_requires_two_correct_categories(self) -> None:
        case = _case(
            (
                Span(start=0, end=3, label="AGE", span_id="s1"),
                Span(start=4, end=5, label="SEX", span_id="s2"),
            ),
            text="45세 남",
            combo=True,
        )
        one_category = CaseRunResult(predictions=(Prediction(type="QUASI_AGE", start=0, end=3),))
        rate, hits, flagged = quasi_combination_detection_rate([(case, one_category)])
        self.assertEqual((0.0, 0, 1), (rate, hits, flagged))
        two_categories = CaseRunResult(
            predictions=(
                Prediction(type="QUASI_AGE", start=0, end=3),
                Prediction(type="QUASI_SEX", start=4, end=5),
            )
        )
        rate, hits, _flagged = quasi_combination_detection_rate([(case, two_categories)])
        self.assertEqual((1.0, 1), (rate, hits))

    def test_qicdr_false_detections_do_not_count(self) -> None:
        case = _case(
            (Span(start=0, end=3, label="AGE", span_id="s1"),),
            text="45세",
            combo=True,
        )
        wrong_span = CaseRunResult(
            predictions=(
                Prediction(type="QUASI_AGE", start=0, end=3),
                Prediction(type="QUASI_SEX", start=99, end=101),
            )
        )
        rate, hits, _flagged = quasi_combination_detection_rate([(case, wrong_span)])
        self.assertEqual((0.0, 0), (rate, hits))

    def test_contextual_risk_score_stays_bounded(self) -> None:
        case = _case(
            (
                Span(start=0, end=3, label="AGE", span_id="s1"),
                Span(start=4, end=7, label="OCCUPATION", span_id="s2"),
                Span(start=8, end=11, label="PATIENT_NAME", span_id="s3"),
            ),
            text="45세 용접공 김예찬 기록",
        )
        nothing_removed = CaseRunResult(transformed_text=case.text)
        mean, scored = contextual_reidentification_risk_experimental([(case, nothing_removed)])
        self.assertEqual(1, scored)
        self.assertGreaterEqual(mean, 0.0)
        self.assertLessEqual(mean, 1.0)


class NegativeScoringTest(unittest.TestCase):
    def test_negative_false_positive_stats(self) -> None:
        negative_case = BenchmarkCase(
            case_id="neg-1",
            subset="negative",
            text="일반 건강 문장이다.",
            synthetic=True,
        )
        clean = negative_case, CaseRunResult(transformed_text=negative_case.text)
        with_fp = negative_case, CaseRunResult(
            transformed_text=negative_case.text,
            predictions=(Prediction(type="PHONE", start=0, end=5),),
        )
        stats = negative_false_positive_stats([clean, with_fp])
        self.assertEqual(0.5, stats["document_fp_rate"])
        self.assertEqual(0.5, stats["mean_predictions_per_document"])

    def test_clean_negatives_score_zero_predictions(self) -> None:
        from benchmark.adapters.s1_generic_pii import S1GenericPiiAdapter

        adapter = S1GenericPiiAdapter()
        text = "충분한 수면과 규칙적인 운동은 만성 피로 개선에 도움이 된다."
        self.assertEqual([], adapter.detect(text))


if __name__ == "__main__":
    unittest.main()
