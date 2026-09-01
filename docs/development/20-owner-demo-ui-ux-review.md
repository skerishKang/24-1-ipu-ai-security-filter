# 20. Owner Demo UI/UX Review

## Purpose

This document defines the owner-demo UI/UX review checklist for IPU AI Firewall.

It separates product comprehension and presentation quality from deployment, authentication, secret storage, DNS, and public hosting work.

```text
ISSUE = #117
SCOPE = UI/UX owner-demo review only
DEPLOYMENT_MUTATION = NO
SECRET_OR_AUTH_MUTATION = NO
BACKEND_RUNTIME_CHANGE = NO
FRONTEND_RUNTIME_CHANGE = NO
```

## Current UI/UX readiness

```text
UI_UX_CORE_READY = YES
LOCAL_DEMO_UI_READY = YES
OWNER_REVIEW_READY = YES
PUBLIC_DEMO_AUTH_READY = NO, handled separately by ops work
```

The current product can already demonstrate the main value proposition locally:

```text
sensitive input
→ detect private/sensitive terms
→ replace with safe text
→ show risk/report evidence
→ copy a safe prompt to an external AI
→ optionally restore protected terms for the owner
```

The remaining UI/UX work is polish and demo framing, not a fundamental missing screen.

## Product story for owner demo

Use this short story:

> IPU AI Firewall is a workbench that lets a person prepare sensitive text, documents, or audio before using external AI. It detects risky private information, replaces it with safer tokens or aliases, gives the owner a review report, and produces a copy-ready prompt. The owner can keep the original mapping locally and restore protected terms when needed.

Avoid these claims in owner demo:

```text
PRODUCTION_CUSTOMER_READY = NO
REAL_CUSTOMER_DATA_APPROVED = NO
MEDICAL_OR_LEGAL_COMPLIANCE_GUARANTEE = NO
AUTOMATIC_EXTERNAL_AI_MODE_READY = NO
LONG_AUDIO_QUALITY_GUARANTEED = NO
```

## Recommended owner-demo sequence

```text
1. Open the main console in general-user mode.
2. Explain the one-sentence value: protect sensitive content before asking AI.
3. Use the default synthetic text.
4. Click the preview/generate button.
5. Show the protected text and protected-item count.
6. Expand original text only if the owner asks what changed.
7. Switch to expert mode.
8. Show detections, replacements, policy report, and copy-ready prompt.
9. Upload one synthetic text/document sample.
10. Show that file input uses the same protection flow.
11. Demonstrate restore as an owner/expert-only function.
12. Open template mode.
13. Show three approved templates.
14. Fill sample values.
15. Explain that approved templates create repeatable safe document drafting flows.
16. End with the boundary: local/owner demo is ready; public hosting/auth is a separate final ops step.
```

## Thirty-second comprehension test

A non-technical owner should understand these points within 30 seconds:

```text
WHAT_IT_IS = AI safety workbench before sending content to external AI
WHAT_IT_PROTECTS = names, contacts, organizations, amounts, and sensitive document context
WHAT_THE_USER_DOES = paste/upload content, generate protected version, copy result
WHY_IT_MATTERS = reduce accidental leakage while keeping work useful
WHAT_IS_NOT_READY = public/customer deployment and automatic AI forwarding
```

Pass condition:

```text
OWNER_CAN_EXPLAIN_PRODUCT_BACK_IN_ONE_SENTENCE = YES
OWNER_CAN_IDENTIFY_MAIN_BUTTON = YES
OWNER_CAN_FIND_PROTECTED_OUTPUT = YES
OWNER_CAN_TELL_GENERAL_MODE_FROM_EXPERT_MODE = YES
```

## General-user mode review

General-user mode should feel like the simple product surface.

Must be clear:

```text
INPUT_LOCATION_CLEAR = YES
PRIMARY_ACTION_CLEAR = YES
PROTECTED_OUTPUT_CLEAR = YES
PROTECTED_ITEM_COUNT_CLEAR = YES
COPY_RESULT_CLEAR = YES
ORIGINAL_TEXT_OPTIONAL = YES
INTERNAL_POLICY_DETAILS_HIDDEN = YES
SESSION_SOURCE_HIDDEN = YES
```

Review questions:

- Does the first screen explain the value without requiring developer knowledge?
- Is the primary button obvious?
- Does the output label say what the user can copy?
- Is the protected-item count reassuring rather than confusing?
- Does the UI avoid over-explaining policies to a general user?
- Are errors written as user actions rather than backend failures?

Recommended polish if needed:

```text
P1_GENERAL_COPY = simplify hero and status text
P1_RESULT_LABEL = make copy-ready output label more explicit
P2_GUIDED_STEP = add 1-2-3 explanation if owner feels lost
```

## Expert mode review

Expert mode should show evidence without becoming noisy.

Must be visible:

```text
DETECTION_LIST_VISIBLE = YES
REPLACEMENT_LIST_VISIBLE = YES
POLICY_OR_STRATEGY_VISIBLE = YES
REPORT_VISIBLE = YES
COPY_READY_PROMPT_VISIBLE = YES
SESSION_SOURCE_VISIBLE = YES
RESTORE_ACTION_VISIBLE = YES
```

Review questions:

- Does expert mode justify why the output is safer?
- Can a reviewer inspect what was detected and how it was replaced?
- Does the report avoid unsupported compliance claims?
- Is restore clearly owner/expert-only?
- Is the copy-ready prompt visually connected to the external-AI workflow?

