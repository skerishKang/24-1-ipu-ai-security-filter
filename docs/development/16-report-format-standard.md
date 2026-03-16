# 16. Report Format Standard

## 목적

이 문서는 `manual-preview` 응답의 `report` 필드를 backend, frontend, engine, 문서에서 같은 의미로 유지하기 위한 최소 표준이다.

## 적용 범위

- `POST /api/v1/mode/manual-preview`
- `POST /api/v1/mode/manual-preview/file`
- frontend mock fallback
- smoke / API / engine 테스트

## canonical field

`report` 는 아래 4개 필드를 항상 포함한다.

- `total_detections`
- `risk_level`
- `strategy`
- `review_status`

## field definition

### `total_detections`

- 타입: integer
- 의미: 현재 preview 에서 탐지되어 치환 대상으로 잡힌 항목 수
- 기준: 현재 구현에서는 `max(len(detections), len(replacements))`

### `risk_level`

- 타입: string enum
- 허용값:
  - `low-risk`
  - `moderate-risk`
  - `high-risk`
- 기준:
  - `0`건: `low-risk`
  - `1-2`건: `moderate-risk`
  - `3`건 이상: `high-risk`

`medium-risk` 는 현재 표준값이 아니다. 프론트와 테스트에서는 `moderate-risk` 를 사용한다.

### `strategy`

- 타입: string enum
- 허용값:
  - `alias`
  - `strict_token`
- 의미:
  - `alias`: `default` policy 의 실제 치환 전략
  - `strict_token`: `strict_token` policy 의 실제 치환 전략

### `review_status`

- 타입: string enum
- 허용값:
  - `clean`
  - `review-required`
- 기준:
  - 탐지 0건: `clean`
  - 탐지 1건 이상: `review-required`

## frontend display rule

- `risk_level` 은 badge 와 요약 metric 에 그대로 표시한다.
- `strategy` 는 현재 policy 설명 박스와 함께 보여준다.
- `review_status` 는 "추가 검토 필요 여부"를 나타내는 최소 운영 상태로 사용한다.

## compatibility rule

- backend schema 는 위 enum 을 기준으로 응답을 검증한다.
- frontend fallback/mock 도 같은 enum 값만 만들어야 한다.
- 새 정책이 추가되면 이 문서를 먼저 갱신한 뒤 schema 와 UI 를 바꾼다.

## 현재 결론

현재 `manual-preview` report 는 운영형 감사 리포트가 아니라, preview 결과를 빠르게 읽기 위한 요약 리포트다.  
따라서 필드는 작게 유지하고, 값 의미는 여기 문서에 고정한다.
