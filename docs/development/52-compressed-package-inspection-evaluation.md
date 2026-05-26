# Compressed Package Inspection Evaluation

## Purpose

This document records the evaluation decision for Issue #32: whether broader compressed package inspection should be added beyond the primary DOCX/HWPX XML guardrails already implemented.

This is a design and evaluation document only. It does not implement broader package-level inspection by itself.

## Background

The current upload guardrail baseline already includes targeted protection for the supported archive-based office formats:

- #27 checks DOCX `word/document.xml` uncompressed entry size before reading the XML content.
- #27 checks HWPX `Contents/section*.xml` entry size, total section XML size, and section XML file count before reading section content.
- #27 changed HWPX parsing to read and parse section XML files sequentially instead of accumulating every section XML file in a list.

These controls protect the primary content paths used by the current parser implementation.

Issue #32 asks whether the project should add broader package-level inspection for archive structures, suspicious compression ratios, entry counts, and non-primary entries.

## Current Decision

Do not add broad package-level zip heuristics to the lightweight default path yet.

Keep the current default behavior:

1. Enforce the existing upload byte limit.
2. Validate the primary DOCX/HWPX XML entries used by the parser.
3. Avoid large or malicious archive fixtures in the repository.
4. Treat broader package inspection as deployment hardening that should be enabled only after the exact risk model is clear.

## Rationale

A generic zip/package inspection layer can be useful, but it is easy to make too broad or too brittle.

Risks of adding broad heuristics immediately:

- False positives on valid office files with many internal entries.
- Format-specific differences between DOCX and HWPX package layouts.
- Extra complexity around nested directories, media entries, styles, fonts, metadata, and preview assets.
- Tests may accidentally encourage adding large or hostile archive fixtures.
- A generic zip bomb detector can become a second parser with unclear ownership and maintenance cost.

The current parsers only need specific XML content paths. Guarding those paths first is safer and easier to validate.

## Options Considered

### Option A: Keep targeted XML guardrails only

Decision: selected for now.

Behavior:

- DOCX guards `word/document.xml` before reading.
- HWPX guards `Contents/section*.xml` count, individual size, and total size before reading.
- Broader package-level heuristics remain deferred.

Benefits:

- Minimal false-positive risk.
- Directly protects the current parser read paths.
- Keeps implementation simple and testable.
- Avoids large or malicious fixtures.

Tradeoff:

- Non-primary archive entries are not deeply inspected beyond the outer upload byte limit.

### Option B: Add default package-level heuristics

Decision: not selected for now.

Possible checks:

- Total uncompressed package size.
- Archive entry count.
- Per-entry uncompressed size.
- Compression ratio threshold.
- Nested archive detection.
- Deny suspicious paths or unsupported package layouts.

Benefits:

- Stronger protection against unusual archive structures.
- Better fit for untrusted public upload environments.

Costs:

- More tuning required.
- Higher risk of blocking valid documents.
- More format-specific edge cases.
- Harder to keep lightweight and explainable.

### Option C: Add optional package inspection behind configuration

Decision: possible future direction.

Behavior:

- Keep default parser behavior targeted and lightweight.
- Add an optional package inspection layer for untrusted external deployments.
- Use conservative thresholds and format-specific allowlists.

Benefits:

- Allows stronger deployment hardening when needed.
- Keeps internal MVP and controlled demos simple.
- Lets thresholds be tuned using real sample files before enforcement.

Costs:

- Requires configuration and documentation.
- Requires careful test design with small fake archives and monkeypatch limits.
- Requires clear distinction between warnings and hard rejection.

## Recommended Future Implementation

If broader package inspection is needed later, prefer Option C.

Recommended shape:

- Add a small `ArchiveInspectionPolicy` or similar helper.
- Keep format-specific policies for DOCX and HWPX rather than one opaque global rule.
- Start with dry-run or warning mode if real-world samples are limited.
- Enforce only after thresholds are validated against representative fake and safe sample files.
- Keep tests small by monkeypatching thresholds rather than committing large archives.

Potential checks:

| Check | Recommended default posture | Notes |
| --- | --- | --- |
| Total entry count | Optional | Useful, but valid office packages may contain many support files. |
| Total uncompressed size | Optional | Should be tuned by format. |
| Per-entry size | Already targeted for primary XML | Broader per-entry checks need allowlists. |
| Compression ratio | Optional/dry-run first | High ratio alone may cause false positives. |
| Nested archive detection | Optional | More relevant if nested archives become supported. |
| Path traversal entries | Good candidate | Should reject unsafe paths if extraction is ever introduced. |

## Current Guarded Paths

### DOCX

Implemented guardrail:

- `word/document.xml` uncompressed size is checked before `archive.read()`.

Current boundary:

- Other package entries such as media, styles, numbering, relationships, and metadata are not deeply inspected by default.
- This is acceptable for the current parser because it only reads the main document XML content.

### HWPX

Implemented guardrails:

- Section XML file count limit.
- Individual section XML size limit.
- Total section XML size limit.
- Sequential read/parse for section XML files.

Current boundary:

- Non-section package entries are not deeply inspected by default.
- This is acceptable for the current parser because it only reads `Contents/section*.xml` for body text extraction.

## Error Behavior

If optional package inspection is implemented later:

| Condition | Recommended status | Notes |
| --- | --- | --- |
| Package-level processing limit exceeded | 413 | Use `ProcessingLimitExceededError`. |
| Unsupported or malformed archive | 400 or existing parser error | Preserve current parser semantics where possible. |
| Unsupported file type | 415 | Existing behavior. |
| Suspicious but not blocked package | No user-facing error in dry-run mode | Log only if safe and privacy-preserving. |

## Testing Strategy

If implementation follows later:

- Do not add large or malicious archive fixtures.
- Use small fake ZIP fixtures.
- Monkeypatch thresholds to very small values.
- Test each heuristic independently.
- Avoid real zip bomb samples.
- Avoid real personal documents.
- Ensure tests use fake content only.

Recommended test cases:

- Entry count exceeds monkeypatched limit.
- Total uncompressed size exceeds monkeypatched limit.
- Compression ratio warning or rejection behavior.
- Safe small DOCX/HWPX package remains accepted.
- Existing targeted XML guardrail behavior remains unchanged.

## Current Recommendation

For internal MVP and controlled demos:

- Keep current targeted DOCX/HWPX XML guardrails.
- Do not add broad package inspection to the default path yet.
- Use known safe sample documents.

Before untrusted external-user testing:

- Decide whether optional package inspection is required.
- If required, implement it behind explicit configuration or a deployment hardening mode.
- Tune thresholds with representative safe samples.
- Keep large or hostile archives out of the repository.

## Relationship to Other Issues

- #32 tracks broader compressed package inspection.
- #31 tracks non-WAV audio duration probing.
- #30 tracks upload timeout and concurrency design.
- #20 remains separate because address detection has high false-positive risk and should not be mixed with upload guardrail work.

## Acceptance Status

This document satisfies the evaluation-first requirement for #32. Implementation should be done in a separate PR only if broader package inspection becomes necessary for an external deployment mode.