Recommended polish if needed:

```text
P1_EXPERT_EXPLANATION = clarify report metric meanings
P1_RESTORE_WARNING = label restore as owner-only/local mapping function
P2_POLICY_HELP = add brief inline descriptions for default/strict_token/local_rewrite
```

## Text, file, and audio entry review

The three entry points should not overwhelm the owner.

```text
TEXT_ENTRY = primary
FILE_ENTRY = strong demo support
AUDIO_ENTRY = optional / short-audio only
```

Review questions:

- Is text input clearly the fastest demo path?
- Is file upload understandable without explaining parsers?
- Is binary `.hwp` unsupported behavior explained as conversion guidance, not failure?
- Is audio positioned as short audio support, not long-meeting transcription?
- Are upload errors actionable?

Demo recommendation:

```text
OWNER_DEMO_USE_TEXT_FIRST = YES
OWNER_DEMO_USE_ONE_FILE_SAMPLE = YES
OWNER_DEMO_AUDIO_OPTIONAL = YES
OWNER_DEMO_AVOID_LONG_AUDIO = YES
```

## Template mode review

Template mode should explain repeatability.

Message:

> Free-form mode protects whatever the user brings. Template mode gives a repeatable approved form so teams can collect the right inputs and generate a safer draft consistently.

Must be clear:

```text
APPROVED_TEMPLATE_CONCEPT_CLEAR = YES
THREE_TEMPLATES_VISIBLE = YES
SAMPLE_VALUE_FILL_CLEAR = YES
MISSING_FIELD_STATUS_CLEAR = YES
GENERATED_DRAFT_CLEAR = YES
```

Review questions:

- Does the owner understand why approved templates matter?
- Are the three templates enough for a short demo?
- Does sample-fill make the demo quick?
- Is missing-field feedback visible before sample-fill?
- Does generated draft look like a usable business artifact?

Approved demo templates:

```text
contract_review_request v1.1.0
customer_inquiry_intake v1.1.0
internal_report_weekly v1.1.0
```

## Sample scenario set

Use synthetic samples only.

Recommended short demo set:

```text
SAMPLE_1_TEXT = customer inquiry with name, phone, email, amount
SAMPLE_2_FILE = contract review request with company/contact/amount/deadline
SAMPLE_3_TEMPLATE = customer inquiry intake template
SAMPLE_4_OPTIONAL_TEMPLATE = internal weekly report template
SAMPLE_5_OPTIONAL_AUDIO = 5-15 second synthetic short audio only
```

Do not use:

```text
REAL_CUSTOMER_DOCUMENT = NO
REAL_RESIDENT_OR_APARTMENT_DATA = NO
REAL_MEDICAL_RECORD = NO
REAL_LEGAL_CASE_DOCUMENT = NO
LONG_MEETING_AUDIO = NO
```

## Mock fallback presentation decision

Mock fallback is acceptable for owner UI/UX review because it proves the screen state and interaction flow.

However, it must not be presented as live backend or production evidence.

```text
MOCK_FALLBACK_ACCEPTABLE_FOR_UI_REVIEW = YES
MOCK_FALLBACK_ACCEPTABLE_FOR_PRODUCTION_EVIDENCE = NO
MOCK_FALLBACK_SHOULD_BE_VISIBLY_MARKED = YES
```

Recommended owner-demo wording:

> If the backend is not running, the screen can show a mock fallback so we can still review the UI. Live backend verification is a separate test.

## Unsupported claims to remove or flag

Check all demo narration and documents for these phrases or implications:

```text
fully production ready
guaranteed privacy compliance
medical-grade de-identification
legal guarantee
automatic safe forwarding to all AIs
long meeting audio ready
customer data approved
multi-user enterprise admin ready
```

Allowed safer wording:

```text
owner-demo ready
local MVP ready
manual protection workflow ready
synthetic PoC sample ready
public deployment requires final ops/auth setup
```

## UI/UX polish priority

```text
P0 = no known core UI blocker for owner review
P1 = owner demo script and copy/status wording review
P1 = make mock/live status visually obvious
P1 = clarify restore as owner/expert-only
P1 = clarify template mode value in one sentence
P2 = responsive/readability pass on owner demo devices
P2 = accessibility pass for labels, focus, and contrast
P3 = brand polish after owner accepts product flow
```

## Review acceptance

```text
OWNER_DEMO_FLOW_DEFINED = YES
GENERAL_MODE_REVIEWED = YES
EXPERT_MODE_REVIEWED = YES
TEMPLATE_MODE_REVIEWED = YES
COPY_AND_STATUS_MESSAGE_REVIEWED = YES
SAMPLE_SCENARIO_SET_DEFINED = YES
MOCK_FALLBACK_PRESENTATION_DECISION = YES
UNSUPPORTED_CLAIMS_REMOVED_OR_FLAGGED = YES
UI_UX_POLISH_ITEMS_PRIORITIZED = YES
NO_DEPLOYMENT_MUTATION = YES
NO_SECRET_OR_AUTH_MUTATION = YES
```

## Next work after this document

```text
1. Owner reviews UI using this script.
2. If owner feedback is mostly wording/layout, create a small UI copy polish PR.
3. If owner accepts the flow, return to #116 demo config/secret preparation.
4. Public/demo URL work remains blocked until ops/auth setup is completed.
```
