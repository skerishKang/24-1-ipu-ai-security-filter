# 41. Session History API

## 개요

세션 히스토리 API는 세션 저장이 SQLite 모드에서만 동작하며, 세션의 목록과 메타데이터를 조회할 수 있다.

## 사전 조건

- `IPU_SESSION_STORE_KIND=sqlite` (기본값)
- 백엔드 실행: `cd backend && python -m uvicorn app.main:app --reload`
- 기본 포트: `8241`

## 세션 생성

```bash
curl -X POST http://localhost:8241/api/v1/mode/manual-preview \
  -H "Content-Type: application/json" \
  -d '{"content": "김철수 대표 (02-1234-5678) test@example.com", "policy": "default"}'
```

**응답 예시:**
```json
{
  "session_id": "ipu-20240315-abcdef",
  "original_text": "김철수 대표 (02-1234-5678) test@example.com",
  "replaced_text": "__PERSON_0__ 대표 (__PHONE_0__) __EMAIL_0__",
  "detections": [...],
  "replacements": [
    {"type": "PERSON", "original": "김철수", "replaced": "__PERSON_0__", "reason": "담당자 실명 보호"},
    {"type": "PHONE", "original": "02-1234-5678", "replaced": "__PHONE_0__", "reason": "연락처 직접 노출 방지"},
    {"type": "EMAIL", "original": "test@example.com", "replaced": "__EMAIL_0__", "reason": "이메일 주소 보호"}
  ],
  "report": {...},
  "copy_ready_prompt": "..."
}
```

## 세션 목록 조회

**Endpoint:** `GET /api/v1/sessions`

```bash
curl http://localhost:8241/api/v1/sessions
```

**응답 예시:**
```json
[
  {"session_id": "ipu-20240315-abcdef", "expires_at": 1710500000.123},
  {"session_id": "ipu-20240315-xyz123", "expires_at": 1710499999.456}
]
```

- 기본 limit: 50
- 만료된 세션은 자동으로 필터링됨

## 세션 메타데이터 조회

**Endpoint:** `GET /api/v1/sessions/{session_id}`

```bash
curl http://localhost:8241/api/v1/sessions/ipu-20240315-abcdef
```

**응답 예시:**
```json
{
  "session_id": "ipu-20240315-abcdef",
  "mapping_count": 3,
  "expires_at": 1710500000.123
}
```

**에러: 세션이 없는 경우**
```json
{"detail": "Session not found"}
```

## Mappings 조회

**Endpoint:** `GET /api/v1/sessions/{session_id}/mappings`

```bash
curl http://localhost:8241/api/v1/sessions/ipu-20240315-abcdef/mappings
```

**응답 예시:**
```json
{
  "session_id": "ipu-20240315-abcdef",
  "mapping_count": 3,
  "mappings": [
    {"type": "PERSON", "replaced": "__PERSON_0__"},
    {"type": "PHONE", "replaced": "__PHONE_0__"},
    {"type": "EMAIL", "replaced": "__EMAIL_0__"}
  ]
}
```

**주의:** `original` 필드는 보안상 API 응답에서 제외됨. 내부 복원에는 사용되지만 외부 노출은 안 함.

## 모드별 동작 차이

| 설정 | session_history API | 설명 |
|------|---------------------|------|
| `IPU_SESSION_STORE_KIND=sqlite` (기본) | 정상 동작 | 세션이 DB에 persisted, 재시작 후에도 조회 가능 |
| `IPU_SESSION_STORE_KIND=memory` | 503 에러 | 프로세스 종료 시 데이터 소멸, 히스토리 의미 없음 |

**memory 모드에서 접근 시:**
```json
{"detail": "세션 히스토리 API는 SQLite 모드에서만 지원됩니다. IPU_SESSION_STORE_KIND=sqlite로 설정해 주세요."}
```

## TTL (Time To Live)

- 기본: 900초 (15분)
- 설정: `IPU_SESSION_TTL_SECONDS`
- TTL 이후 세션은 자동으로 삭제됨 (조회 불가)

## 운영 체크리스트

1. [ ] 백엔드 정상 실행 확인 (`GET /health`)
2. [ ] 세션 생성 후 session_id 기록
3. [ ] `GET /api/v1/sessions`으로 목록 조회 가능 확인
4. [ ] 특정 세션 `GET /api/v1/sessions/{id}` 조회 가능 확인
5. [ ] mappings 조회 시 original 미노출 확인

## Related Docs

- [15-logging-and-audit-scope.md](./15-logging-and-audit-scope.md)
- [02-system-architecture.md](./02-system-architecture.md)
