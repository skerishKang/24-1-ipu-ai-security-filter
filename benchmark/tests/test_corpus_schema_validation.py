"""Corpus schema validation tests."""

from __future__ import annotations

import unittest

from benchmark.corpus.generator import build_base_cases
from benchmark.corpus.schema import (
    BenchmarkCase,
    CorpusValidationError,
    Span,
    UtilitySpan,
    validate_case,
    validate_corpus,
)


def _valid_case() -> BenchmarkCase:
    return BenchmarkCase(
        case_id="case-001",
        subset="direct",
        text="환자 김예찬 연락처 010-1234-5678",
        spans=(
            Span(start=3, end=6, label="PATIENT_NAME", span_id="s1"),
            Span(start=11, end=23, label="PHONE", span_id="s2"),
        ),
        synthetic=True,
    )


class CorpusSchemaValidationTest(unittest.TestCase):
    def test_valid_case_passes(self) -> None:
        validate_case(_valid_case())

    def test_generated_corpus_validates(self) -> None:
        cases = build_base_cases()
        self.assertGreaterEqual(len(cases), 100)
        validate_corpus(cases)

    def test_out_of_bounds_span_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-bad-bounds",
            subset="direct",
            text="짧은 텍스트",
            spans=(Span(start=0, end=99, label="PHONE", span_id="s1"),),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_inverted_span_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-inverted",
            subset="direct",
            text="환자 김예찬 기록",
            spans=(Span(start=5, end=5, label="PATIENT_NAME", span_id="s1"),),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_unknown_label_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-unknown-label",
            subset="direct",
            text="환자 김예찬 기록",
            spans=(Span(start=3, end=6, label="NOT_A_LABEL", span_id="s1"),),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_unknown_utility_type_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-unknown-util",
            subset="utility",
            text="아목시실린 처방",
            utility_spans=(UtilitySpan(start=0, end=5, utility_type="mystery", span_id="u1"),),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_overlapping_phi_spans_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-overlap",
            subset="direct",
            text="환자 김예찬 기록",
            spans=(
                Span(start=3, end=7, label="PATIENT_NAME", span_id="s1"),
                Span(start=6, end=9, label="PHONE", span_id="s2"),
            ),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_duplicate_span_ids_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-dup-ids",
            subset="direct",
            text="환자 김예찬 연락처 010-1234-5678",
            spans=(
                Span(start=3, end=6, label="PATIENT_NAME", span_id="same"),
                Span(start=11, end=23, label="PHONE", span_id="same"),
            ),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_negative_case_with_phi_rejected(self) -> None:
        case = BenchmarkCase(
            case_id="case-negative-phi",
            subset="negative",
            text="환자 김예찬 기록",
            spans=(Span(start=3, end=6, label="PATIENT_NAME", span_id="s1"),),
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_missing_synthetic_marker_rejected(self) -> None:
        case = _valid_case()
        object.__setattr__(case, "synthetic", False)
        with self.assertRaises(CorpusValidationError):
            validate_case(case)

    def test_duplicate_case_ids_rejected(self) -> None:
        first = _valid_case()
        second = BenchmarkCase(
            case_id=first.case_id,
            subset="negative",
            text="일반 문장이다.",
            synthetic=True,
        )
        with self.assertRaises(CorpusValidationError):
            validate_corpus([first, second])


if __name__ == "__main__":
    unittest.main()
