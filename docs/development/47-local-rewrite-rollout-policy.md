# Local Rewrite Rollout Policy

## Purpose
- define the current product status of `local_rewrite`
- separate "implemented" from "promoted"
- fix the operational rule for when to use `default`, `strict_token`, and `local_rewrite`

## Current Status
- `default`: implemented and stable
- `strict_token`: implemented and stable (still the benchmark for conservative masking)
- `local_rewrite`: implemented and exposed in API/UI, but NOT the universal default yet
- Ollama-backed rewriting is disabled by default and requires explicit `IPU_OLLAMA_ENABLED=true`

The important distinction is:
- `local_rewrite` is no longer a code-only experiment
- it is connected to the public API and visible in the UI
- deterministic fallback remains available when the local model is disabled or unavailable
- but it is not the recommended default policy for all use cases

## Why `local_rewrite` Exists
The current regex + token flow is safe enough for a PoC, but often too rigid for real business prompting.

`local_rewrite` keeps the existing detection path and changes only the rewrite stage:
1. detect sensitive spans with the conservative policy
2. generate more readable generalized replacements with a local model or deterministic fallback
3. preserve restore mapping and auditability

This is safer than replacing the entire engine with an LLM-only masking flow.

## Local Model Trust Boundary

When Ollama is explicitly enabled, `local_rewrite` may send original content and detected sensitive labels to the local model process. Loopback execution avoids remote transfer by default, but the model server is still a separate component that can observe the input it receives.

Operational rule:
- keep `IPU_OLLAMA_ENABLED=false` unless a deployment intentionally opts in
- keep remote Ollama hosts blocked by default
- do not log original content, detected labels, or raw local-model responses
- use deterministic fallback behavior when the model is disabled, unavailable, or malformed

## Policy Positioning

### `default`
Use when:
- quick readable preview is more important than maximum masking
- the user wants a softer before/after preview
- the document is low-risk and the user is actively reviewing output

Strengths:
- easier to read than strict tokens
- good for quick preview and manual inspection

Weaknesses:
- narrower detection scope than `strict_token`
- not the right choice for conservative external transfer

### `strict_token`
Use when:
- conservative masking is required
- business readability is secondary
- external transfer safety is more important than natural phrasing

Strengths:
- strongest current baseline
- easiest to audit
- easiest to compare in tests

Weaknesses:
- output is rigid
- business users may find the result unnatural

### `local_rewrite`
Use when:
- readability matters and the user still wants conservative detection
- the user wants a more natural sanitized text for external AI prompting
- the team is explicitly comparing output quality against `strict_token`
- the deployment has intentionally opted into local-model assistance, or deterministic fallback is acceptable

Strengths:
- keeps `strict_token`-level detection path
- produces more usable business text when rewrite quality is good
- preserves restore semantics

Weaknesses:
- output quality depends on local model behavior or fallback quality
- rollout requires stronger evaluation discipline
- local-model assistance expands the runtime trust boundary when explicitly enabled

## Promotion Rule
`local_rewrite` should be treated as promoted preview only if all conditions below remain true:

1. detection coverage is not worse than `strict_token`
2. direct leakage remains zero on the evaluation set
3. restore round-trip remains lossless
4. human review consistently prefers it over `strict_token` for business readability

If any one of these breaks, keep it available but do not treat it as the recommended policy.

## Fallback Rule
When the local model is unavailable or malformed:
- do not fail open
- fall back to deterministic generalized replacements
- keep the result restorable
- surface that the output came from fallback behavior if needed for debugging

## Recommended UX Position
Current recommendation:
- keep all three presets visible
- explain them by risk/readability tradeoff
- do not silently make `local_rewrite` the default yet
- explain that local-model assistance requires explicit backend opt-in

Suggested UI wording:
- `default`: readable baseline protection
- `strict_token`: conservative masking
- `local_rewrite`: readable rewrite with local-model assistance when enabled

## What Must Be True Before Wider Promotion
- document-type overlays exist for at least a few real document classes
- scorecard review is repeated on real business-like samples
- fallback behavior is accepted as operationally safe
- README and policy docs describe `local_rewrite` consistently as implemented preview, not as a hidden experiment

## Immediate Next Work
1. align README and policy docs with the real shipped state
2. add document-type overlays for the most common business documents
3. improve review UX so users can compare original / tokenized / rewritten text more clearly
4. keep `strict_token` as the benchmark policy for regression checks
