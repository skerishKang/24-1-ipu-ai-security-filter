import json
import unittest

from engine.src.contracts import Detection
from engine.src.local_rewriter import OllamaLocalRewriter


class FakeClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, *, model: str, system: str, prompt: str) -> str:
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
        self.assertEqual(result.replacements[1].replaced, "A사")

    def test_rewrite_falls_back_when_json_is_invalid(self) -> None:
        client = FakeClient("not-json")
        rewriter = OllamaLocalRewriter(client=client, model="test-model")
        detections = [
            Detection(type="EMAIL", label="test@example.com", start=0, end=16, score=0.9, note="test"),
        ]

        result = rewriter.rewrite("test@example.com", detections)

        self.assertTrue(result.used_fallback)
        self.assertEqual(result.replacements[0].replaced, "이메일 주소")


if __name__ == "__main__":
    unittest.main()
