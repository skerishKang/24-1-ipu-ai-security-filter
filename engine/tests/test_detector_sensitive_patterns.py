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

        no_prefix = self.detector.detect(
            "990101-1234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertNotIn("RESIDENT_REGISTRATION_NUMBER", [item.type for item in no_prefix])

    def test_strict_detects_foreign_registration_number(self) -> None:
        detections = self.detector.detect(
            "외국인등록번호 990101-5234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("FOREIGN_REGISTRATION_NUMBER", [item.type for item in detections])

        no_prefix = self.detector.detect(
            "990101-5234567 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertNotIn("FOREIGN_REGISTRATION_NUMBER", [item.type for item in no_prefix])

    def test_strict_detects_card_number(self) -> None:
        detections = self.detector.detect(
            "카드 번호 4111-1111-1111-1111 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertIn("CARD_NUMBER", [item.type for item in detections])

        no_prefix = self.detector.detect(
            "4111-1111-1111-1111 은 테스트용 가짜 값입니다.",
            policy="strict_token",
        )
        self.assertNotIn("CARD_NUMBER", [item.type for item in no_prefix])

    def test_default_does_not_detect_id_number_or_card_types(self) -> None:
        detections = self.detector.detect(
            "주민등록번호 990101-1234567 / 외국인등록번호 990101-5234567 / 카드 번호 4111-1111-1111-1111",
            policy="default",
        )
        types = {item.type for item in detections}
        self.assertNotIn("RESIDENT_REGISTRATION_NUMBER", types)
        self.assertNotIn("FOREIGN_REGISTRATION_NUMBER", types)
        self.assertNotIn("CARD_NUMBER", types)


if __name__ == "__main__":
    unittest.main()
