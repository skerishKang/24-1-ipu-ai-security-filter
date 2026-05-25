# 48. Restore API Security Policy

## 목적

이 문서는 `/api/v1/mode/manual-preview/restore` API를 어떤 보안 기준으로 다룰지 정리한다.

restore API는 단순 조회 API가 아니다. `session_id`와 치환된 텍스트를 받아 세션 저장소에 남아 있는 매핑을 이용해 원문 민감정보를 복원할 수 있는 경로다. 따라서 로컬 MVP에서는 개발 편의를 위해 열어둘 수 있지만, 외부 데모나 운영 배포에서는 인증, 세션 소유권, 감사 기준이 먼저 정리되어야 한다.

## 현재 결론

현재 restore API는 아래처럼 구분한다.

1. `dev-local`
   - 단일 사용자 개발과 테스트를 위한 허용 경로
   - 별도 인증 없이 세션 TTL 안에서 restore 가능
   - 외부 네트워크 노출 금지

2. `demo-stack`
   - 제한된 시연 환경
   - 접근 URL과 사용자 범위를 통제하는 경우에만 허용
   - 시연 데이터는 가짜 또는 비식별 샘플을 사용

3. `ops-target`
   - 실제 고객사 또는 사설망 운영 환경
   - 인증, 사용자별 세션 소유권, 감사 로그, TTL/삭제 정책이 구현되기 전에는 restore API를 그대로 노출하지 않는다

## 현재 API 동작

현재 구현은 다음 전제를 가진다.

- preview 요청에서 생성된 `session_id`를 기준으로 세션 저장소에 치환 매핑을 보관한다.
- restore 요청은 `session_id`와 `replaced_text`를 받아 매핑이 있으면 원문을 복원한다.
- 매핑이 없으면 입력된 `replaced_text`를 그대로 반환하고 `restored=false`로 응답한다.
- 세션 저장소 TTL은 기본 900초다.
- SQLite 세션 저장소를 쓰면 백엔드 재시작 뒤에도 TTL 범위 안에서는 restore가 가능하다.

이 구조는 MVP 테스트에는 충분하지만, 외부 사용자 환경에서는 `session_id`가 사실상 복원 권한처럼 작동할 수 있다.

## 위험 모델

restore API에서 특히 주의해야 할 위험은 아래와 같다.

### 1. session_id 추측 또는 유출

`session_id`가 외부로 노출되면 해당 세션의 복원 가능성이 생긴다. 현재 세션 ID는 난수 suffix를 포함하지만, 운영 보안에서는 난수성만으로 소유권 검증을 대신하면 안 된다.

### 2. 세션 소유권 부재

현재는 `session_id`가 어느 사용자에게 속하는지 확인하지 않는다. 운영 환경에서는 같은 조직 또는 같은 브라우저라 하더라도, 사용자가 다른 세션을 복원할 수 없어야 한다.

### 3. 로그와 디버그 출력

restore 요청/응답은 원문 민감정보를 다시 만들어낼 수 있으므로, 요청 본문, 복원 결과, 치환 텍스트 전문을 로그에 남기면 안 된다.

### 4. CORS/CSRF 경계

브라우저 기반 환경에서 restore API가 쿠키 인증과 결합되면 CSRF 문제가 생길 수 있다. 토큰 기반 인증이든 쿠키 기반 인증이든 배포 방식에 맞는 CSRF/CORS 기준이 필요하다.

### 5. TTL과 삭제 정책 혼동

세션 TTL은 restore 가능 시간을 뜻한다. 운영 로그 보관 기간과 혼동하면 안 된다. TTL이 지난 매핑은 복원 불가능해야 하며, cleanup 정책이 실제로 작동해야 한다.

## dev-local 기준

현재 개발 단계에서는 아래를 허용한다.

- 인증 없이 restore API 사용
- SQLite 또는 memory session store 사용
- 짧은 TTL 안에서 preview -> restore 흐름 테스트
- 테스트용 샘플 문서와 가짜 개인정보 사용

단, 아래는 금지한다.

- 외부 네트워크에 dev-local backend를 노출
- 실제 고객 개인정보가 포함된 문서로 restore 테스트
- restore 결과 전문을 로그, 스크린샷, issue comment에 그대로 남김

## demo-stack 기준

외부 시연 또는 PoC demo에서 restore API를 사용할 때는 아래 기준을 따른다.

