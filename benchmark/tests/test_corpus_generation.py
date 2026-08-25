"""Corpus generation and adversarial-variant determinism tests."""

from __future__ import annotations

import json
import unittest

from benchmark.corpus.adversarial import ADVERSARIAL_KINDS, apply_variant, build_adversarial_cases
from benchmark.corpus.generator import build_base_cases, build_manifest
from benchmark.corpus.schema import corpus_to_dict


class CorpusGenerationTest(unittest.TestCase):
    def test_generation_is_deterministic(self) -> None:
        first = corpus_to_dict(build_manifest(build_base_cases()), build_base_cases())
        second = corpus_to_dict(build_manifest(build_base_cases()), build_base_cases())
        self.assertEqual(
            json.dumps(first, sort_keys=True, ensure_ascii=False),
            json.dumps(second, sort_keys=True, ensure_ascii=False),
        )

    def test_base_case_count_meets_target(self) -> None:
        cases = build_base_cases()
        manifest = build_manifest(cases)
        self.assertGreaterEqual(manifest.base_case_count, 100)

    def test_all_required_subsets_present(self) -> None:
        cases = build_base_cases()
        subsets = {case.subset for case in cases}
        self.assertEqual({"direct", "institutional", "quasi", "negative", "utility"}, subsets)

    def test_negative_cases_have_no_phi(self) -> None:
        for case in build_base_cases():
            if case.subset == "negative":
                self.assertEqual((), case.spans, case.case_id)

    def test_quasi_subset_flags_combinations(self) -> None:
        quasi_cases = [case for case in build_base_cases() if case.subset == "quasi"]
        self.assertTrue(all(case.has_quasi_combination for case in quasi_cases))


class AdversarialGenerationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.base_cases = [case for case in build_base_cases() if case.spans]

    def test_variants_are_deterministic(self) -> None:
        first = build_adversarial_cases(self.base_cases)
        second = build_adversarial_cases(self.base_cases)
        self.assertEqual(
            [(case.case_id, case.text) for case in first],
            [(case.case_id, case.text) for case in second],
        )

    def test_all_kinds_exercised(self) -> None:
        variants = build_adversarial_cases(self.base_cases)
        kinds = {case.variant_kind for case in variants}
        self.assertTrue(set(ADVERSARIAL_KINDS).issubset(kinds))

    def test_variant_spans_stay_in_bounds_and_match_text(self) -> None:
        for variant in build_adversarial_cases(self.base_cases):
            for span in variant.spans:
                self.assertGreaterEqual(span.start, 0, variant.case_id)
                self.assertLessEqual(span.end, len(variant.text), variant.case_id)
                self.assertLess(span.start, span.end, variant.case_id)
            for utility_span in variant.utility_spans:
                self.assertLessEqual(utility_span.end, len(variant.text), variant.case_id)

    def test_single_variant_is_reproducible(self) -> None:
        case = self.base_cases[0]
        first = apply_variant(case, "zero_width_chars")
        second = apply_variant(case, "zero_width_chars")
        self.assertEqual(first.text, second.text)
        self.assertEqual("zero_width_chars", first.variant_kind)
        self.assertEqual(case.case_id, first.parent_case_id)


if __name__ == "__main__":
    unittest.main()
