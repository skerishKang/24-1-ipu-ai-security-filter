# IPU AI 방화벽 Commercialization Development Plan

## 목적

이 문서는 IPU를 데모/PoC 수준에서 상용 제품 수준으로 끌어올리기 위한 개발 기준선을 정리한다.  
핵심은 `무엇을 먼저 제품화할지`, `무엇은 아직 하지 않을지`, `기술/운영/배포에서 최소로 갖춰야 할 것`을 고정하는 데 있다.

## 현재 출발점

현재 기준으로 IPU는 아래 2개 축을 이미 갖고 있다.

- `manual-preview` 흐름
  - 텍스트 입력
  - `.txt` 업로드
  - 일반인 모드 / 전문가 모드
  - 탐지 / 치환 / 리포트 / 복사용 결과
- `template pipeline` 흐름
  - 자유문서 -> draft 템플릿 추출
  - draft -> approved 승격
  - approved 템플릿 선택
  - 폼 입력 -> 문서 초안 재구성

즉, 지금은 “개념 검증”은 지난 상태이며, 다음 단계는 “상용화 범위 축소 + 운영 요구사항 추가”다.

## 상용화 1차 목표

상용화 1차 목표는 아래처럼 좁게 잡는다.

- 목표 고객:
  - 공공기관 / 공공성 강한 조직
  - 또는 재무/계약 문서를 자주 다루는 B2B 팀
- 목표 시나리오:
  - `자유문서 비식별화`
  - `반복 문서 템플릿화`
- 목표 제품 형태:
  - 웹 기반 내부 도구
  - owner-only demo URL에서 먼저 검증
  - 이후 고객사 PoC 배포형으로 확장 가능

## 상용화 1차 범위

### 포함

- 텍스트 입력 / `.txt` 업로드
- 일반인 모드 / 전문가 모드
- strict_token 기반 보안 전처리
- approved 템플릿 선택
- 템플릿 기반 입력 폼
- draft -> approved 최소 승인 흐름
- 기본 운영 로그
- demo-stack 배포 계획과 smoke 기준

### 제외

- PDF / DOCX / HWP 전체 지원
- 자동 모드 완성형
- 조직 전체 배포용 관리자 콘솔
- 정교한 권한 체계
- 대규모 멀티테넌트
- 실시간 협업
- 완전한 로컬 LLM 운영 플랫폼
- production launch claim

## 제품 트랙

### Track A. 자유문서 전처리

목적:
- 외부 SOTA 모델에 보내기 전 민감정보를 치환

핵심 기능:
- 규칙 기반 + LLM 보조 탐지
- strict_token 정책
- 결과 복사 및 검토

상용화 기준:
- 핵심 민감정보 탐지 기준선 확보
- 고객 샘플 5~10개 기준 품질 검증

### Track B. 템플릿 기반 반복 문서

목적:
- 자주 쓰는 문서를 템플릿으로 저장하고 폼 입력으로 재사용

핵심 기능:
- draft 추출
- approved 관리
- 템플릿 선택기
- 폼 입력 -> 문서 초안 생성

상용화 기준:
- 승인 템플릿 3개 이상
- 폼 기반 생성 흐름 안정화

## PoC 샘플과 approved template 기준

첫 PoC/commercialization demo 기준 자산은 `docs/development/13-poc-sample-corpus-and-template-set.md`를 따른다.

### 1차 approved template set

- `contract_review_request` v1.1.0
- `customer_inquiry_intake` v1.1.0
- `internal_report_weekly` v1.1.0

이 3개는 첫 PoC의 최소 approved template set이다. vendor coordination과 security incident template은 future candidate로 둔다.

### 1차 sample category

- contract / agreement
- customer inquiry / 민원 접수
- internal report
- vendor coordination
- security incident note

공개 demo에서는 contract, customer inquiry, internal report 3개 category를 우선 노출한다. vendor coordination과 security incident note는 내부 또는 전문가 PoC용으로 제한한다.

### 데이터 안전 기준

- GitHub에는 synthetic sample과 redacted metadata만 둔다.
- 실제 고객/사용자/기관 문서 원문은 GitHub에 commit하지 않는다.
- private sample 평가가 필요한 경우 원문은 local/private 위치에 두고, GitHub에는 sample id, category, redacted evaluation note, owner approval 여부만 남긴다.

## Demo/ops 배포 기준

첫 demo/ops 계획은 `docs/development/18-demo-ops-deployment-plan.md`를 따른다.

핵심 결정은 다음과 같다.

