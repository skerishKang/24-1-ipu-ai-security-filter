# 18. Demo And Ops Deployment Plan

## 목적

이 문서는 IPU AI Firewall의 첫 외부 demo/PoC 배포 계획을 고정한다.

이 PR은 planning-only 변경이다. 실제 배포, DNS, secret 업로드, GitHub Environment 생성, Cloudflare/hosting 설정 변경은 하지 않는다.

## 현재 결론

첫 외부 노출은 production이 아니라 `demo-stack`으로 둔다.

```text
DEPLOYMENT_TARGET_SELECTED = YES
SELECTED_TARGET = demo-stack
EXTERNAL_SURFACE = owner-only demo first
CUSTOMER_POC = after owner smoke and explicit approval
PRODUCTION_CLAIM = NO
```

이 단계의 목표는 공개 제품 출시가 아니라, synthetic PoC 샘플과 approved template 3개를 기준으로 안전하게 시연 가능한 최소 surface를 확보하는 것이다.

## 배포 표면

### Frontend

```text
FRONTEND_HOSTING_PLAN = YES
HOSTING_CLASS = static hosting
PREFERRED_TARGET = Cloudflare Pages or equivalent static host
PUBLIC_PATHS = /, /frontend/template-mode.html, static JS/CSS/assets, approved template JSON reads
AUTH_AT_FRONTEND = not relied on for security
```

Frontend는 정적 파일로 배포한다. 보안 경계는 frontend가 아니라 backend API key hash, CORS allowlist, minimized response, secret handling에서 잡는다.

첫 demo URL은 owner-only 공유를 기본값으로 하며, public indexing이나 광고성 공개는 하지 않는다.

### Backend

```text
BACKEND_HOSTING_PLAN = YES
HOSTING_CLASS = single HTTPS web service
PREFERRED_TARGET = managed web service or container host
APP_ENTRYPOINT = uvicorn app.main:app --app-dir backend
PORT = platform-provided port mapped to internal app server
PUBLIC_API_SURFACE = /health and /api/v1/mode/manual-preview* only
```

Backend는 단일 웹 서비스로 띄운다. 첫 demo 단계에서는 sqlite session store를 허용하되, 데이터 보존은 restore 가능 시간에 한정하고 장기 문서 저장소로 사용하지 않는다.

## 환경 값 선택

첫 demo는 아래 값을 사용한다.

```text
IPU_DEPLOYMENT_ENV = ops-target
IPU_MANUAL_PREVIEW_RESPONSE_MODE = minimized
IPU_API_KEY_HASH = required 64-char SHA-256 hex digest
IPU_ALLOWED_ORIGINS = exact frontend demo origin only
IPU_CORS_ALLOW_CREDENTIALS = false
IPU_CORS_ALLOW_METHODS = GET,POST
IPU_CORS_ALLOW_HEADERS = Content-Type,X-IPU-API-Key
IPU_PUBLIC_UPLOAD_MAX_BYTES = 20971520
IPU_UPLOAD_MAX_CONCURRENCY = 8
IPU_SESSION_TTL_SECONDS = 900
IPU_SESSION_STORE_KIND = sqlite
IPU_SESSION_STORE_PATH = platform persistent/private path, not repo path
IPU_AUDIO_TRANSCRIBER = placeholder
IPU_OLLAMA_ENABLED = false
```

`ops-target`을 선택하는 이유는 다음과 같다.

- public/ops guardrail을 강제한다.
- `IPU_ALLOWED_ORIGINS` 누락 시 시작 실패가 발생한다.
- `IPU_API_KEY_HASH` 누락 또는 잘못된 hash 형식을 시작 단계에서 차단한다.
- `/docs`, `/redoc`, `/openapi.json`가 외부 노출되지 않는다.
- `manual-preview` 응답이 minimized mode로 제한된다.

## API key 운영

```text
API_KEY_STORAGE = hosting secret manager only
RAW_API_KEY_IN_REPO = NO
RAW_API_KEY_IN_LOGS = NO
HASH_IN_REPO = NO
HASH_ALGORITHM = SHA-256
ROTATION_POLICY = regenerate raw key, replace hash secret, invalidate old key manually
```

운영자는 raw API key를 직접 저장하지 않고 SHA-256 hex digest만 `IPU_API_KEY_HASH` secret으로 설정한다. 원문 key, hash 값, secret 이름별 실제 값은 GitHub issue/PR/document에 기록하지 않는다.

## CORS 기준

```text
ALLOWED_ORIGINS_EXPLICIT = YES
ALLOW_LOCALHOST_IN_DEMO = NO
ALLOW_WILDCARD_ORIGIN = NO
ALLOW_CREDENTIALS = false by default
```

첫 demo에서는 frontend HTTPS origin 하나만 허용한다. `http://localhost:4241`와 `http://127.0.0.1:4241`는 dev-local 전용이며 demo/ops에는 포함하지 않는다.

## 공개 보안 guardrails

```text
PUBLIC_RESPONSE_MODE = minimized
PUBLIC_API_KEY_HASH_REQUIRED = yes
ALLOWED_ORIGINS_EXPLICIT = yes
OPENAPI_PUBLIC_DISABLED = yes
REAL_CUSTOMER_DATA_IN_DEMO = no
SENSITIVE_TEXT_LOGGING = no
RESTORE_TOKEN_HANDLING_REVIEWED = yes
UPLOAD_LIMITS_REVIEWED = yes
AUTOMATIC_EXTERNAL_MODEL_CALLS = disabled
```

