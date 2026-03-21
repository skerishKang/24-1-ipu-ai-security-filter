# 17. Security Policy Presets

## 목적

이 문서는 `manual-preview`가 현재 공식적으로 지원하는 보안 정책 preset을 고정한다.  
목표는 backend schema, engine 동작, frontend 설명이 같은 기준을 쓰게 만드는 것이다.

## 현재 공식 preset

현재 지원하는 preset은 아래 3개다.

- `default`
- `strict_token`
- `local_rewrite`

새 preset을 추가할 때는 먼저 이 문서를 갱신한 뒤 API schema, engine, frontend를 함께 수정한다.

## preset definition

### `default`

- 위치: 읽기 쉬운 기본 보호
- 목적: 사용자가 원문 문맥을 비교적 쉽게 읽으면서도 직접 표기된 핵심 민감정보를 빠르게 가리는 것
- 현재 탐지 범위:
  - `EMAIL`
  - `PHONE`
  - `PERSON`
- 현재 치환 전략:
  - `alias`
- 대표 토큰:
  - `[EMAIL_ALIAS_01]`
  - `[PHONE_ALIAS_01]`
  - `[PERSON_ALIAS_01]`
- 권장 사용:
  - 빠른 초안 검토
  - 일반인 모드 preview
  - 가독성이 중요한 데모

### `strict_token`

- 위치: 더 보수적인 비식별화
- 목적: 외부 전송 전 더 넓은 범위를 가리고, 어떤 유형이 치환됐는지 설명 가능한 형태로 유지하는 것
- 현재 탐지 범위:
  - `EMAIL`
  - `PHONE`
  - `PERSON`
  - `ORG`
  - `AMOUNT`
- 현재 치환 전략:
  - `strict_token`
- 대표 토큰:
  - `[EMAIL_01]`
  - `[PHONE_01]`
  - `[PERSON_01]`
  - `[ORG_01]`
  - `[AMOUNT_01]`
- 추가 동작:
  - 변형 이메일 탐지
  - 제한된 직함 없는 실명 전달 문맥 탐지
- 권장 사용:
  - 고객 PoC
  - 외부 모델 전송 전 보수적 전처리
  - 전문가 모드 검토

### `local_rewrite`

- 위치: 로컬 모델 보조 치환
- 목적: strict_token 수준의 탐지 범위를 유지하면서 더 자연스러운 치환 결과 생성
- 현재 탐지 범위:
  - `EMAIL`, `PHONE`, `PERSON`, `ORG`, `AMOUNT` (strict_token 기준)
- 현재 치환 전략:
  - Ollama 로컬 모델 기반 자연어 치환
  - 모델 실패 시 deterministic generalized fallback
- 일반화 표현 예시:
  - 모델이 문맥을 분석하여 생성하는 일반화 표현
- 권장 사용:
  - 가독성이 중요한 외부 AI 전송 시
  - strict_token 결과의 부자연스러움이 문제될 때
- 주의:
  - 아직 universal default가 아님
  - 모델 품질에 따라 결과가 달라질 수 있음

## 제품 원칙

- 기본 추천 정책은 `default`가 아니라 용도에 따라 다르다.
- 일반 사용자에게는 `default`를 먼저 보여주되, 외부 전송 전 검토에는 `strict_token`을 더 분명히 안내한다.
- 현재 PoC 품질 기준선은 `strict_token` 중심으로 해석한다.

## API 계약

- request `policy`는 `default | strict_token | local_rewrite`를 허용한다.
- response `report.strategy`는 `alias | strict_token | local_rewrite`로 확장한다.
- unsupported policy는 backend schema 단계에서 거절한다.

## 현재 결론

현재 단계에서 policy preset은 실험용 토글이 아니라 제품 계약이다.  
따라서 설명 문구, 테스트, 품질 리뷰는 모두 이 세 preset을 기준으로 유지한다.