필수 기준:

- 데모 데이터는 가짜 또는 비식별 샘플만 사용
- 시연 URL 접근자를 제한
- 세션 TTL을 짧게 유지
- restore 결과를 저장하지 않음
- restore 결과 전문을 로그에 남기지 않음

권장 기준:

- 데모 전용 세션 저장소 사용
- 데모 종료 후 session cleanup 실행
- restore 버튼/기능이 어떤 의미인지 시연자에게 설명

## ops-target 기준

운영 환경에서는 아래가 구현되기 전까지 restore API를 외부 사용자에게 그대로 열지 않는다.

### 1. 인증

restore 요청자는 인증된 사용자여야 한다.

필수 후보:

- 조직 내부 SSO
- 사내망 인증 프록시
- API token 또는 session 기반 인증

### 2. 세션 소유권

restore는 아래 조건을 만족해야 한다.

- preview를 생성한 사용자와 restore 요청 사용자가 동일해야 한다.
- 또는 같은 조직/권한 그룹 안에서 명시적으로 공유된 세션이어야 한다.
- 단순히 `session_id`를 아는 것만으로 restore가 허용되면 안 된다.

세션 저장소에는 향후 아래 메타데이터가 필요하다.

- `owner_id`
- `tenant_id` 또는 `organization_id`
- `created_at`
- `expires_at`
- `policy`
- `request_type`

### 3. 감사 이벤트

운영 감사 로그는 원문을 남기지 않고 아래 이벤트만 남긴다.

- `restore_requested`
- `restore_succeeded`
- `restore_missed`
- `restore_denied`

허용 필드:

- `session_id`
- `owner_id` 또는 익명화된 사용자 식별자
- `tenant_id`
- `policy`
- `request_type`
- `restored` 여부
- `processing_ms`
- `error_type`

금지 필드:

- 원문 텍스트
- 복원된 텍스트 전문
- 치환 전 탐지 값
- 치환 후 텍스트 전문
- 업로드 파일 본문

이 기준은 `15-logging-and-audit-scope.md`의 원문 비노출 원칙을 따른다.

### 4. CORS/CSRF

운영 배포에서는 아래를 고정한다.

- 허용 origin을 명시적으로 제한
- wildcard CORS 금지
- 쿠키 인증을 쓰는 경우 CSRF token 또는 SameSite 정책 확정
- 토큰 인증을 쓰는 경우 Authorization header 기반으로 통일
- restore API를 public unauthenticated endpoint로 두지 않음

### 5. TTL과 cleanup

운영 기준:

- restore TTL은 짧게 유지한다.
- TTL 만료 후 restore는 실패하거나 `restored=false`가 되어야 한다.
- cleanup job이 실제 배포 환경에서 주기적으로 실행되어야 한다.
- 세션 저장소 백업/복제 시 민감 매핑이 포함된다는 점을 배포 문서에 명시한다.

## 구현 전 체크리스트

restore API를 외부 사용자에게 열기 전 아래를 확인한다.

- [ ] 인증 방식 결정
- [ ] 사용자/조직 식별자 모델 결정
- [ ] session store에 owner metadata 추가
- [ ] restore 요청에서 owner 검증
- [ ] restore audit event 추가
- [ ] restore 결과 전문 로그 금지 확인
- [ ] CORS origin 운영값 고정
- [ ] CSRF 기준 결정
- [ ] TTL cleanup 운영 확인
- [ ] 데모/운영 샘플 데이터 분리

## 현재 하지 않는 것

현재 MVP에서는 아래를 아직 하지 않는다.

- 사용자 계정 시스템 도입
- tenant/organization 모델 도입
- restore API 인증 강제
- restore audit table 추가
- 장기 세션 보관
- restore 결과 저장

이 항목은 운영 배포 전 별도 PR에서 처리한다.

## 관련 문서

- `14-deployment-environment-strategy.md`
- `15-logging-and-audit-scope.md`
- `41-session-history-api.md`
- `47-local-rewrite-rollout-policy.md`

## 결론

restore API는 MVP에서는 편의 기능이지만, 운영 환경에서는 민감정보 복원 권한에 해당한다. 따라서 현재는 dev-local/demo-stack 범위에서만 제한적으로 사용하고, ops-target에서는 인증과 세션 소유권 검증이 구현되기 전까지 그대로 노출하지 않는 것을 기본 정책으로 둔다.
