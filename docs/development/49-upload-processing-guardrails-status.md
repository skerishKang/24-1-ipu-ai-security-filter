# Upload Processing Guardrails Status

## Purpose

This document tracks the current implementation status of upload processing guardrails for manual-preview file and audio intake.

This is a status and operating-boundary document for Issue #5. It does not close Issue #5 by itself.

## Current Status

Issue #5 remains open.

Completed implementation slices:

| PR | Scope | Status |
| --- | --- | --- |
| #26 | PDF page limit, OCR page limit, OCR subprocess timeout, 413 mapping | Merged |
| #27 | DOCX document XML size limit, HWPX section XML entry/total/count limits, sequential HWPX section parsing | Merged |
| #28 | WAV duration limit using Python stdlib `wave`, audio 413 mapping | Merged |

## Implemented Guardrails

### General upload size

- Existing upload byte limit remains in place.
- File upload paths reject inputs over the configured byte limit.
- Audio upload path rejects inputs over the configured byte limit.

### PDF and OCR

Implemented:

- `MAX_PDF_PAGES = 50`
- `MAX_OCR_PAGES = 5`
- `OCR_TOOL_TIMEOUT_SECONDS = 15`
- PDF page count is checked before page text extraction.
- OCR page count is checked before entering the heavy OCR fallback path.
- OCR subprocess calls use timeout handling.
- Processing limit failures map to HTTP 413.

Operational boundary:

- OCR depends on local `pdftoppm` and `tesseract` availability.
- Missing OCR toolchain is still treated as unsupported processing guidance rather than a processing-limit failure.

### DOCX

Implemented:

- `word/document.xml` uncompressed entry size is checked before `archive.read()`.
- Oversized DOCX XML entries raise `ProcessingLimitExceededError`.

Operational boundary:

- This guardrail protects the main document XML entry.
- Broader Office package-level zip bomb detection is not yet implemented.

### HWPX

Implemented:

- HWPX section XML file count limit.
- HWPX section XML individual entry size limit.
- HWPX section XML total size limit.
- HWPX section XML files are parsed sequentially instead of being accumulated in a list.

Operational boundary:

- Current guardrails focus on `Contents/section*.xml`.
- Broader package-level validation for non-section entries is not yet implemented.

### Audio

Implemented:

- WAV duration is checked using Python stdlib `wave`.
- `MAX_AUDIO_DURATION_SECONDS = 60`
- Over-limit WAV uploads raise `ProcessingLimitExceededError`.
- Audio route maps processing-limit failures to HTTP 413.

Operational boundary:

- MP3, M4A, MP4, and WEBM duration extraction is intentionally not implemented yet.
- No `ffprobe` or `ffmpeg` dependency is introduced in the default path.

## Remaining Work

Issue #5 remains open for the following items:

| Area | Current Decision | Rationale |
| --- | --- | --- |
| Whole-request processing timeout | Deferred | Needs careful design around async cancellation, thread work, OCR subprocesses, and Whisper execution. |
| Concurrent upload limit | Deferred | Should be designed at app/middleware/deployment level rather than parser-only level. |
| MP3/M4A/MP4/WEBM duration limit | Deferred | Reliable duration extraction likely needs external media tooling such as `ffprobe`; not introduced in the default lightweight path. |
| Broader zip/package-level inspection | Deferred | Current DOCX/HWPX guardrails cover primary XML paths; broader zip bomb heuristics should be designed separately. |

## Current Recommendation

For internal MVP and controlled demos, the current guardrails are sufficient for basic file and WAV audio intake.

Before untrusted external-user testing or public deployment, complete or explicitly accept the risk for:

1. Whole-request processing timeout.
2. Concurrent upload limit.
3. Non-WAV audio duration validation.
4. Broader compressed package inspection.

## Issue Tracking

- Keep Issue #5 open until the remaining deployment-level decisions are made.
- Keep Issue #20 separate. Address detection has high false-positive risk and must not be mixed with upload guardrail work.
