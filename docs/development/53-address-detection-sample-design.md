# Address Detection Sample Design

## Purpose

This document records the sample-driven design for Issue #20. Address detection should be designed with a representative fake corpus before any detector is added.

This is a design document only. It does not implement address detection.

## Current Decision

Do not add a regex-only address detector directly to the default detection path.

Address-like text has a high false-positive risk because ordinary place names, organization names, road names, building names, and administrative terms can look like addresses without being personal data in context.

The first implementation step should be a fake-sample corpus and acceptance criteria. Detector code should follow only after the sample set is reviewed.

## Scope

Address detection is considered only for explicit privacy-sensitive policies:

| Policy | Initial posture | Rationale |
| --- | --- | --- |
| `strict_token` | Candidate after sample review | Best fit for high-sensitivity token detection. |
| `local_rewrite` | Candidate after sample review | May help local rewriting if precision is acceptable. |
| `default` | Do not enable initially | False positives would harm ordinary text use. |

## Non-goals

- Do not use real addresses in tests or documentation.
- Do not add broad location detection.
- Do not classify every city, district, street, institution, or landmark as sensitive.
- Do not enable address detection in `default` policy without a separate decision.
- Do not rely on one large regular expression without sample-backed precision checks.

## Fake Sample Corpus Design

Use fake examples only. The corpus should separate positive, negative, and boundary cases.

### Positive samples

Positive samples should represent text that looks like a user-specific location or delivery/contact address.

Example shapes, using fictional values only:

- `Fictional City Sample District Sample-ro 12, Sample Building 301`
- `Sample Province Sample City Sample-gu Sample-gil 45-6`
- `Sample Apt 101-202, Sample-dong, Example City`

Positive samples should cover:

- road-name style text;
- lot-number style text;
- apartment, building, or unit details;
- English-style address fragments;
- mixed Korean and English formatting if supported later.

### Negative samples

Negative samples should be ordinary text that must not be flagged.

Examples:

- product names that include a place word;
- institution names;
- news text mentioning a city or district only;
- general travel descriptions;
- public office or agency names;
- road names without user-specific delivery context;
- company names that include location-like words.

### Boundary samples

Boundary samples should be difficult cases that guide future implementation limits.

Examples:

- a building name without unit number;
- a street name without city or district;
- a city and district pair only;
- a postal-code-like number without address context;
- a meeting place or landmark;
- a fake address embedded inside a longer sentence.

## Detection Principles

Address detection should prefer precision over recall.

Recommended principles:

1. Require multiple address-like components before flagging.
2. Treat unit, building, road, and lot markers as supporting signals, not standalone proof.
3. Avoid flagging single place names.
4. Avoid flagging organization names merely because they include administrative words.
5. Keep Korean and English address handling explicit and testable.
6. Require separate review before enabling the detector in `default` policy.

## Implementation Shape for a Future PR

If implementation follows, prefer a small helper with a narrow contract.

Possible shape:

- Add address-pattern helpers to the existing sensitive pattern detector module.
- Gate the detector to `strict_token` and optionally `local_rewrite` first.
- Keep `default` unchanged.
- Keep patterns decomposed into readable components.
- Add tests before enabling broader behavior.

The future implementation should be separate from this design PR.

## Test Strategy

Tests should use only fake samples.

Recommended tests:

- positive fake road-name address is detected under `strict_token`;
- positive fake apartment or unit address is detected under `strict_token`;
- negative institution or place-name examples are not detected;
- negative city-only or district-only examples are not detected;
- `default` policy remains unchanged;
- `local_rewrite` behavior is explicit and separately asserted;
- no real personal address appears in fixtures.

## Acceptance Criteria

This design is acceptable when it documents:

- why regex-only direct implementation is unsafe;
- fake sample corpus categories;
- policy boundaries for `strict_token`, `local_rewrite`, and `default`;
- no-real-address testing rules;
- future implementation boundaries.

After this document is merged, Issue #20 can be treated as design-complete if the issue scope is design-only. If detector implementation is desired, open a follow-up implementation issue and keep it separate from this design PR.
