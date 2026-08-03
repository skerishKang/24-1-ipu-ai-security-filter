from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.src.local_rewriter import OllamaLocalRewriter
from engine.src.manual_preview_engine import ManualPreviewEngine
from engine.tests.rewrite_comparison_samples import REWRITE_COMPARISON_SAMPLES


class StubClient:
    TYPE_TO_LABEL: ClassVar[dict[str, str]] = {
        "PERSON": "담당자",
        "ORG": "A사",
        "EMAIL": "이메일 주소",
        "PHONE": "연락처",
        "AMOUNT": "비공개 금액",
    }

    def generate(self, *, model: str, system: str, prompt: str) -> str:
        replacements = []
        pattern = re.compile(r"- index=(\d+) type=([A-Z_]+) ")
        for line in prompt.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            index = int(match.group(1))
            detection_type = match.group(2)
            base = self.TYPE_TO_LABEL.get(detection_type, "비식별 정보")
            replacements.append(
                {
                    "index": index,
                    "replacement": f"{base} {index}",
                    "reason": "stubbed_local_rewrite",
                }
            )
        return json.dumps({"replacements": replacements}, ensure_ascii=False)


engine = ManualPreviewEngine(local_rewriter=OllamaLocalRewriter(client=StubClient(), model="stub"))

print("IPU Rewrite Comparison")
print("=" * 80)
for sample in REWRITE_COMPARISON_SAMPLES:
    print(f"\n[{sample.sample_id}] {sample.description}")
    print(f"original: {sample.content}")
    strict_preview = engine.manual_preview(sample.content, session_id=f"strict-{sample.sample_id}", policy="strict_token")
    rewrite_preview = engine.manual_preview(sample.content, session_id=f"rewrite-{sample.sample_id}", policy="local_rewrite")
    print(f"strict_token : {strict_preview['replaced_text']}")
    print(f"local_rewrite: {rewrite_preview['replaced_text']}")
    print(
        "detections    : "
        f"strict={len(strict_preview['detections'])} / rewrite={len(rewrite_preview['detections'])}"
    )