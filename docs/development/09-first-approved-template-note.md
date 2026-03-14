# First Approved Template Note

## 목적

이 문서는 draft 템플릿 1건을 실제 approved 템플릿으로 승격한 첫 사례를 기록한다.

대상 템플릿:

- `demo-samples/derived/sample-long-contract-review.template.json`

생성 결과:

- `templates/approved/contract_review_request/v1.1.0.template.json`

## 이번 승격에서 보정한 항목

### 1. 레거시 타입 정리

- `business_id` 를 `business_reg_no` 로 변경했다.

### 2. placeholder 정합성 보정

기존 draft 본문에는 아래 placeholder가 있었지만 필드 정의가 없었다.

- `recipient_group`
- `counterparty_phone`
- `counterparty_email`
- `conclusion_note`
- `owner_person`
- `owner_phone`
- `owner_email`

이 항목들을 optional field 로 추가해 `template_text` 와 `fields` 를 일치시켰다.

### 3. 검증 규칙 추가

draft에는 `validation_rules` 가 없었으므로 아래를 채웠다.

- `required_fields`
- 이메일 정규식
- 전화번호 정규식
- 사업자등록번호 정규식
- 금액 최소 검증

### 4. 민감도 프로파일 추가

draft에는 `sensitivity_profile` 이 없었으므로 아래를 추가했다.

- `profile_id`
- `level`
- `default_masking`
- `contains`
- `field_overrides`
- `retention`

### 5. 샘플 값 보강

템플릿 모드 및 검토 편의를 위해 `sample_values` 를 채웠다.

## 운영상 의미

이번 승격은 아래 흐름이 문서가 아니라 실제 데이터로도 닫힌다는 점을 보여준다.

1. 자유문서에서 draft 템플릿 추출
2. draft 구조 보정
3. dry-run 승인 검증
4. approved 버전 생성
5. 프론트 템플릿 모드 재사용 가능

## 현재 한계

- 아직 사람 검토 UI는 없다
- 승격 체크리스트는 CLI와 문서 기준이다
- 모든 draft가 바로 승격 가능한 것은 아니다

하지만 최소한 1건은 실제로 `approved` 까지 승격 가능한 상태임을 확인했다.
