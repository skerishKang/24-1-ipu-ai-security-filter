# 21. Owner-only Demo Secrets and Config Preparation

## Purpose

This document defines the preparation checklist for the first owner-only IPU AI Firewall demo environment.

It is intentionally preparation-only. It does not upload secrets, create hosting projects, create DNS records, apply branch protection, run a public deployment, or claim customer PoC readiness.

```text
ISSUE = #116
SCOPE = owner-only demo config/secret preparation
DEPLOYMENT_MUTATION = NO
SECRET_VALUE_COMMITTED = NO
HOSTING_PROJECT_CREATED = NO
DNS_CHANGE = NO
BRANCH_PROTECTION_MUTATION = NO
PRODUCTION_CLAIM = NO
```

## Current baseline

```text
SOURCE_REPOSITORY = skerishKang/24-1-ipu-ai-security-filter
SOURCE_MAIN_AT_PREP = 90204feb15c371aafd4a19ce8b7b189d25c19dcd
DEPLOYMENT_PLAN = docs/development/18-demo-ops-deployment-plan.md
BRANCH_PROTECTION_POLICY = docs/development/19-main-branch-protection-policy.md
OWNER_DEMO_UI_UX_REVIEW = docs/development/20-owner-demo-ui-ux-review.md
```

## Owner-only demo boundary

The first external environment is an owner-only demo stack.

```text
OWNER_ONLY_DEMO = YES
PUBLIC_MARKETING_LAUNCH = NO
CUSTOMER_POC_LAUNCH = NO
REAL_CUSTOMER_DATA = NO
AUTOMATIC_EXTERNAL_MODEL_CALLS = NO
```

The purpose is to prove that the current local MVP can run behind the public/ops guardrails with synthetic samples and controlled operator access.

## Required config matrix

The demo stack must use this matrix unless a later reviewed PR changes it.

```text
IPU_DEPLOYMENT_ENV = ops-target
IPU_MANUAL_PREVIEW_RESPONSE_MODE = minimized
IPU_API_KEY_HASH = secret manager only; required 64-character SHA-256 hex digest
IPU_ALLOWED_ORIGINS = exact owner-only frontend HTTPS origin
IPU_CORS_ALLOW_CREDENTIALS = false
IPU_CORS_ALLOW_METHODS = GET,POST
IPU_CORS_ALLOW_HEADERS = Content-Type,X-IPU-API-Key
IPU_PUBLIC_UPLOAD_MAX_BYTES = 20971520
IPU_UPLOAD_MAX_CONCURRENCY = 8
IPU_SESSION_TTL_SECONDS = 900
IPU_SESSION_STORE_KIND = sqlite
IPU_SESSION_STORE_PATH = target private persistent path, not repository path
IPU_AUDIO_TRANSCRIBER = placeholder
IPU_OLLAMA_ENABLED = false
```

## Placeholder values to decide outside GitHub

These values must be selected by the operator before actual deployment work, but the concrete secret values must not be pasted into GitHub, PRs, logs, or ChatGPT.

```text
FRONTEND_DEMO_ORIGIN = <exact HTTPS owner-only frontend origin>
BACKEND_DEMO_TARGET = <hosting provider/service name, non-secret>
BACKEND_PUBLIC_BASE_URL = <exact HTTPS backend base URL, non-secret if public>
SESSION_STORE_PATH = <private persistent server path>
RAW_OWNER_API_KEY = <generated out-of-band, never recorded>
IPU_API_KEY_HASH = <derived out-of-band, stored only in hosting secret manager>
```

Safe to record later:

```text
hosting class
non-secret project/service name
public frontend origin if intentionally shared
public backend base URL if intentionally shared
smoke result summary
```

Not safe to record:

```text
raw API key
API key hash value
.env contents
provider secret screenshots
private hostnames
session DB file contents
uploaded sample contents containing real sensitive data
```

## Secret generation runbook

Generate the raw key on the operator machine or the hosting provider secret UI. Do not generate it in a GitHub issue, PR comment, CI log, or ChatGPT message.

Recommended local pattern:

```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
```

Then hash it locally:

```bash
python - <<'PY'
import hashlib, getpass
raw = getpass.getpass('IPU raw API key: ')
print(hashlib.sha256(raw.encode('utf-8')).hexdigest())
PY
```

Operational rules:

```text
RAW_KEY_VISIBLE_ONLY_TO_OPERATOR = YES
HASH_VALUE_STORED_IN_SECRET_MANAGER_ONLY = YES
RAW_KEY_STORED_IN_PASSWORD_MANAGER_OR_OPERATOR_VAULT = YES
GITHUB_SECRET_VALUE_PASTE = NO
CHATGPT_SECRET_VALUE_PASTE = NO
CI_LOG_SECRET_VALUE_PRINT = NO
```

## Secret storage boundary

Use the chosen hosting provider's secret manager or environment-secret UI.

Required storage behavior:

```text
IPU_API_KEY_HASH stored as secret/env var on backend host only
IPU_ALLOWED_ORIGINS stored as exact allowed frontend origin
IPU_SESSION_STORE_PATH points outside repository checkout
runtime .env file, if used locally, is gitignored and never uploaded
```

