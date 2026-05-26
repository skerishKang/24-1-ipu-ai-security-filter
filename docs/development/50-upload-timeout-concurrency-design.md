# Upload Timeout and Concurrency Guardrail Design

## Purpose

This document records the design decision for Issue #30: upload timeout and concurrency guardrails for manual-preview file and audio intake.

This is a design document only. It does not implement timeout or concurrency behavior by itself.

## Background

The first upload guardrail wave is already implemented and documented:

- #26 added PDF page limits, OCR page limits, OCR subprocess timeout handling, and processing-limit HTTP 413 mapping.
- #27 added DOCX/HWPX internal XML size and count guardrails.
- #28 added WAV duration validation with Python stdlib `wave`.
- #29 documented the upload guardrail status in `49-upload-processing-guardrails-status.md`.

The remaining risk in #30 is not parser-specific. It is deployment-level behavior for expensive request paths.

## Current Decision

Do not add a blanket `asyncio.wait_for()` wrapper around manual-preview routes yet.

Instead, use a layered strategy:

1. Keep parser/transcriber-level guardrails as the first line of defense.
2. Use deployment or ingress request timeouts for hard network/request boundaries.
3. Add application-level concurrency limiting only for expensive upload paths if the service is exposed to untrusted users.
4. Add application-level processing deadlines only after cancellation and cleanup behavior is verified for thread, subprocess, and Whisper paths.

## Why Not a Blind Route Timeout

A simple route-level timeout can appear attractive, but it has several risks:

- `asyncio.wait_for()` cancellation does not automatically stop work already running in a thread.
- OCR subprocesses need explicit timeout and cleanup behavior, which #26 already handles at the subprocess-call level.
- Whisper transcription may run through model code and temporary files; interruption boundaries must be understood before adding app-level cancellation.
- A timeout at the wrong layer can return an error to the client while expensive background work continues.

For these reasons, parser/subprocess-specific guardrails are safer as the default baseline, and request-level timeout should be treated as a deployment hardening decision.

## Recommended Layering

### Internal MVP / controlled demo

Recommended default:

- Keep current parser/transcriber-level limits.
- Do not add app-level request timeout yet.
- Do not add app-level concurrency throttling yet unless manual load testing shows a need.
- Keep deployment environment small and controlled.

Rationale:

- The current code already rejects many expensive inputs early.
- Controlled demos have known users and predictable sample files.
- Avoiding extra concurrency and timeout plumbing keeps debugging simple.

### Untrusted-user testing / external deployment

Recommended default before exposure:

- Configure deployment/ingress request timeout.
- Add bounded concurrency for expensive upload routes.
- Prefer explicit HTTP 429 or 503 for concurrency rejection.
- Keep existing HTTP 413 mapping for processing-limit failures.
- Log timeout/concurrency rejections as operational events without storing raw uploaded content.

Potential defaults to evaluate:

| Setting | Candidate default | Notes |
| --- | --- | --- |
| File upload processing slots | 2 to 4 | Depends on CPU and OCR availability. |
| Audio upload processing slots | 1 to 2 | Whisper/STT can be much heavier than file parsing. |
| Ingress request timeout | 60 to 120 seconds | Should align with demo expectations and server resources. |
| App-level processing deadline | Deferred | Only after cleanup behavior is proven. |

## Concurrency Design Candidate

If application-level concurrency is added later, prefer a narrow service-level limiter over global middleware.

Candidate approach:

- Add separate semaphores for file and audio upload paths.
- Acquire the semaphore around `build_file_preview()` and `build_audio_preview()` or a small wrapper close to those calls.
- Reject immediately when the limiter is saturated instead of queueing indefinitely.
- Return HTTP 429 or 503 with a clear message such as `Upload processing is busy. Please try again shortly.`
- Do not apply this limiter to the plain text manual-preview route unless load testing shows a need.

Why not global middleware:

- Global middleware may throttle cheap health/text requests unnecessarily.
- Upload routes have very different cost profiles from text preview and restore routes.
- Route/service-specific limits are easier to reason about and test.

## Timeout Design Candidate

If application-level timeout is added later, it should be designed per expensive operation rather than as a blanket catch-all.

Candidate approach:

- Keep OCR subprocess timeout at the subprocess-call level.
- Keep WAV duration limit before transcription.
- Add Whisper/STT operation timeout only if the transcriber implementation can guarantee cleanup of temporary files and does not leave expensive work running.
- Use deployment/ingress timeout for final request boundary.
- Add app-level timeout only with tests proving the expensive work stops or is safely bounded.

## Error Behavior

Recommended status mapping:

| Condition | Recommended status | Notes |
| --- | --- | --- |
| Parser/transcriber processing limit exceeded | 413 | Already used for `ProcessingLimitExceededError`. |
| Upload size exceeded | 413 | Already used for file/audio byte limits. |
| Concurrency limit saturated | 429 or 503 | 429 is clearer for client retry behavior; 503 is acceptable for server capacity. |
| Deployment/ingress timeout | Platform-specific | Usually generated by proxy/platform, not FastAPI. |
| App-level processing timeout | 504 or 503 | Only if implemented with safe cancellation semantics. |

## Testing Strategy

If concurrency limiting is implemented later:

- Use fake parsers/transcribers that sleep briefly.
- Avoid real OCR, Whisper, or large files.
- Test that the limit rejects excess requests without queueing indefinitely.
- Test that normal requests still complete when slots are available.

If app-level timeout is implemented later:

- Use fake tasks with deterministic delay.
- Verify response status and error body.
- Verify cleanup hooks run if the implementation creates temporary files.
- Do not use real long-running media or document fixtures.

## Current Recommendation

For now, keep Issue #30 open as a design-tracking issue and do not implement timeout/concurrency behavior until one of these conditions is true:

1. The app is prepared for untrusted-user testing.
2. Load testing shows controlled demos can saturate the server.
3. The deployment target requires explicit app-level timeouts in addition to proxy timeouts.
4. Whisper/STT execution is enabled in a setting where concurrent users are expected.

## Relationship to Other Issues

- #30 tracks timeout and concurrency behavior.
- #31 tracks non-WAV audio duration probing.
- #32 tracks broader compressed package inspection.
- #20 remains separate because address detection has high false-positive risk and should not be mixed with upload guardrail work.

## Acceptance Status

This document satisfies the design-first requirement for #30. Implementation should be done in a separate PR only after the operating mode and deployment target are clear.
