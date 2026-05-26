# Non-WAV Audio Duration Probing Evaluation

## Purpose

This document records the evaluation decision for Issue #31: whether MP3, M4A, MP4, and WEBM duration validation should be added to the lightweight default upload path.

This is a design and evaluation document only. It does not implement non-WAV duration probing by itself.

## Background

The audio intake path currently has two layers of protection:

- A byte-size upload limit for all supported audio formats.
- A WAV duration limit implemented with Python stdlib `wave` in #28.

The remaining question is whether non-WAV formats should also be duration-checked by default.

Supported non-WAV extensions currently include:

- `.mp3`
- `.m4a`
- `.mp4`
- `.webm`

## Current Decision

Do not add MP3/M4A/MP4/WEBM duration probing to the lightweight default path yet.

Keep the current default behavior:

1. Validate supported extension and content type where available.
2. Enforce the audio byte-size limit.
3. Validate WAV duration using Python stdlib `wave`.
4. Leave non-WAV duration validation as an opt-in deployment hardening decision.

## Rationale

Reliable duration extraction for MP3, M4A, MP4, and WEBM is not as simple as WAV duration extraction.

WAV can be handled safely with the Python standard library because frame count and sample rate are directly available from the file header.

Non-WAV media often requires container and codec metadata parsing. A robust implementation usually needs a media probing tool such as `ffprobe` from FFmpeg.

Adding that to the default path has costs:

- Heavier local setup.
- More CI dependencies.
- Platform-specific installation differences.
- More failure modes when the binary is missing or malformed media is uploaded.
- Extra security and timeout considerations around spawning another external process.

The project has intentionally kept heavy audio dependencies opt-in so far. Non-WAV probing should follow that same principle unless the deployment target requires it.

## Options Considered

### Option A: Keep default path dependency-light

Decision: selected for now.

Behavior:

- WAV duration is checked with stdlib `wave`.
- MP3/M4A/MP4/WEBM keep byte-size validation only.
- Operators who need stronger validation can enable media probing in a deployment-specific path later.

Benefits:

- Keeps default CI lightweight.
- Avoids mandatory FFmpeg installation.
- Avoids additional subprocess failure modes.
- Preserves the existing opt-in philosophy for heavy audio processing.

Tradeoff:

- A non-WAV file under the byte-size limit may still be long in duration.

### Option B: Add `ffprobe` to the default path

Decision: not selected for now.

Behavior:

- Use `ffprobe` to extract duration for MP3/M4A/MP4/WEBM.
- Reject over-limit media before transcription.

Benefits:

- Stronger duration guardrail for all supported audio formats.
- Better protection before Whisper/STT execution.

Costs:

- Adds an external media tool dependency.
- Requires timeout handling around `ffprobe` subprocess execution.
- Requires CI and local setup updates.
- Needs clear behavior when `ffprobe` is missing.
- Can complicate default installation for a feature that may not be needed in internal demos.

### Option C: Add optional `ffprobe` probing behind configuration

Decision: possible future direction.

Behavior:

- Keep default path dependency-light.
- Add an environment flag such as `IPU_AUDIO_DURATION_PROBER=ffprobe` later.
- Add optional requirements/setup docs only for deployments that need it.

Benefits:

- Keeps default developer path simple.
- Allows stronger production hardening where needed.
- Aligns with the current Whisper opt-in pattern.

Costs:

- More configuration surface.
- Requires separate tests and documentation.
- Still needs subprocess timeout and missing-tool behavior.

## Recommended Future Implementation

If non-WAV duration probing is needed later, use Option C rather than adding FFmpeg tooling unconditionally.

Recommended shape:

- Add a small prober abstraction, for example `AudioDurationProber`.
- Keep `WavDurationProber` as the default stdlib implementation for WAV.
- Add optional `FfprobeDurationProber` only when explicitly enabled.
- Apply subprocess timeout to `ffprobe` calls.
- Map over-limit media to `ProcessingLimitExceededError` and HTTP 413.
- Map missing `ffprobe` to a clear configuration/tooling error, not a silent pass.

Potential environment setting:

```text
IPU_AUDIO_DURATION_PROBER=none|wav|ffprobe
```

Potential defaults:

| Environment | Recommended value | Notes |
| --- | --- | --- |
| Local default | `wav` | stdlib-only duration validation. |
| CI default | `wav` | no FFmpeg dependency required. |
| Controlled demo | `wav` | acceptable when sample files are known. |
| Untrusted external upload | `ffprobe` if available | stronger validation before STT. |

## Error Behavior

Recommended status mapping if optional probing is implemented later:

| Condition | Recommended status | Notes |
| --- | --- | --- |
| Duration exceeds configured limit | 413 | Use `ProcessingLimitExceededError`. |
| Audio file exceeds byte limit | 413 | Existing behavior. |
| Unsupported extension | 415 | Existing behavior. |
| Malformed WAV | 400 or existing validation error | Current WAV path raises a clear parsing error. |
| Missing optional `ffprobe` when required | 501 or 500-level configuration error | Depends on whether the mode is user-triggered or deployment-required. |
| `ffprobe` timeout | 413 or 504 | Prefer processing-limit style only if treated as guardrail rejection. |

## Testing Strategy

If optional `ffprobe` probing is implemented later:

- Do not add large audio fixtures.
- Use small generated or fake media files only when needed.
- Prefer mocking subprocess output for unit tests.
- Test timeout behavior without invoking a real long-running process.
- Keep real media probing smoke tests opt-in, similar to real Whisper smoke tests.
- Do not require FFmpeg in the default CI path unless the project explicitly changes the default dependency policy.

## Current Recommendation

For internal MVP and controlled demos:

- Keep current WAV-only duration validation.
- Keep MP3/M4A/MP4/WEBM duration probing deferred.
- Prefer known short demo samples.

Before untrusted external-user testing:

- Decide whether optional `ffprobe` probing is required.
- If required, implement it behind explicit configuration.
- Add subprocess timeout and missing-tool behavior.
- Keep default CI dependency-light unless there is a clear product reason to change it.

## Relationship to Other Issues

- #31 tracks non-WAV audio duration probing.
- #30 tracks upload timeout and concurrency design.
- #32 tracks broader compressed package inspection.
- #20 remains separate because address detection has high false-positive risk and should not be mixed with upload guardrail work.

## Acceptance Status

This document satisfies the evaluation-first requirement for #31. Implementation should be done in a separate PR only if a deployment mode needs non-WAV duration validation.
