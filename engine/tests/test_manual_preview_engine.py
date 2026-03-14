import unittest

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.src.session_store import InMemorySessionStore


class FakeClock:
    def __init__(self, initial: float = 0.0) -> None:
        self.current = initial

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class ManualPreviewEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ManualPreviewEngine()

    def test_detect_replace_and_report_shape(self) -> None:
        content = (
            "아이피유테크 홍길동 이사는 contact@ipu.co.kr 과 010-1234-5678 정보를 포함하며 "
            "계약 금액은 12,500,000원입니다."
        )

        preview = self.engine.manual_preview(content=content, session_id="ipu-test-session")

        self.assertEqual(preview["session_id"], "ipu-test-session")
        self.assertEqual(preview["original_text"], content)
        self.assertIn("replaced_text", preview)
        self.assertGreaterEqual(preview["report"]["total_detections"], 1)
        self.assertTrue(preview["detections"])
        self.assertTrue(preview["replacements"])
        self.assertIn("[Redacted Input]", preview["copy_ready_prompt"])

    def test_restore_uses_session_mapping(self) -> None:
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."
        preview = self.engine.manual_preview(content=content, session_id="ipu-restore-session")

        restored = self.engine.restore(preview["replaced_text"], "ipu-restore-session")

        self.assertEqual(restored, content)

    def test_non_text_content_returns_empty_detections(self) -> None:
        detections = self.engine.detect("ignored", content_type="audio", policy="default")
        self.assertEqual(detections, [])

    def test_restore_returns_original_text_only_before_ttl_expiration(self) -> None:
        clock = FakeClock()
        session_store = InMemorySessionStore(ttl_seconds=1, clock=clock.now)
        engine = ManualPreviewEngine(session_store=session_store)
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."

        preview = engine.manual_preview(content=content, session_id="ipu-ttl-session")
        restored_before_expiry = engine.restore(preview["replaced_text"], "ipu-ttl-session")

        clock.advance(2)
        restored_after_expiry = engine.restore(preview["replaced_text"], "ipu-ttl-session")

        self.assertEqual(restored_before_expiry, content)
        self.assertEqual(restored_after_expiry, preview["replaced_text"])

    def test_cleanup_expired_sessions_removes_stale_mappings(self) -> None:
        clock = FakeClock()
        session_store = InMemorySessionStore(ttl_seconds=1, clock=clock.now)
        engine = ManualPreviewEngine(session_store=session_store)

        engine.manual_preview(
            content="아이피유테크 홍길동 이사는 contact@ipu.co.kr 에 메일을 보냅니다.",
            session_id="ipu-cleanup-session",
        )
        self.assertTrue(session_store.get_mappings("ipu-cleanup-session"))

        clock.advance(2)
        session_store.cleanup_expired_sessions()

        self.assertEqual(session_store.get_mappings("ipu-cleanup-session"), [])

    def test_effective_strategy_is_reflected_in_report_strategy(self) -> None:
        content = "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다."

        default_preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-policy-default",
            policy="default",
        )
        strict_preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-policy-strict",
            policy="strict_token",
        )

        self.assertEqual(default_preview["report"]["strategy"], "alias")
        self.assertEqual(strict_preview["report"]["strategy"], "strict_token")

    def test_default_policy_uses_alias_tokens(self) -> None:
        preview = self.engine.manual_preview(
            content="문의는 contact@ipu.co.kr 또는 010-1234-5678 로 주세요.",
            session_id="ipu-policy-default-alias",
            policy="default",
        )

        self.assertIn("[EMAIL_ALIAS_", preview["replaced_text"])
        self.assertIn("[PHONE_ALIAS_", preview["replaced_text"])

    def test_strict_token_policy_detects_more_types_than_default(self) -> None:
        content = (
            "아이피유테크 담당자는 박지은 이사입니다. 미래전자와 security@ipu.co.kr 및 "
            "010-2222-3333 연락처를 공유했고, 제안 금액은 120,000,000원입니다."
        )

        default_preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-policy-default-detect",
            policy="default",
        )
        strict_preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-policy-strict-detect",
            policy="strict_token",
        )

        default_types = {item["type"] for item in default_preview["detections"]}
        strict_types = {item["type"] for item in strict_preview["detections"]}

        self.assertEqual(default_types, {"PERSON", "EMAIL", "PHONE"})
        self.assertEqual(strict_types, {"ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"})
        self.assertIn("[PERSON_ALIAS_", default_preview["replaced_text"])
        self.assertIn("[PERSON_", strict_preview["replaced_text"])
        self.assertNotIn("[ORG_ALIAS_", default_preview["replaced_text"])
        self.assertIn("[ORG_", strict_preview["replaced_text"])
        self.assertNotIn("[AMOUNT_ALIAS_", default_preview["replaced_text"])
        self.assertIn("[AMOUNT_", strict_preview["replaced_text"])
        self.assertEqual(default_preview["report"]["strategy"], "alias")
        self.assertEqual(strict_preview["report"]["strategy"], "strict_token")

    def test_strict_token_skips_generic_org_suffix_terms(self) -> None:
        preview = self.engine.manual_preview(
            content="협력기업, 외부회사, 중견기업 담당자와 순차적으로 미팅을 진행합니다.",
            session_id="ipu-generic-org-filter",
            policy="strict_token",
        )

        detected_types = {item["type"] for item in preview["detections"]}
        self.assertNotIn("ORG", detected_types)

    def test_strict_token_detects_obfuscated_email_and_bare_name_context(self) -> None:
        preview = self.engine.manual_preview(
            content="문의는 security at ipu dot co kr 로 보내고, 박지은에게 먼저 공유해 주세요.",
            session_id="ipu-strict-obfuscated-email",
            policy="strict_token",
        )

        detected_types = [item["type"] for item in preview["detections"]]
        self.assertIn("EMAIL", detected_types)
        self.assertIn("PERSON", detected_types)
        self.assertIn("[EMAIL_", preview["replaced_text"])
        self.assertIn("[PERSON_", preview["replaced_text"])

    def test_strict_token_rejects_generic_person_phrase(self) -> None:
        preview = self.engine.manual_preview(
            content="브랜드 대표 색상은 청록색이며, 소개 문구는 다음 주에 교체합니다.",
            session_id="ipu-generic-person-filter",
            policy="strict_token",
        )

        detected_types = {item["type"] for item in preview["detections"]}
        self.assertNotIn("PERSON", detected_types)


if __name__ == "__main__":
    unittest.main()
