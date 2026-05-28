# Non-WAV Audio Duration Probing Evaluation

## Purpose

This document records the evaluation decision for Issue #31 and the follow-up hardening implementation for Issue #75: whether MP3, M4A, MP4, and WEBM duration validation should be added to the lightweight default upload path.

## Background

The audio intake path has these protection layers:

- A byte-size upload limit for all supported audio formats.
- A WAV duration limit implemented with Python stdlib `wave`.
- Optional non-WAV duration validation through `ffprobe` when explicitly enabled.

Supported non-WAV extensions currently include:

- `.mp3`
- `.m4a`
- `.mp4`
- `.webm`

## Current Decision

Keep the default path dependency-light, but allow deployment hardening with optional `ffprobe` duration probing.

Default behavior:

1. Validate supported extension and content type where available.
2. Enforce the audio byte-size limit.
3. Validate WAV duration using Python stdlib `wave`.
4. Leave MP3/M4A/MP4/WEBM duration probing disabled unless explicitly configured.

Optional hardening behavior:

```text
IPU_AUDIO_DURATION_PROBER=ffprobe
```

When this setting is enabled, non-WAV uploads are written to a temporary file, probed with `ffprobe`, and rejected before STT if duration exceeds `MAX_AUDIO_DURATION_SECONDS`.

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

The project keeps heavy audio dependencies opt-in. Optional non-WAV probing follows that same principle while allowing stronger deployment hardening before untrusted external-user testing.

## Options Considered

### Option A: Keep default path dependency-light

Decision: still selected as the default behavior.

Behavior:

- WAV duration is checked with stdlib `wave`.
- MP3/M4A/MP4/WEBM keep byte-size validation only unless `IPU_AUDIO_DURATION_PROBER=ffprobe` is set.

Benefits:

- Keeps default CI lightweight.
- Avoids mandatory FFmpeg installation.
- Avoids additional subprocess failure modes in local demos.
- Preserves the existing opt-in philosophy for heavy audio processing.

Tradeoff:

- A non-WAV file under the byte-size limit may still be long in duration when the optional prober is disabled.

### Option B: Add `ffprobe` to the default path

Decision: not selected for the default path.

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

Decision: selected as the hardening path in #75.

Behavior:

- Keep default path dependency-light.
- Add `IPU_AUDIO_DURATION_PROBER=ffprobe` for deployments that need non-WAV duration validation.
- Add subprocess timeout and clear missing-tool behavior.

Benefits:

- Keeps default developer path simple.
- Allows stronger production hardening where needed.
- Aligns with the current Whisper opt-in pattern.

Costs:

- More configuration surface.
- Still needs optional setup guidance.
- Default CI does not validate real FFmpeg integration unless opt-in smoke tests are added later.

## Environment Setting

```text
IPU_AUDIO_DURATION_PROBER=none|ffprobe
```

| Value | Behavior |
| --- | --- |
| unset / `none` / `disabled` | WAV duration is checked; non-WAV keeps byte-size validation only. |
| `ffprobe` | MP3/M4A/MP4/WEBM duration is probed before STT. |

Recommended defaults:

| Environment | Recommended value | Notes |
| --- | --- | --- |
| Local default | unset / `none` | no FFmpeg dependency required. |
| CI default | unset / `none` | no FFmpeg dependency required. |
| Controlled demo | unset / `none` | acceptable when sample files are known. |
| Untrusted external upload | `ffprobe` if available | stronger validation before STT. |

## Error Behavior

| Condition | Status mapping | Notes |
| --- | --- | --- |
| Duration exceeds configured limit | 413 | Uses `ProcessingLimitExceededError`. |
| Audio file exceeds byte limit | 413 | Existing behavior. |
| Unsupported extension | 415 | Existing behavior. |
| Malformed WAV | Existing validation error | Current WAV path raises a clear parsing error. |
| Missing `ffprobe` when enabled | Existing validation error | Clear configuration/tooling error. |
| `ffprobe` timeout | 413 | Treated as processing-limit style guardrail rejection. |

## Testing Strategy

- Do not add large audio fixtures.
- Prefer mocking subprocess output for unit tests in follow-up work.
- Test timeout behavior without invoking a real long-running process.
- Keep real media probing smoke tests opt-in, similar to real Whisper smoke tests.
- Do not require FFmpeg in the default CI path unless the project explicitly changes the default dependency policy.

## Current Recommendation

For internal MVP and controlled demos:

- Keep WAV-only duration validation plus byte-size validation by default.
- Prefer known short demo samples.

Before untrusted external-user testing:

- Enable `IPU_AUDIO_DURATION_PROBER=ffprobe`.
- Ensure `ffprobe` is installed in the deployment image or host.
- Keep default CI dependency-light unless there is a clear product reason to change it.

## Relationship to Other Issues

- #75 tracks optional non-WAV audio duration probing implementation.
- #31 tracked the initial evaluation decision.
- #30 tracks upload timeout and concurrency design.
- #32 tracks broader compressed package inspection.
- #20 remains separate because address detection has high false-positive risk and should not be mixed with upload guardrail work.

## Acceptance Status

The default path remains dependency-light, and optional `ffprobe` probing is available for deployments that need non-WAV duration validation.
