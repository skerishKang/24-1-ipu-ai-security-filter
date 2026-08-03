import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.schemas.manual_preview import ManualPreviewRequest
from app.services.manual_preview_service import ManualPreviewService

from engine.src.session_store import InMemorySessionStore


class ManualPreviewResponseModeTest(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("IPU_MANUAL_PREVIEW_RESPONSE_MODE", None)

    def test_default_response_mode_keeps_review_fields(self) -> None:
        os.environ.pop("IPU_MANUAL_PREVIEW_RESPONSE_MODE", None)
        service = ManualPreviewService(session_store=InMemorySessionStore())

        response = service.build_preview(
            ManualPreviewRequest(
                content="아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
                content_type="text",
                policy="default",
            )
        )

        self.assertIn("contact@ipu.co.kr", response.original_text)
        self.assertTrue(any(item.label for item in response.detections))
        self.assertTrue(any(item.original for item in response.replacements))

    def test_minimized_response_mode_removes_review_originals(self) -> None:
        os.environ["IPU_MANUAL_PREVIEW_RESPONSE_MODE"] = "minimized"
        service = ManualPreviewService(session_store=InMemorySessionStore())

        response = service.build_preview(
            ManualPreviewRequest(
                content="아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
                content_type="text",
                policy="default",
            )
        )

        self.assertEqual(response.original_text, "")
        self.assertTrue(response.replaced_text)
        self.assertTrue(response.restore_token)
        self.assertTrue(response.detections)
        self.assertTrue(response.replacements)
        self.assertTrue(all(item.label == "" for item in response.detections))
        self.assertTrue(all(item.original == "" for item in response.replacements))
        self.assertTrue(all(item.replaced for item in response.replacements))


if __name__ == "__main__":
    unittest.main()
