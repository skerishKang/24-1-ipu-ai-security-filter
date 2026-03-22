import json
import unittest

from engine.src.contracts import Detection
from engine.src.local_rewriter import OllamaLocalRewriter


class FakeClient:
    def __init__(self, response: str = "", should_fail: bool = False) -> None:
        self.response = response
        self.should_fail = should_fail

    def generate(self, *, model: str, system: str, prompt: str) -> str:
        if self.should_fail:
            raise RuntimeError("ollama-offline")
        return self.response


class LocalRewriterTest(unittest.TestCase):
    def test_rewrite_uses_model_json_when_valid(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "replacements": [
                        {"index": 1, "replacement": "담당자 1", "reason": "person generalized"},
                        {"index": 2, "replacement": "A사", "reason": "organization generalized"},
                    ]
                },
                ensure_ascii=False,
            )
        )
        rewriter = OllamaLocalRewriter(client=client, model="test-model")
        detections = [
            Detection(type="PERSON", label="홍길동", start=0, end=3, score=0.9, note="test"),
            Detection(type="ORG", label="아이피유", start=4, end=8, score=0.9, note="test"),
        ]

        result = rewriter.rewrite("홍길동 아이피유", detections)

        self.assertFalse(result.used_fallback)
        self.assertEqual(result.replacements[0].replaced, "담당자 1")
        self.assertEqual(result.replacements[1].replaced, "A사 2")

    def test_rewrite_falls_back_when_json_is_invalid(self) -> None:
        client = FakeClient("not-json")
        rewriter = OllamaLocalRewriter(client=client, model="test-model")
        detections = [
            Detection(type="EMAIL", label="test@example.com", start=0, end=16, score=0.9, note="test"),
        ]

        result = rewriter.rewrite("test@example.com", detections)

        self.assertTrue(result.used_fallback)
        self.assertEqual(result.replacements[0].replaced, "이메일 주소 1")

    def test_rewrite_falls_back_when_client_fails(self) -> None:
        client = FakeClient(should_fail=True)
        rewriter = OllamaLocalRewriter(client=client, model="test-model")
        detections = [
            Detection(type="PHONE", label="010-1234-5678", start=0, end=13, score=0.9, note="test"),
        ]

        result = rewriter.rewrite("010-1234-5678", detections)

        self.assertTrue(result.used_fallback)
        self.assertEqual(result.replacements[0].replaced, "연락처 1")


if __name__ == "__main__":
    unittest.main()
