# 00. Master Roadmap

## 1. 문서 목적

이 문서는 `IPU AI Firewall` 프로젝트의 장기 작업 기준 문서다.

목표는 다음 세 가지를 동시에 정렬하는 것이다.

- 제품 방향
- 개발 우선순위
- 사업 문서와 기술 문서의 역할 분리

즉, 개별 문서나 개별 구현 작업이 흩어지지 않도록 상위 로드맵 역할을 한다.

## 2. 프로젝트 한 줄 정의

IPU AI Firewall은 민감정보를 내부에서 탐지, 치환, 복원한 뒤 생성형 AI 요청과 응답을 정책에 따라 통제하는 기업용 AI 방화벽이다.

## 3. 현재 프로젝트 상태

현재 `main` 기준 프로젝트는 문서 기반 방향 고정 단계를 지나, 수동 모드 중심 MVP와 주요 입력 확장 경로가 구현된 상태다.

완료 또는 구현 확인된 축은 다음과 같다.

- 새 프로젝트 구조 생성 완료
- 제품 개요, 시스템 아키텍처, MVP 범위, 백로그, 사업 포지셔닝 문서 생성
- 수동 모드 워크벤치의 기본 화면 흐름 구현
- `manual-preview` API, 파일 업로드 preview API, 음성 업로드 preview API 연결
- 엔진 `detect / replace / restore / report` 계열 기본 흐름 연결
- 텍스트 입력, 파일 입력, 음성 입력의 수동 preview 처리 경로 마련
- `default`, `strict_token`, `local_rewrite` 정책 preset 노출
- 세션 저장, restore token, response minimization, upload guardrail, CORS/auth/hash boundary 등 주요 보안 guardrail 반영
- Ruff, engine/backend/frontend smoke, live integration, frontend unit을 포함한 CI workflow 구성
- repository branch cleanup 완료: `main`과 B63 evidence branch 2개만 보존

아직 제품화 완료로 보지 않는 축은 다음과 같다.

- 외부 공개 demo/ops 배포 미완료
- 조직/사용자 인증과 관리자 정책 UI 미완료
- 자동 외부 모델 전송 및 응답 역치환 자동화 미완료
- 고객 샘플 기반 PoC 품질 기준 미확정
- template mode 브라우저 검증과 approved template 최소 세트 확정 필요
- B63 benchmark/evidence branch는 보존 상태이나, production clinical claim으로 승격되지 않음

현재 단계의 핵심 의미는 "무엇을 만들 것인가"만 고정된 상태가 아니라, **수동 모드 기반 기술 MVP를 제품화 기준으로 재정렬해야 하는 상태**라는 점이다.

## 4. 전체 단계 개요

프로젝트는 크게 4단계로 나눈다.

### Phase 0. Foundation

문서, 구조, 역할, 경계, MVP 정의를 고정하는 단계

### Phase 1. Manual Workbench MVP

수동 모드 중심 보안 치환 워크벤치를 만드는 단계

### Phase 2. Secure Workflow Expansion

파일, 음성, 정책, 세션 관리 등 실무 입력 경로를 확장하는 단계

### Phase 3. Enterprise Productization

자동 모드, 외부 모델 연동, 관리자 기능, 배포 전략까지 확장하는 단계

## 5. 각 단계의 목표와 현재 판정

## Phase 0. Foundation

### 목표

- 프로젝트의 제품 방향을 문서로 고정
- 프론트엔드, 백엔드, 엔진의 책임 분리
- 수동 모드를 MVP의 기준으로 확정

### 현재 판정

`DONE`.

Foundation 문서와 기본 구조는 충분히 마련되어 있으며, 이후 작업은 문서 신규 작성보다 구현 상태와 제품화 우선순위를 맞추는 방향으로 진행한다.

## Phase 1. Manual Workbench MVP

### 목표

사용자가 텍스트를 입력하면 안전한 치환본을 만들고 검토할 수 있는 웹 기반 워크벤치를 완성한다.

### 포함 기능

- 텍스트 입력
- 민감정보 탐지
- 치환 결과 생성
- 탐지 리포트 표시
- 외부 AI용 복사 프롬프트 생성
- 세션 단위 매핑 관리

### 현재 판정

`IMPLEMENTED / NEEDS VERIFICATION REFRESH`.

수동 모드 end-to-end 경로는 구현되어 있다. 다만 상용화 단계에서는 브라우저 검증, 고객 샘플 기준 품질 문서화, demo용 시나리오 고정이 추가로 필요하다.

## Phase 2. Secure Workflow Expansion

### 목표

수동 모드 MVP를 실무 입력 경로 중심으로 확장한다.

### 포함 기능

- 파일 업로드
- 파일 파서 연결
- 음성 업로드
- 로컬 STT 연결 가능 구조
- 정책 프리셋
- 세션 만료 및 복원 규칙 정교화

### 현재 판정

`PARTIAL / IMPLEMENTED WITH BOUNDARIES`.

파일과 음성 preview 경로, parser, upload guardrail, opt-in STT 구조는 마련되어 있다. 단, 긴 음성, 다화자 회의, segment/timestamp, broader package inspection, real customer corpus는 보수적으로 보류 또는 별도 검증 대상으로 남긴다.

