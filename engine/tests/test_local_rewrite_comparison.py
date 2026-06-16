from __future__ import annotations

import hashlib
import json
import unittest

from engine.src.local_rewriter import OllamaLocalRewriter
from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.tests.rewrite_comparison_samples import REWRITE_COMPARISON_SAMPLES


def _arm_restore_auth(session_store, session_id: str, *, owner_hash: str = "test-owner") -> str:
    """Helper: register owner + restore token for a session and return the raw token."""
    token = f"test-token-{session_id}"
    session_store.save_owner_hash(session_id, owner_hash)
    session_store.save_restore_token_hash(
        session_id,
        hashlib.sha256(token.encode("utf-8")).hexdigest(),
    )
    return token


class FakeClient:
    def generate(self, *, model: str, system: str, prompt: str) -> str:
        indices = []
        for line in prompt.splitlines():
            if line.startswith("- index="):
                index = int(line.split()[1].split("=")[1])
                indices.append(index)
        replacements = []
        for index in indices:
            replacements.append(
                {
                    "index": index,
                    "replacement": f"검토용 일반화 표현 {index}",
                    "reason": "stubbed_local_rewrite",
                }
            )
        return json.dumps({"replacements": replacements}, ensure_ascii=False)


class LocalRewriteComparisonTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ManualPreviewEngine(local_rewriter=OllamaLocalRewriter(client=FakeClient(), model="stub"))

    def test_local_rewrite_produces_non_tokenized_output_for_all_samples(self) -> None:
        for sample in REWRITE_COMPARISON_SAMPLES:
            with self.subTest(sample=sample.sample_id):
                preview = self.engine.manual_preview(
                    content=sample.content,
                    session_id=f"local-rewrite-{sample.sample_id}",
                    policy="local_rewrite",
                )
                self.assertEqual(preview["report"]["strategy"], "local_rewrite")
                self.assertGreaterEqual(len(preview["detections"]), 1)
                self.assertNotIn("[EMAIL", preview["replaced_text"])
                self.assertNotIn("[PHONE", preview["replaced_text"])
                self.assertIn("검토용 일반화 표현", preview["replaced_text"])

    def test_local_rewrite_restore_restores_original_text(self) -> None:
        sample = REWRITE_COMPARISON_SAMPLES[0]
        preview = self.engine.manual_preview(
            content=sample.content,
            session_id="local-rewrite-restore",
            policy="local_rewrite",
        )

        token = _arm_restore_auth(self.engine.session_store, "local-rewrite-restore")
        restored = self.engine.restore(
            preview["replaced_text"],
            "local-rewrite-restore",
            token=token,
            owner_hash="test-owner",
        )

        self.assertEqual(restored, sample.content)


if __name__ == "__main__":
    unittest.main()
