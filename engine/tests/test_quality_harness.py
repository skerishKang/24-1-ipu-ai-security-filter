from __future__ import annotations

import unittest

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.tests.quality_samples import QUALITY_SAMPLES


class ManualPreviewQualityHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ManualPreviewEngine()

    def test_quality_samples_cover_expected_detection_types(self) -> None:
        for sample in QUALITY_SAMPLES:
            if sample.sample_group != "baseline":
                continue

            with self.subTest(sample=sample.sample_id):
                preview = self.engine.manual_preview(
                    content=sample.content,
                    session_id=f"quality-{sample.sample_id}",
                    policy="strict_token",
                )

                detected_types = {item["type"] for item in preview["detections"]}
                self.assertGreaterEqual(len(preview["detections"]), sample.minimum_detections)
                for expected_type in sample.expected_types:
                    self.assertIn(expected_type, detected_types)

                self.assertEqual(preview["report"]["total_detections"], len(preview["detections"]))
                self.assertEqual(preview["report"]["strategy"], "strict_token")
                self.assertTrue(preview["replaced_text"])
                self.assertIn("[Redacted Input]", preview["copy_ready_prompt"])

    def test_replaced_text_contains_expected_tokens_for_quality_samples(self) -> None:
        for sample in QUALITY_SAMPLES:
            if sample.sample_group != "baseline":
                continue

            with self.subTest(sample=sample.sample_id):
                preview = self.engine.manual_preview(
                    content=sample.content,
                    session_id=f"quality-token-{sample.sample_id}",
                    policy="strict_token",
                )

                self.assertEqual(preview["report"]["strategy"], "strict_token")
                for expected_type in sample.expected_token_types:
                    self.assertIn(f"[{expected_type}_", preview["replaced_text"])

    def test_default_policy_uses_alias_tokens_for_detected_types(self) -> None:
        sample = next(item for item in QUALITY_SAMPLES if item.sample_id == "combined_business_note")

        preview = self.engine.manual_preview(
            content=sample.content,
            session_id="quality-default-alias",
            policy="default",
        )

        self.assertIn("[PERSON_ALIAS_", preview["replaced_text"])
        self.assertIn("[EMAIL_ALIAS_", preview["replaced_text"])
        self.assertIn("[PHONE_ALIAS_", preview["replaced_text"])
        self.assertNotIn("[ORG_ALIAS_", preview["replaced_text"])
        self.assertNotIn("[AMOUNT_ALIAS_", preview["replaced_text"])

    def test_observe_only_samples_keep_current_limitations_visible_without_crashing(self) -> None:
        for sample in QUALITY_SAMPLES:
            if sample.sample_group != "observe-only":
                continue

            with self.subTest(sample=sample.sample_id):
                preview = self.engine.manual_preview(
                    content=sample.content,
                    session_id=f"quality-observe-{sample.sample_id}",
                    policy="default",
                )

                self.assertEqual(preview["report"]["strategy"], "alias")
                self.assertEqual(preview["report"]["total_detections"], len(preview["detections"]))
                self.assertIsInstance(preview["detections"], list)
                self.assertIsInstance(preview["replacements"], list)
                self.assertIn("[Redacted Input]", preview["copy_ready_prompt"])

    def test_combined_sample_restore_round_trip_is_lossless_before_expiration(self) -> None:
        sample = next(item for item in QUALITY_SAMPLES if item.sample_id == "combined_business_note")

        preview = self.engine.manual_preview(
            content=sample.content,
            session_id="quality-restore-roundtrip",
            policy="strict_token",
        )
        restored = self.engine.restore(preview["replaced_text"], "quality-restore-roundtrip")

        self.assertEqual(restored, sample.content)


if __name__ == "__main__":
    unittest.main()