Do not store `RAW_OWNER_API_KEY` in the backend host unless the final auth design explicitly requires it. The backend needs only `IPU_API_KEY_HASH`.

## Frontend/API-key delivery decision

This issue does not implement frontend auth. It records the decision point for the deployment phase.

Two possible approaches:

```text
A. owner manually enters API key in a local/session-only UI for short owner demo
B. same-origin proxy or access gateway injects/guards auth so browser code does not contain the raw key
```

Near-term rule:

```text
OWNER_ONLY_SHORT_DEMO_CAN_USE_MANUAL_KEY_INPUT = MAYBE
CUSTOMER_OR_PUBLIC_POC_SHOULD_USE_PROXY_OR_GATEWAY = YES
DO_NOT_COMMIT_RAW_KEY_IN_RUNTIME_CONFIG = YES
DO_NOT_PUT_RAW_KEY_IN_STATIC_JS = YES
```

## Session store policy

The SQLite session store contains restore mappings and must be treated as private runtime data.

```text
SESSION_STORE_KIND = sqlite
SESSION_STORE_PATH = private persistent path outside repository
SESSION_TTL_SECONDS = 900
SESSION_FILE_BACKUP = NO by default
SESSION_DB_PUBLIC_DOWNLOADABLE = NO
SESSION_DB_COMMITTED = NO
```

Recommended path pattern:

```text
Linux service host: /var/lib/ipu-ai-firewall/manual_preview_sessions.sqlite3
Container host: mounted private volume path
Local operator test: ./data/runtime/manual_preview_sessions.sqlite3 only for dev-local
```

## Preflight checklist before actual deployment mutation

Before creating or changing hosting settings, record a fresh checklist result without exposing secret values.

```text
MAIN_HEAD_CONFIRMED = YES
OPEN_PR_COUNT_CHECKED = YES
OPEN_ISSUE_CONTEXT_CHECKED = YES
BRANCH_PROTECTION_DECISION_REVIEWED = YES
FRONTEND_ORIGIN_SELECTED = YES
BACKEND_TARGET_SELECTED = YES
SESSION_STORE_PATH_SELECTED = YES
RAW_API_KEY_GENERATED_OUT_OF_BAND = YES
API_KEY_HASH_STORED_AS_SECRET = YES
ALLOWED_ORIGINS_EXACT = YES
PUBLIC_RESPONSE_MODE_MINIMIZED = YES
OPENAPI_PUBLIC_DISABLED_EXPECTED = YES
REAL_CUSTOMER_DATA_USED = NO
SYNTHETIC_SAMPLES_ONLY = YES
```

## Required smoke after deployment setup

The later deployment/smoke issue should verify these outcomes. This document does not execute them.

```text
OPS_TARGET_STARTUP_VALID_ENV = PASS
MISSING_API_KEY_HASH_FAILS_STARTUP = PASS
MISSING_ALLOWED_ORIGINS_FAILS_STARTUP = PASS
PUBLIC_HEALTH_MINIMIZED = PASS
PUBLIC_OPENAPI_DISABLED = PASS
MISSING_API_KEY_REQUEST = 401
INVALID_API_KEY_REQUEST = 403
VALID_API_KEY_TEXT_PREVIEW = 200
MINIMIZED_RESPONSE_OMITS_ORIGINAL_TEXT = PASS
RESTORE_WITH_VALID_TOKEN = PASS
RESTORE_WITH_INVALID_TOKEN = 403
CORS_ALLOWED_ORIGIN = PASS
CORS_UNLISTED_ORIGIN_REJECTED = PASS
```

## Main branch protection dependency

Main branch protection has been documented but not applied.

```text
MAIN_BRANCH_PROTECTION_POLICY_DEFINED = YES
MAIN_BRANCH_PROTECTION_APPLIED = NO
OWNER_APPROVAL_REQUIRED_BEFORE_SETTING_MUTATION = YES
```

Recommended order before public/customer PoC:

```text
1. Finish owner-only demo config preparation.
2. Decide whether to apply main protection before hosting mutation.
3. Apply settings only with owner approval.
4. Run owner-only demo smoke.
5. Share URL only after smoke acceptance.
```

## Acceptance mapping

```text
DEMO_CONFIG_MATRIX_CONFIRMED = YES
FRONTEND_ORIGIN_PLACEHOLDER_DEFINED = YES
BACKEND_TARGET_PLACEHOLDER_DEFINED = YES
SECRET_GENERATION_RUNBOOK_DEFINED = YES
SECRET_STORAGE_BOUNDARY_DEFINED = YES
SESSION_STORE_PATH_POLICY_DEFINED = YES
PREFLIGHT_CHECKLIST_DEFINED = YES
MAIN_PROTECTION_DEPENDENCY_RECORDED = YES
NO_SECRET_VALUE_COMMITTED = YES
NO_DEPLOYMENT_MUTATION = YES
```

## Next work

```text
1. Owner chooses frontend/backend hosting targets and secret manager.
2. Decide API key delivery strategy for owner-only demo.
3. Create owner-only demo smoke runbook.
4. Apply hosting/secret settings only after explicit owner approval.
```
