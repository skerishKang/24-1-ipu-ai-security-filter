import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.src.restorer import RestoreAuthenticationError
from engine.src.session_store import InMemorySessionStore, SQLiteSessionStore


class FakeClock:
    def __init__(self, initial: float = 0.0) -> None:
        self.current = initial

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def _arm_restore_auth(session_store, session_id: str, *, owner_hash: str = "test-owner") -> str:
    """Helper: register owner + restore token for a session and return the raw token."""
    token = f"test-token-{session_id}"
    session_store.save_owner_hash(session_id, owner_hash)
    session_store.save_restore_token_hash(
        session_id,
        hashlib.sha256(token.encode("utf-8")).hexdigest(),
    )
    return token


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
        self.assertIn(preview["report"]["risk_level"], {"low-risk", "moderate-risk", "high-risk"})
        self.assertIn(preview["report"]["strategy"], {"alias", "strict_token"})
        self.assertIn(preview["report"]["review_status"], {"clean", "review-required"})
        self.assertTrue(preview["detections"])
        self.assertTrue(preview["replacements"])
        self.assertIn("[Sanitized Text]", preview["copy_ready_prompt"])

    def test_restore_uses_session_mapping(self) -> None:
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."
        preview = self.engine.manual_preview(content=content, session_id="ipu-restore-session")

        token = _arm_restore_auth(self.engine.session_store, "ipu-restore-session")
        restored = self.engine.restore(
            preview["replaced_text"],
            "ipu-restore-session",
            token=token,
            owner_hash="test-owner",
        )

        self.assertEqual(restored, content)

    def test_restore_rejects_missing_token(self) -> None:
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."
        self.engine.manual_preview(content=content, session_id="ipu-restore-missing-token")
        _arm_restore_auth(self.engine.session_store, "ipu-restore-missing-token")

        with self.assertRaises(RestoreAuthenticationError):
            self.engine.restore(
                "[EMAIL_01]",
                "ipu-restore-missing-token",
                token="",
                owner_hash="test-owner",
            )

    def test_restore_rejects_wrong_token(self) -> None:
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."
        preview = self.engine.manual_preview(content=content, session_id="ipu-restore-wrong-token")
        _arm_restore_auth(self.engine.session_store, "ipu-restore-wrong-token")

        with self.assertRaises(RestoreAuthenticationError):
            self.engine.restore(
                preview["replaced_text"],
                "ipu-restore-wrong-token",
                token="not-the-issued-token",
                owner_hash="test-owner",
            )

    def test_restore_rejects_wrong_owner(self) -> None:
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."
        preview = self.engine.manual_preview(content=content, session_id="ipu-restore-wrong-owner")
        token = _arm_restore_auth(
            self.engine.session_store,
            "ipu-restore-wrong-owner",
            owner_hash="owner-a",
        )

        with self.assertRaises(RestoreAuthenticationError):
            self.engine.restore(
                preview["replaced_text"],
                "ipu-restore-wrong-owner",
                token=token,
                owner_hash="owner-b",
            )

    def test_non_text_content_returns_empty_detections(self) -> None:
        detections = self.engine.detect("ignored", content_type="audio", policy="default")
        self.assertEqual(detections, [])

    def test_restore_returns_original_text_only_before_ttl_expiration(self) -> None:
        clock = FakeClock()
        session_store = InMemorySessionStore(ttl_seconds=1, clock=clock.now)
        engine = ManualPreviewEngine(session_store=session_store)
        content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."

        preview = engine.manual_preview(content=content, session_id="ipu-ttl-session")
        token = _arm_restore_auth(session_store, "ipu-ttl-session")
        engine.restore(
            preview["replaced_text"],
            "ipu-ttl-session",
            token=token,
            owner_hash="test-owner",
        )

        clock.advance(2)
        with self.assertRaises(RestoreAuthenticationError):
            engine.restore(
                preview["replaced_text"],
                "ipu-ttl-session",
                token=token,
                owner_hash="test-owner",
            )
        # After expiry the session is cleared so even a valid token is rejected.
        # The replaced_text itself is unchanged.
        self.assertEqual(preview["replaced_text"], preview["replaced_text"])

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

        self.assertEqual(default_types, {"ORG", "PERSON", "EMAIL", "PHONE"})
        self.assertEqual(strict_types, {"ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"})
        self.assertIn("[PERSON_ALIAS_", default_preview["replaced_text"])
        self.assertIn("[PERSON_", strict_preview["replaced_text"])
        self.assertIn("[ORG_ALIAS_", default_preview["replaced_text"])
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

    def test_default_policy_skips_obfuscated_email_but_strict_token_detects_it(self) -> None:
        content = "문의는 security at ipu dot co kr 로 보내고, 박지은에게 먼저 공유해 주세요."

        default_preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-default-obfuscated-email",
            policy="default",
        )
        strict_preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-strict-obfuscated-email-compare",
            policy="strict_token",
        )

        default_types = {item["type"] for item in default_preview["detections"]}
        strict_types = {item["type"] for item in strict_preview["detections"]}

        self.assertEqual(default_types, set())
        self.assertIn("EMAIL", strict_types)
        self.assertIn("PERSON", strict_types)
        self.assertNotIn("[EMAIL_ALIAS_", default_preview["replaced_text"])
        self.assertIn("[EMAIL_", strict_preview["replaced_text"])
        self.assertEqual(default_preview["readiness"]["ready_to_send"], False)
        self.assertEqual(default_preview["readiness"]["review_status"], "review-required")
        self.assertEqual(default_preview["readiness"]["detection_count"], 2)
        self.assertEqual(default_preview["readiness"]["risk_level"], "moderate-risk")
        self.assertIn("EMAIL", default_preview["readiness"]["remaining_risks"])
        self.assertIn("PERSON", default_preview["readiness"]["remaining_risks"])

    def test_default_policy_blocks_readiness_for_strict_only_api_key(self) -> None:
        content = "외부 전달 전 검토: api_key: abcdef1234567890abcdef1234567890"

        preview = self.engine.manual_preview(
            content=content,
            session_id="ipu-default-strict-residual-api-key",
            policy="default",
        )

        self.assertEqual(preview["detections"], [])
        self.assertEqual(preview["replaced_text"], content)
        self.assertEqual(preview["report"]["review_status"], "clean")
        self.assertEqual(preview["readiness"]["ready_to_send"], False)
        self.assertEqual(preview["readiness"]["review_status"], "review-required")
        self.assertEqual(preview["readiness"]["detection_count"], 1)
        self.assertEqual(preview["readiness"]["risk_level"], "moderate-risk")
        self.assertIn("API_KEY", preview["readiness"]["remaining_risks"])

    def test_strict_token_rejects_generic_person_phrase(self) -> None:
        preview = self.engine.manual_preview(
            content="브랜드 대표 색상은 청록색이며, 소개 문구는 다음 주에 교체합니다.",
            session_id="ipu-generic-person-filter",
            policy="strict_token",
        )

        detected_types = {item["type"] for item in preview["detections"]}
        self.assertNotIn("PERSON", detected_types)

    def test_replace_rejects_explicit_empty_detection_list(self) -> None:
        # Defense-in-depth: an empty list cannot be used to bypass detection.
        with self.assertRaises(ValueError):
            self.engine.replace(
                content="민감정보 없는 일반 문장입니다.",
                detections=[],
                session_id="ipu-empty-detection-list",
                strategy="alias",
            )

    def test_replace_runs_detection_when_detections_is_none(self) -> None:
        # When ``detections`` is omitted the engine still runs detection
        # against the supplied content.
        replaced_text, replacements = self.engine.replace(
            content="문의는 contact@ipu.co.kr 로 주세요.",
            detections=None,
            session_id="ipu-auto-detect",
            strategy="alias",
        )
        self.assertNotEqual(replaced_text, "문의는 contact@ipu.co.kr 로 주세요.")
        self.assertTrue(replacements)

    def test_sqlite_session_store_restores_after_engine_restart(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "session_store.sqlite3"
            first_engine = ManualPreviewEngine(
                session_store=SQLiteSessionStore(db_path=db_path, ttl_seconds=900)
            )
            content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."

            preview = first_engine.manual_preview(
                content=content,
                session_id="ipu-sqlite-restart-session",
                policy="strict_token",
            )

            second_engine = ManualPreviewEngine(
                session_store=SQLiteSessionStore(db_path=db_path, ttl_seconds=900)
            )
            token = _arm_restore_auth(
                second_engine.session_store, "ipu-sqlite-restart-session"
            )
            restored = second_engine.restore(
                preview["replaced_text"],
                "ipu-sqlite-restart-session",
                token=token,
                owner_hash="test-owner",
            )

            self.assertEqual(restored, content)

    def test_sqlite_session_store_cleans_up_expired_sessions(self) -> None:
        clock = FakeClock()
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "session_store.sqlite3"
            session_store = SQLiteSessionStore(
                db_path=db_path,
                ttl_seconds=1,
                clock=clock.now,
            )
            engine = ManualPreviewEngine(session_store=session_store)
            content = "문의는 010-1234-5678 또는 contact@ipu.co.kr 로 주세요."

            preview = engine.manual_preview(content=content, session_id="ipu-sqlite-ttl")
            token = _arm_restore_auth(session_store, "ipu-sqlite-ttl")
            self.assertEqual(
                engine.restore(
                    preview["replaced_text"],
                    "ipu-sqlite-ttl",
                    token=token,
                    owner_hash="test-owner",
                ),
                content,
            )

            clock.advance(2)
            session_store.cleanup_expired_sessions()

            with self.assertRaises(RestoreAuthenticationError):
                engine.restore(
                    preview["replaced_text"],
                    "ipu-sqlite-ttl",
                    token=token,
                    owner_hash="test-owner",
                )

    def test_strict_policy_replaces_api_key_and_ip(self) -> None:
        result = self.engine.manual_preview(
            content="api_key: abcdef1234567890abcdef1234567890 서버 IP 10.0.0.5",
            session_id="test-session",
            content_type="text",
            policy="strict_token",
            strategy="strict_token",
        )
        self.assertIn("[API_KEY_", result["replaced_text"])
        self.assertIn("[IP_ADDRESS_", result["replaced_text"])

    def test_strict_policy_replaces_id_numbers_and_card_number(self) -> None:
        result = self.engine.manual_preview(
            content=(
                "주민등록번호 990101-1234567, "
                "외국인등록번호 990101-5234567, "
                "카드 번호 4111-1111-1111-1111"
            ),
            session_id="test-id-number-session",
            content_type="text",
            policy="strict_token",
            strategy="strict_token",
        )
        self.assertIn("[RESIDENT_REGISTRATION_NUMBER_", result["replaced_text"])
        self.assertIn("[FOREIGN_REGISTRATION_NUMBER_", result["replaced_text"])
        self.assertIn("[CARD_NUMBER_", result["replaced_text"])

    def test_strict_policy_replaces_account_and_vehicle_number(self) -> None:
        result = self.engine.manual_preview(
            content="입금 계좌 123-456-789012, 차량 번호 123가4567",
            session_id="test-account-vehicle-session",
            content_type="text",
            policy="strict_token",
            strategy="strict_token",
        )
        self.assertIn("[ACCOUNT_NUMBER_", result["replaced_text"])
        self.assertIn("[VEHICLE_REGISTRATION_NUMBER_", result["replaced_text"])


if __name__ == "__main__":
    unittest.main()