## Phase 3. Enterprise Productization

### 목표

실제 기업 도입을 염두에 둔 운영 기능과 자동 모드를 붙인다.

### 포함 기능

- 외부 모델 자동 연동
- 응답 역치환 자동화
- 감사 로그 범위 정의
- 관리자 정책 관리
- 조직 단위 배포 전략
- 온프레미스/사내 서버 운영 전략

### 현재 판정

`NEXT`.

운영 보안 기준의 일부는 이미 문서화·구현되어 있으나, demo/ops 배포 계획, 인증, 관리자 정책 UI, 자동 모드, 고객사별 설정은 아직 제품화 전 단계다.

## 6. 사업 문서와 개발 문서의 분리 원칙

현재 문서는 두 축으로 나뉜다.

### 사업 문서

위치: `docs/business/`

역할:

- 고객 문제 정의
- 포지셔닝
- 세일즈 메시지
- 공공/대기업 대상 설명
- 향후 BM과 고객군 정의

### 개발 문서

위치: `docs/development/`

역할:

- 제품 정의
- 시스템 구조
- MVP 범위
- 백로그
- 구현 순서
- API/엔진/워크플로우 기준

현재 개발 문서는 `docs/development/` 아래에 분리한다.

## 7. 지금 시점의 최우선 개발 순서

현재 기준으로 가장 적절한 개발 순서는 다음과 같다.

1. `docs/development/04-backlog.md`와 roadmap을 현재 구현 상태에 맞게 현실화한다.
2. template mode 브라우저 검증을 수행한다.
3. PoC용 고객 샘플/합성 샘플 정책과 approved template 최소 세트를 확정한다.
4. demo/ops 배포 계획을 확정한다.
5. 필요한 경우 외부 demo URL과 backend hosting 구성을 별도 PR에서 추가한다.

## 8. 지금 시점의 최우선 사업 문서 순서

현재 기준으로 가장 적절한 사업 문서 순서는 다음과 같다.

1. 수동 모드 MVP와 template mode를 기준으로 한 PoC 데모 시나리오 정리
2. 고객 샘플 5~10개 기준 품질 평가 방식 정리
3. 공공기관/B2B 내부 도구 포지셔닝 보강
4. demo/ops 배포 조건과 보안 가드레일 정리
5. BM 및 과금 전략 업데이트
6. 고객 페르소나와 도입 시나리오 정교화

## 9. 의사결정 포인트

앞으로 프로젝트에서 중요한 결정은 다음 순서로 정리한다.

### 제품 결정

- 수동 모드만으로도 첫 PoC 가치가 충분한가
- template mode를 1차 상용화 축으로 둘 것인가
- 자동 모드는 언제 붙일 것인가
- 입력 타입 우선순위는 텍스트/파일/음성 중 무엇인가

### 기술 결정

- 경량 로컬 모델 도입 시점
- 규칙 기반 탐지와 모델 기반 탐지의 경계
- 세션 저장 범위와 폐기 정책
- public/demo/ops 환경에서 어느 API 응답 필드를 최소화할 것인가

### 사업 결정

- 첫 고객군은 대기업/금융/공공 중 어디인가
- PoC형 판매로 시작할지, 연간 라이선스로 갈지
- 온프레미스가 기본인지, 관리형 배포가 기본인지
- 데모 URL을 누구에게 어느 범위까지 공개할 것인가

## 10. 작업 운영 원칙

- 큰 방향은 문서에서 먼저 정리한다.
- 구현은 문서를 따르되, 구현 중 문서와 충돌하면 먼저 충돌 지점을 명시한다.
- 수동 모드와 template mode를 먼저 제품화하고 자동 모드는 확장 구조로만 설계한다.
- 기존 `24-secure-bridge`는 구조 복제가 아니라 개념 참고용으로만 사용한다.
- 사업 문서와 개발 문서는 같은 목표를 보되, 서로 역할이 다르다는 점을 유지한다.
- branch cleanup은 repository hygiene이며, 제품 readiness를 대신하지 않는다.
- evidence/audit-only branch는 제품 claim이나 production release로 오인하지 않는다.

## 11. 다음 체크포인트

다음 체크포인트는 아래 세 가지 중 어느 수준까지 왔는지로 판단한다.

### Checkpoint A

- roadmap/backlog가 현재 `main` 구현 상태와 일치함

### Checkpoint B

- template mode 브라우저 검증이 PASS이고 coverage gap이 기록됨

### Checkpoint C

- PoC 샘플/approved template 최소 세트와 demo/ops 배포 계획이 확정됨

이 세 가지가 완료되면 Phase 3 상용화 준비 작업에 들어갈 수 있다.

## 12. 한 줄 결론

IPU AI Firewall은 문서 기반 방향 고정과 수동 모드 기술 MVP 단계를 지나, 지금은 `자유문서 전처리 + 반복문서 템플릿화`를 좁은 범위에서 검증하고 demo/ops 제품화 기준으로 정렬해야 하는 단계다.
