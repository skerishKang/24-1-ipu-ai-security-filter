# Local Rewrite Strategy

## Goal
- keep the current regex-based detection path
- add an opt-in local rewrite layer for better context preservation
- keep session mapping and restore semantics intact

## Current State
- `ManualPreviewEngine` uses `RegexDetector` + `TokenReplacer`
- current public policies are `default`, `strict_token`, and `local_rewrite`
- `local_rewrite` is now implemented and connected to API/UI
- `local_rewrite` is NOT the universal default yet
- current replacement output is safe for PoC, but not natural enough for real business prompting

## Next Step
- do not replace detection first
- replace only the rewrite stage
- keep restore and audit semantics unchanged

## Proposed Flow
1. detect sensitive spans with existing regex policy
2. generate safe rewrite suggestions with local model via Ollama
3. validate that rewrite output does not reveal original values
4. save mapping for restore and audit

## Why This Order
- detection quality already has baseline tests
- full LLM-only masking would be harder to validate
- rewrite-only upgrade is smaller and safer for MVP progression

## New Experimental Components
- `engine/src/local_rewriter.py`
- `engine/scripts/run_local_rewrite_preview.py`
- `engine/tests/test_local_rewriter.py`

## Suggested Future Policies

These policies are now implemented:
- `local_rewrite` (connected to API/UI, but not the universal default)
- `local_rewrite_strict` (future variant, still experimental)

`local_rewrite_strict` is still experimental. Keep it experimental until quality review is complete.

## Rollout Criteria
- baseline sample set should pass with no raw sensitive leakage
- rewritten text should preserve business usefulness better than `strict_token`
- fallback behavior should be deterministic when Ollama output is malformed

## Non-Goals For This Step
- no frontend migration
- no database migration
- no automatic mode rollout
- no removal of existing `default` / `strict_token`