```text
SELECTED_TARGET = demo-stack
EXTERNAL_SURFACE = owner-only demo first
FRONTEND_HOSTING_CLASS = static hosting
BACKEND_HOSTING_CLASS = single HTTPS web service
IPU_DEPLOYMENT_ENV = ops-target
IPU_MANUAL_PREVIEW_RESPONSE_MODE = minimized
IPU_API_KEY_HASH = required
IPU_ALLOWED_ORIGINS = exact frontend demo origin only
PUBLIC_OPENAPI_DISABLED = yes
REAL_CUSTOMER_DATA_IN_DEMO = no
```

이 계획은 public production launch가 아니라, owner-only demo를 먼저 안전하게 검증하기 위한 기준이다.

## 기술 아키텍처 기준

### 1. 엔진

- 규칙 기반 탐지를 baseline으로 유지
- LLM은 문맥형 민감정보 보조 탐지에 한정
- strict_token을 PoC 기준 정책으로 유지
- default는 preview 친화 정책으로 위치를 분명히 유지
- 현재 제품 preset은 `default`, `strict_token`, `local_rewrite` 세 가지다
- `local_rewrite`는 구현되어 있고 API/UI에 노출되어 있으나, 아직 universal default는 아니다
- 새 preset 추가는 상용화 Phase 3 이후 검토

### 2. 템플릿

- draft / approved 분리
- 공통 스키마 유지
- template_id + version으로 관리
- approval 메타 유지

### 3. 프론트

- 일반인 모드:
  - 결과 중심
- 전문가 모드:
  - 탐지/리포트/세부 정보 중심
- template mode:
  - 템플릿 선택 -> 폼 입력 -> 문서 초안 생성

### 4. 백엔드

- manual-preview API 유지
- 파일 업로드 API 유지
- 템플릿 저장/조회 API는 나중에 추가 가능
- 현재는 정적 template mode를 우선 유지

## 운영 요구사항

상용화로 가려면 아래가 반드시 필요하다.

- 인증
  - 최소 사용자 식별
- 감사 로그
  - 누가 어떤 문서를 처리했는지
- 템플릿 승인 기록
  - reviewer / approved_at / version
- 문서 보관 정책
  - 저장 여부 / TTL / 삭제 정책
- 민감정보 로그 금지 원칙
- demo URL 공유 전 smoke checklist

## 배포 기준

### 단기

- frontend: 정적 호스팅
- backend: 단일 HTTPS 웹 서비스
- 외부 데모 URL은 owner-only 공유부터 시작
- `ops-target` guardrail을 강제

### 중기

- 고객사 전용 배포
- 온프레미스 또는 사설망 설치 가능 구조 검토
- dev/demo/ops 환경 구분 문서 기준으로 운영 요구사항을 분리

## 개발 우선순위

### Phase 1. 상용화 최소선

- 템플릿 선택기 안정화
- approved 템플릿 3개 확보
- strict_token 품질 보강
- 고객 샘플 기준 품질 문서화

### Phase 2. 운영 준비

- 승인 워크플로 보강
- 템플릿 버전 관리 정리
- 로그/감사 기준 보강
- demo-stack 배포 계획과 smoke 기준 정리

### Phase 3. 상용 제품 초안

- 템플릿 저장/조회 API
- 사용자 인증
- 고객사별 설정
- 정책 구성 UI 최소화

## 리스크

- 규칙 기반과 LLM 보조 경계가 흐려질 수 있음
- 템플릿 추출 품질이 문서 유형마다 흔들릴 수 있음
- 공공/B2B/B2C를 동시에 잡으면 범위가 지나치게 커짐
- 운영 기능 없이 데모 구조만 키우면 다시 흔들릴 수 있음
- public URL을 너무 빨리 공유하면 secret/CORS/logging 경계가 흔들릴 수 있음

## 의사결정 원칙

- 첫 상용화는 `좁은 시나리오`부터 간다
- 새 기능보다 `실무 사용 가능성`을 우선한다
- 템플릿 1개가 아니라 3개 이상 돌아야 제품성이 생긴다
- 자유문서는 LLM, 반복문서는 템플릿 중심으로 분리한다
- GitHub에는 synthetic/redacted 자료만 남긴다
- demo URL 공유 전에는 owner-only smoke를 먼저 통과시킨다

## 즉시 해야 할 일

1. 실제 demo environment secret/config 준비 issue를 만든다
2. owner-only demo smoke용 runbook을 작성한다
3. main branch protection 적용 여부를 결정한다
4. 고객 샘플 기반 품질 검증 결과를 redacted summary로 축적한다

## 결론

IPU 상용화의 핵심은 “기능을 더 많이 붙이는 것”이 아니라,  
`자유문서 전처리 + 반복문서 템플릿화` 두 축을 좁은 범위에서 안전하게 제품화하는 것이다.