첫 demo에 사용할 자료는 `docs/development/13-poc-sample-corpus-and-template-set.md`의 synthetic/redacted 기준을 따른다.

## 허용 로그

허용 로그는 운영 메타데이터로 제한한다.

```text
request_type
policy
content_type
session_id
detection_count
replacement_count
report_strategy
processing_ms
error_type
```

## 금지 로그

```text
original_text
replaced_text full body
copy_ready_prompt full body
raw detected values
email/phone/name/address/account/card/raw money values
uploaded file body
uploaded original filename when it may contain sensitive data
restore token value
raw API key
IPU_API_KEY_HASH value
```

## Demo smoke checklist

외부 URL을 공유하기 전 아래 smoke를 통과해야 한다.

```text
DEMO_SMOKE_CHECKLIST_DEFINED = YES
```

### Backend startup

```text
OPS_TARGET_STARTUP_WITH_VALID_ENV = PASS
MISSING_IPU_API_KEY_HASH_FAILS_STARTUP = PASS
INVALID_IPU_API_KEY_HASH_FAILS_STARTUP = PASS
MISSING_IPU_ALLOWED_ORIGINS_FAILS_STARTUP = PASS
PUBLIC_OPENAPI_DISABLED = PASS
PUBLIC_HEALTH_MINIMIZED = PASS
```

### Manual preview

```text
UNAUTHENTICATED_MANUAL_PREVIEW = 401
INVALID_API_KEY_MANUAL_PREVIEW = 403
VALID_API_KEY_TEXT_PREVIEW = 200
MINIMIZED_RESPONSE_HAS_NO_RAW_ORIGINAL_TEXT = PASS
STRICT_TOKEN_SAMPLE_PREVIEW_COMPLETES = PASS
RESTORE_WITH_VALID_TOKEN = PASS
RESTORE_WITH_INVALID_TOKEN = 403_OR_404
```

### File upload

```text
TXT_SAMPLE_UPLOAD = PASS
DOCX_OR_HWPX_SAMPLE_UPLOAD = PASS_IF_SUPPORTED_IN_TARGET
PDF_TEXT_SAMPLE_UPLOAD = PASS_IF_PARSER_READY
OVERSIZE_UPLOAD_REJECTED = PASS
UNSUPPORTED_HWP_BINARY_SHOWS_GUIDANCE = PASS
```

### Template mode

```text
TEMPLATE_MODE_PAGE_LOADS = PASS
APPROVED_TEMPLATE_PICKER_LOADS_3 = PASS
FORM_FIELDS_RENDER = PASS
SAMPLE_VALUES_FILL = PASS
DRAFT_RECONSTRUCTION = PASS
XSS_SAFE_TEMPLATE_VALUES = PASS
STATE_RESETS_ON_TEMPLATE_SWITCH = PASS
```

### CORS and frontend integration

```text
FRONTEND_DEMO_ORIGIN_CAN_CALL_BACKEND = PASS
UNLISTED_ORIGIN_REJECTED = PASS
LOCALHOST_NOT_ALLOWED_IN_DEMO = PASS
```

## Demo sharing gate

첫 URL 공유 전 gate는 아래와 같다.

```text
OWNER_ONLY_SMOKE_PASS = REQUIRED
REAL_CUSTOMER_DATA_USED = NO
API_KEY_SHARED_OUT_OF_BAND = YES
RAW_SECRET_IN_GITHUB = NO
LOG_SAMPLE_REVIEWED_FOR_NO_RAW_PII = YES
DEPLOYMENT_CONFIG_REVIEWED = YES
OWNER_APPROVAL_TO_SHARE_URL = REQUIRED
```

## Production과 구분

이 계획은 production release가 아니다.

```text
PRODUCTION_DEPLOYMENT = NO
CUSTOM_DOMAIN_DNS_CHANGE = NO
PUBLIC_MARKETING_LAUNCH = NO
CUSTOMER_DATA_PROCESSING = NO
SLA_OR_ENTERPRISE_ADMIN = NO
```

Production 또는 customer PoC로 승격하려면 별도 issue/PR에서 아래를 결정해야 한다.

- 사용자 인증/조직 권한 모델
- 감사 로그와 retention 정책
- session store를 sqlite로 유지할지 외부 DB로 옮길지
- secret rotation 절차
- 고객사별 allowed origin과 배포 경계
- 실제 고객 데이터 처리 계약/동의/보관 기준

## Acceptance mapping

```text
DEPLOYMENT_TARGET_SELECTED = YES
FRONTEND_HOSTING_PLAN = YES
BACKEND_HOSTING_PLAN = YES
ENVIRONMENT_VARIABLE_MATRIX = YES
PUBLIC_SECURITY_GUARDRAILS_RECORDED = YES
DEMO_SMOKE_CHECKLIST_DEFINED = YES
NO_DEPLOYMENT_MUTATION_IN_PLANNING_PR = YES
```

## 다음 작업

이 문서가 merge되면 다음 순서는 다음 중 하나다.

1. 실제 demo environment secret/config 준비 issue 생성
2. main branch protection 적용 여부 결정
3. owner-only demo smoke용 local/deployment runbook 작성
