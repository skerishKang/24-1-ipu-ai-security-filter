"""Clinical utility retention metric tests."""

from __future__ import annotations

import unittest

from benchmark.adapters.base import CaseRunResult
from benchmark.corpus.schema import BenchmarkCase, RelationPair, UtilitySpan
from benchmark.metrics.utility import (
    category_retention,
    event_ordering_preservation,
    relation_preservation,
)


def _case_with_utilities(text: str, utilities: tuple[UtilitySpan, ...], **kwargs) -> BenchmarkCase:
    return BenchmarkCase(
        case_id=kwargs.get("case_id", "u-case"),
        subset="utility",
        text=text,
        utility_spans=utilities,
        relations=kwargs.get("relations", ()),
        event_order_markers=kwargs.get("event_order_markers", ()),
        synthetic=True,
    )


class CategoryRetentionTest(unittest.TestCase):
    def test_kept_and_redacted_spans(self) -> None:
        case = _case_with_utilities(
            "아목시실린 500mg 처방",
            (
                UtilitySpan(start=0, end=5, utility_type="medication", span_id="m1"),
                UtilitySpan(start=6, end=11, utility_type="dosage", span_id="d1"),
            ),
        )
        kept = category_retention([(case, CaseRunResult(transformed_text=case.text))], "medication")
        self.assertEqual((1.0, 1, 1), kept)
        redacted = category_retention([(case, CaseRunResult(transformed_text="[MED] 500mg 처방"))], "medication")
        self.assertEqual((0.0, 0, 1), redacted)

    def test_missing_category_is_zero_total(self) -> None:
        case = _case_with_utilities("텍스트", ())
        rate, kept, total = category_retention([(case, CaseRunResult(transformed_text="텍스트"))], "lab_value")
        self.assertEqual(0, total)
        self.assertEqual(0.0, rate)

    def test_unknown_category_type_ignored(self) -> None:
        case = _case_with_utilities(
            "아목시실린",
            (UtilitySpan(start=0, end=5, utility_type="medication", span_id="m1"),),
        )
        rate, _kept, total = category_retention([(case, CaseRunResult(transformed_text="아목시실린"))], "diagnosis")
        self.assertEqual(0, total)
        self.assertEqual(0.0, rate)


class RelationAndOrderingTest(unittest.TestCase):
    def test_relation_preserved_when_both_endpoints_survive(self) -> None:
        text = "고혈압으로 진단받고 아토르바스타틴 복용"
        case = _case_with_utilities(
            text,
            (
                UtilitySpan(start=0, end=3, utility_type="diagnosis", span_id="dx"),
                UtilitySpan(start=9, end=17, utility_type="medication", span_id="rx"),
            ),
            relations=(RelationPair(diagnosis_span_id="dx", treatment_span_id="rx"),),
        )
        rate, preserved, total = relation_preservation([(case, CaseRunResult(transformed_text=text))])
        self.assertEqual((1.0, 1, 1), (rate, preserved, total))

    def test_relation_lost_when_treatment_redacted(self) -> None:
        case = _case_with_utilities(
            "고혈압으로 진단받고 아토르바스타틴 복용",
            (
                UtilitySpan(start=0, end=3, utility_type="diagnosis", span_id="dx"),
                UtilitySpan(start=9, end=17, utility_type="medication", span_id="rx"),
            ),
            relations=(RelationPair(diagnosis_span_id="dx", treatment_span_id="rx"),),
        )
        transformed = "[MEDICATION]으로 진단받고 아토르바스타틴 복용"
        rate, preserved, total = relation_preservation([(case, CaseRunResult(transformed_text=transformed))])
        self.assertEqual(1, total)
        self.assertEqual(0.0, rate)
        self.assertEqual(0, preserved)

    def test_event_ordering_requires_all_markers(self) -> None:
        text = "먼저 검사하고 이후 약을 먹는다"
        case = _case_with_utilities(
            text,
            (),
            event_order_markers=("먼저", "이후"),
        )
        intact = event_ordering_preservation([(case, CaseRunResult(transformed_text=text))])
        self.assertEqual((1.0, 1, 1), intact)
        broken_case = _case_with_utilities(
            "먼저 검사한다",
            (),
            event_order_markers=("먼저", "이후"),
            case_id="order-broken",
        )
        broken = event_ordering_preservation([(broken_case, CaseRunResult(transformed_text="먼저 검사한다"))])
        self.assertEqual((0.0, 0, 1), broken)


if __name__ == "__main__":
    unittest.main()
