# Second Approved Template Note

## 목적

이 문서는 customer inquiry 계열 draft 템플릿 1건을 실제 approved 템플릿으로 승격한 두 번째 사례를 기록한다.

대상 템플릿:

- `demo-samples/derived/sample-long-customer-inquiry.template.json`

생성 결과:

- `templates/approved/customer_inquiry_intake/v1.1.0.template.json`

## 이번 승격에서 보정한 항목

### 1. 템플릿 식별자 정리

- `template_id` 를 `customer_inquiry_intake` 로 정리했다.
- `document_type` 도 approved 카탈로그와 맞게 `customer_inquiry` 로 정리했다.

### 2. placeholder 정합성 보정

기존 draft 본문에는 아래 placeholder가 있었지만 필드 정의가 없었다.

- `owner_email`
- `owner_phone`
- `customer_contact_email`
- `customer_contact_phone`
- `customer_business_id`
- `timeline_items`
- `compensation_note`
- `cc_people`

이 항목들을 optional field 로 추가해 `template_text` 와 `fields` 를 일치시켰다.

### 3. 승인용 타입과 검증 규칙 보강

- `customer_business_id` 는 approved 기준 타입인 `business_reg_no` 로 정의했다.
- `validation_rules` 를 추가했다.
  - `required_fields`
  - 이메일 정규식
  - 전화번호 정규식
  - 사업자등록번호 정규식
  - 금액 검증

### 4. 민감도 프로파일 추가

- `sensitivity_profile.profile_id`
- `sensitivity_profile.level`
- `sensitivity_profile.default_masking`
- `sensitivity_profile.contains`
- `field_overrides`
- `retention`

### 5. 샘플 값 보강

프론트 템플릿 모드와 승인 리뷰 편의를 위해 `sample_values` 를 채웠다.

## 운영상 의미

이번 승격으로 template pipeline 이 문서상 설명이 아니라 실제 데이터 기준으로도 2개 템플릿까지 닫혔다.

1. contract review
2. customer inquiry

즉, draft 추출 -> 승인 보정 -> dry-run 검증 -> approved 생성 -> 프론트 재사용 흐름이 복수 템플릿 기준으로 재현 가능해졌다.

## 현재 한계

- customer inquiry 도 여전히 사람 검토 없이 자동 승인하는 단계는 아니다
- 문맥형 필드의 완성도는 추출 품질에 영향을 받는다
- 템플릿 카탈로그 최신화는 별도 작업으로 관리해야 한다
