"""System adapter tests (S0/S1/S3 behavior and failure isolation)."""

from __future__ import annotations

import unittest

from benchmark.adapters.base import AdapterStats, SystemAdapter, record_stats, run_case
from benchmark.adapters.s1_generic_pii import S1GenericPiiAdapter
from benchmark.adapters.s3_b63_hybrid import S3B63HybridAdapter

CLINICAL_TEXT = (
    "외래 기록. 김예찬(45세 여) 환자가 한빛대학교병원에 접수했다. "
    "연락처 010-2345-6789, 주소 서울특별시 예시구 예시로 123. "
    "환자번호: M2026-00341. 담당 유원준 원장(직원 ID DR-10247)."
)


class S0AdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        from benchmark.adapters.s0_ipu_current import S0IpuCurrentAdapter

        self.adapter = S0IpuCurrentAdapter()

    def test_detects_core_contact_entities(self) -> None:
        predictions = self.adapter.detect(CLINICAL_TEXT)
        detected_text = {CLINICAL_TEXT[p.start : p.end] for p in predictions}
        self.assertIn("010-2345-6789", detected_text)

    def test_transform_replaces_detected_phone(self) -> None:
        transformed = self.adapter.transform("연락처 010-2345-6789 확인", "s0-test")
        self.assertNotIn("010-2345-6789", transformed)
        self.assertIn("[PHONE_", transformed)

    def test_transform_without_detections_returns_original(self) -> None:
        text = "민감정보가 없는 일반 문장이다."
        self.assertEqual(text, self.adapter.transform(text, "s0-clean"))


class S1AdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = S1GenericPiiAdapter()

    def test_detects_generic_types(self) -> None:
        predictions = self.adapter.detect(CLINICAL_TEXT)
        types = {p.type for p in predictions}
        self.assertTrue({"PHONE", "ADDRESS"}.issubset(types), types)

    def test_national_id_shape_matches_rrn_gold_equivalence(self) -> None:
        predictions = self.adapter.detect("주민번호 901010-1234567 기재")
        self.assertTrue(any(p.type == "NATIONAL_ID" for p in predictions))

    def test_transform_tokens_are_deterministic(self) -> None:
        first = self.adapter.transform(CLINICAL_TEXT, "k1")
        second = self.adapter.transform(CLINICAL_TEXT, "k2")
        self.assertEqual(first, second)

    def test_luhn_guard_blocks_random_digits(self) -> None:
        self.assertEqual([], self.adapter.detect("1234567812345678 는 카드가 아니다"))


class S3AdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = S3B63HybridAdapter()

    def test_detects_clinical_institutional_entities(self) -> None:
        found = {(p.type, CLINICAL_TEXT[p.start : p.end]) for p in self.adapter.detect(CLINICAL_TEXT)}
        expected_types = {"HOSPITAL_NAME", "MRN", "CLINICIAN_NAME", "CLINICIAN_ID", "ADDRESS"}
        self.assertTrue(expected_types.issubset({t for t, _v in found}), found)

    def test_quasi_categories_reported(self) -> None:
        categories = self.adapter.quasi_categories(CLINICAL_TEXT)
        self.assertIn("QUASI_AGE", categories)
        self.assertIn("QUASI_SEX", categories)

    def test_p2_keeps_quasi_verbatim_and_p1_redacts_it(self) -> None:
        quasi_text = "45세 남 환자"
        p2 = self.adapter.transform(quasi_text, "policy-test")
        p1 = self.adapter.transform_p1_max_redaction(quasi_text)
        self.assertIn("45세", p2)
        self.assertNotIn("45세", p1)

    def test_utility_content_preserved_by_default(self) -> None:
        utility_text = "아목시실린 500mg을 하루 3회 식후 경구 투여한다."
        transformed = self.adapter.transform(utility_text, "utility-test")
        self.assertIn("아목시실린 500mg을 하루 3회 식후 경구 투여한다.", transformed)

    def test_guardian_name_particle_variants(self) -> None:
        for fragment in (
            "보호자 이난향(연락처 확인)",
            "보호자는 김정묵이며 연락처 확인",
            "호출자 초미란, 연락처 확인",
        ):
            with self.subTest(fragment=fragment):
                found = [fragment[p.start : p.end] for p in self.adapter.detect(fragment) if p.type == "GUARDIAN_NAME"]
                self.assertEqual(1, len(found), found)

    def test_policy_outputs_declare_frontier_support(self) -> None:
        outputs = self.adapter.policy_outputs()
        self.assertIn("P2", outputs)
        self.assertIn("P1", outputs)


class FailureIsolationTest(unittest.TestCase):
    def test_failing_adapter_is_recorded_not_raised(self) -> None:
        class BrokenAdapter(SystemAdapter):
            system_id = "BROKEN"

            def detect(self, text: str):
                raise RuntimeError("detector exploded")

            def transform(self, text: str, case_key: str) -> str:
                raise RuntimeError("replacer exploded")

        adapter = BrokenAdapter()
        result = run_case(adapter, "아무 텍스트", "case-x")
        self.assertIsNotNone(result.error)
        self.assertIn("detector exploded", result.error or "")
        self.assertEqual((), result.predictions)
        self.assertEqual("", result.transformed_text)

    def test_stats_track_failures(self) -> None:
        class HalfBroken(SystemAdapter):
            system_id = "HALF_BROKEN"

            def detect(self, text: str):
                if text:
                    raise ValueError("boom")
                return []

            def transform(self, text: str, case_key: str) -> str:
                return text

        adapter = HalfBroken()
        stats = AdapterStats(system_id=adapter.system_id)
        result = run_case(adapter, "텍스트", "c1")
        record_stats(stats, result)
        self.assertEqual(1, stats.cases_run)
        self.assertEqual(1, stats.cases_failed)


if __name__ == "__main__":
    unittest.main()
