import unittest

from engine.src.detector import RegexDetector


class SensitivePatternDetectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = RegexDetector()

    def _types_for(self, content: str, policy: str = "strict_token") -> list[str]:
        return [item.type for item in self.detector.detect(content, policy=policy)]

    def test_strict_detects_business_registration_number(self) -> None:
        detections = self.detector.detect(
            "사업자등록번호 123-45-67890 을 계약서에 포함했습니다.",
            policy="strict_token",
        )
        self.assertIn("BUSINESS_REGISTRATION_NUMBER", [item.type for item in detections])

        # No prefix = no detection
        no_prefix = self.detector.detect(
            "123-45-67890 을 계약서에 포함했습니다.",
            policy="strict_token",
        )
        self.assertNotIn("BUSINESS_REGISTRATION_NUMBER", [item.type for item in no_prefix])

    def test_strict_detects_ip_address(self) -> None:
        detections = self.detector.detect(
            "관리 서버 IP는 192.168.0.10 입니다.",
            policy="strict_token",
        )
        self.assertIn("IP_ADDRESS", [item.type for item in detections])

        # IP check with bounds (invalid IP)
        invalid_ip = self.detector.detect(
            "관리 서버 IP는 999.168.0.10 입니다.",
            policy="strict_token",
        )
        self.assertNotIn("IP_ADDRESS", [item.type for item in invalid_ip])

        # Date false positive check
        date_str = self.detector.detect(
            "기준일은 2026.05.25 입니다.",
            policy="strict_token",
        )
        self.assertNotIn("IP_ADDRESS", [item.type for item in date_str])

    def test_strict_detects_api_key(self) -> None:
        detections = self.detector.detect(
            "OPENAI_API_KEY=sk-test1234567890abcdef1234567890",
            policy="strict_token",
        )
        self.assertIn("API_KEY", [item.type for item in detections])

    def test_local_rewrite_detects_new_sensitive_types(self) -> None:
        detections = self.detector.detect(
            "api_key: abcdef1234567890abcdef1234567890 / IP 10.0.0.5 / 사업자 번호: 1234567890",
            policy="local_rewrite",
        )
        types = {item.type for item in detections}
        self.assertIn("API_KEY", types)
        self.assertIn("IP_ADDRESS", types)
        self.assertIn("BUSINESS_REGISTRATION_NUMBER", types)

    def test_default_does_not_detect_new_strict_only_types(self) -> None:
        detections = self.detector.detect(
            "api_key: abcdef1234567890abcdef1234567890 / IP 10.0.0.5 / 사업자 번호: 1234567890",
            policy="default",
        )
        types = {item.type for item in detections}
        self.assertNotIn("API_KEY", types)
        self.assertNotIn("IP_ADDRESS", types)
        self.assertNotIn("BUSINESS_REGISTRATION_NUMBER", types)

    def test_strict_detects_resident_registration_number(self) -> None:
        detections = self.detector.detect(
            "주민등록번호 990101-1234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("RESIDENT_REGISTRATION_NUMBER", [item.type for item in detections])

        # Bare format is also caught: the post-hyphen "1" is a Korean RRN
        # (1900-1999 male) which the bare-format pattern picks up.
        no_prefix = self.detector.detect(
            "990101-1234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("RESIDENT_REGISTRATION_NUMBER", [item.type for item in no_prefix])

    def test_strict_detects_foreign_registration_number(self) -> None:
        detections = self.detector.detect(
            "외국인등록번호 990101-5234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("FOREIGN_REGISTRATION_NUMBER", [item.type for item in detections])

        # Bare format: post-hyphen "5" is the foreign-resident range, which
        # the FOREIGN bare-format pattern catches before the generic RRN.
        no_prefix = self.detector.detect(
            "990101-5234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("FOREIGN_REGISTRATION_NUMBER", [item.type for item in no_prefix])

    def test_strict_detects_card_number(self) -> None:
        detections = self.detector.detect(
            "카드 번호 4111-1111-1111-1111 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("CARD_NUMBER", [item.type for item in detections])

        # Bare (no-prefix) format is also caught under strict_token. The
        # Luhn-validated 4111-1111-1111-1111 is a known test card.
        bare = self.detector.detect(
            "4111-1111-1111-1111 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("CARD_NUMBER", [item.type for item in bare])

    def test_default_does_not_detect_id_number_or_card_types(self) -> None:
        detections = self.detector.detect(
            "주민등록번호 990101-1234567 / 외국인등록번호 990101-5234567 / 카드 번호 4111-1111-1111-1111",
            policy="default",
        )
        types = {item.type for item in detections}
        self.assertNotIn("RESIDENT_REGISTRATION_NUMBER", types)
        self.assertNotIn("FOREIGN_REGISTRATION_NUMBER", types)
        self.assertNotIn("CARD_NUMBER", types)

    def test_strict_detects_account_number(self) -> None:
        detections = self.detector.detect(
            "입금 계좌 123-456-789012 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("ACCOUNT_NUMBER", [item.type for item in detections])

        # Bare account number (3 groups separated by hyphens) is caught under
        # strict_token as a defense against label-stripped bypass attempts.
        bare = self.detector.detect(
            "123-456-789012 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("ACCOUNT_NUMBER", [item.type for item in bare])

    def test_strict_detects_vehicle_registration_number(self) -> None:
        detections = self.detector.detect(
            "차량 번호 123가4567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("VEHICLE_REGISTRATION_NUMBER", [item.type for item in detections])

        # Vehicle plate shape without a label is rare; we do not catch it as
        # bare-format because it produces too many false positives. The
        # labelled detection still works.
        bare = self.detector.detect(
            "123가4567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertNotIn("VEHICLE_REGISTRATION_NUMBER", [item.type for item in bare])

    def test_default_does_not_detect_account_or_vehicle_types(self) -> None:
        detections = self.detector.detect(
            "입금 계좌 123-456-789012 / 차량 번호 123가4567",
            policy="default",
        )
        types = {item.type for item in detections}
        self.assertNotIn("ACCOUNT_NUMBER", types)
        self.assertNotIn("VEHICLE_REGISTRATION_NUMBER", types)

    def test_bare_format_detects_resident_registration_number(self) -> None:
        # No prefix label: defense against the most common bypass.
        bare = self.detector.detect(
            "990101-1234567",
            policy="strict_token",
        )
        self.assertIn("RESIDENT_REGISTRATION_NUMBER", [item.type for item in bare])

    def test_bare_format_detects_foreign_registration_number(self) -> None:
        bare = self.detector.detect(
            "990101-5234567",
            policy="strict_token",
        )
        self.assertIn("FOREIGN_REGISTRATION_NUMBER", [item.type for item in bare])

    def test_bare_format_does_not_detect_under_default_policy(self) -> None:
        # Bare-format fallback only activates under strict_token / local_rewrite.
        bare = self.detector.detect(
            "990101-1234567",
            policy="default",
        )
        self.assertEqual([item.type for item in bare], [])

    def test_unicode_normalization_catches_zero_width_email(self) -> None:
        # Without normalization, the email regex would split on the zero-width
        # space and miss the value. After NFKC + zero-width stripping, the
        # email is detected.
        obfuscated = "sec\u200burity@ipu.co.kr"
        detections = self.detector.detect(obfuscated, policy="strict_token")
        self.assertTrue(
            any(item.type == "EMAIL" for item in detections),
            f"expected EMAIL detection for obfuscated input, got {[item.type for item in detections]}",
        )

    def test_unicode_normalization_catches_fullwidth_phone(self) -> None:
        obfuscated = "전화 ０１０-１２３４-５６７８ 로 주세요."
        detections = self.detector.detect(obfuscated, policy="strict_token")
        self.assertTrue(
            any(item.type == "PHONE" for item in detections),
            f"expected PHONE detection for fullwidth input, got {[item.type for item in detections]}",
        )


if __name__ == "__main__":
    unittest.main()
