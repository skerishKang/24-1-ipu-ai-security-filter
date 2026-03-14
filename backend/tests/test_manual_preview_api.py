import unittest

import httpx

from app.main import app


class ManualPreviewApiSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_health_endpoint(self) -> None:
        response = await self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "healthy")
        self.assertIn("mode", body)

    async def test_manual_preview_endpoint_shape(self) -> None:
        payload = {
            "content": (
                "아이피유테크 홍길동 이사는 고객사 contact@ipu.co.kr 과 "
                "010-1234-5678 정보를 포함한 제안서를 검토해 주세요."
            ),
            "content_type": "text",
            "policy": "default",
        }

        response = await self.client.post("/api/v1/mode/manual-preview", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()

        for field in (
            "session_id",
            "original_text",
            "replaced_text",
            "detections",
            "replacements",
            "report",
            "copy_ready_prompt",
        ):
            self.assertIn(field, body)

        self.assertEqual(body["original_text"], payload["content"])
        self.assertNotEqual(body["replaced_text"], body["original_text"])
        self.assertIsInstance(body["detections"], list)
        self.assertIsInstance(body["replacements"], list)
        self.assertGreaterEqual(len(body["detections"]), 1)
        self.assertGreaterEqual(len(body["replacements"]), 1)

        report = body["report"]
        for field in (
            "total_detections",
            "risk_level",
            "strategy",
            "review_status",
        ):
            self.assertIn(field, report)

        first_detection = body["detections"][0]
        for field in ("type", "label", "start", "end", "score", "note"):
            self.assertIn(field, first_detection)

        first_replacement = body["replacements"][0]
        for field in ("type", "original", "replaced", "reason"):
            self.assertIn(field, first_replacement)

    async def test_manual_preview_file_endpoint_shape(self) -> None:
        files = {
            "file": ("sample.txt", "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.", "text/plain"),
        }
        data = {"policy": "default"}

        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files=files,
            data=data,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("session_id", body)
        self.assertIn("replaced_text", body)
        self.assertIn("report", body)
        self.assertNotEqual(body["replaced_text"], body["original_text"])
        self.assertIsInstance(body["detections"], list)
        self.assertIsInstance(body["replacements"], list)

    async def test_manual_preview_file_rejects_unsupported_extension(self) -> None:
        files = {
            "file": ("sample.pdf", "fake pdf content", "application/pdf"),
        }

        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files=files,
            data={"policy": "default"},
        )

        self.assertEqual(response.status_code, 415)

    async def test_manual_preview_policy_is_reflected_in_report(self) -> None:
        strict_payload = {
            "content": "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
            "content_type": "text",
            "policy": "strict_token",
        }

        strict_response = await self.client.post("/api/v1/mode/manual-preview", json=strict_payload)
        self.assertEqual(strict_response.status_code, 200)
        self.assertEqual(strict_response.json()["report"]["strategy"], "strict_token")

        default_response = await self.client.post(
            "/api/v1/mode/manual-preview",
            json={**strict_payload, "policy": "default"},
        )
        self.assertEqual(default_response.status_code, 200)
        self.assertEqual(default_response.json()["report"]["strategy"], "alias")


if __name__ == "__main__":
    unittest.main()
