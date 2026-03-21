from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.src.detector import RegexDetector
from engine.src.local_rewriter import OllamaLocalRewriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local rewrite experiment with Ollama.")
    parser.add_argument("--input-file", type=Path, help="UTF-8 text file to analyze")
    parser.add_argument("--text", help="Direct text input")
    parser.add_argument("--model", default="qwen2.5:7b-instruct")
    parser.add_argument("--policy", default="strict_token", choices=["default", "strict_token"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input_file and not args.text:
        raise SystemExit("Provide --input-file or --text")

    if args.input_file:
        content = args.input_file.read_text(encoding="utf-8")
    else:
        content = str(args.text)

    detector = RegexDetector()
    detections = detector.detect(content, policy=args.policy)
    rewriter = OllamaLocalRewriter(model=args.model)
    result = rewriter.rewrite(content, detections)

    payload = {
        "policy": args.policy,
        "model": args.model,
        "used_fallback": result.used_fallback,
        "detections": [
            {
                "type": item.type,
                "label": item.label,
                "start": item.start,
                "end": item.end,
            }
            for item in detections
        ],
        "replacements": [
            {
                "type": item.type,
                "original": item.original,
                "replaced": item.replaced,
                "reason": item.reason,
            }
            for item in result.replacements
        ],
        "raw_response": result.raw_response,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
