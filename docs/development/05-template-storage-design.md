# 05. Template Storage Design

## 목적

이 문서는 LLM이 추출한 템플릿을 제품 내부에서 저장, 버전관리, 재사용하기 위한 JSON 저장 포맷과 메타데이터 구조를 정의한다.

핵심 목표는 다음과 같다.

- 템플릿 자체를 파일 단위로 이식 가능하게 유지
- 웹 폼 렌더링과 검증 로직에서 바로 사용할 수 있는 구조 제공
- 템플릿 수정과 승인 흐름에서 버전 추적이 가능하도록 설계
- 민감정보 필드 성격을 템플릿 메타데이터에 함께 보관

## 설계 원칙

- 저장 포맷은 JSON 단일 문서로 정의한다.
- 하나의 파일은 하나의 템플릿 버전을 나타낸다.
- `template_id`는 논리적 템플릿 식별자이고 `version`은 불변 버전 식별자다.
- 템플릿 본문, 필드 정의, 검증 규칙, 민감도 정책을 한 파일에 함께 둔다.
- UI 렌더링에 필요한 속성은 `fields` 배열 내부에 포함한다.
- 승인 상태와 변경 이력은 메타데이터에 남기되 실제 문서 본문과 분리하지 않는다.

## 권장 저장 경로

운영 저장소 기준 권장 구조는 아래와 같다.

```text
templates/
  examples/
    contract_review.template.json
    customer_inquiry.template.json
  contract_review/
    contract_review_request/
      v1.0.0.template.json
      v1.1.0.template.json
  customer_inquiry/
    customer_inquiry_intake/
      v1.0.0.template.json
```

- `document_type` 단위로 디렉터리를 나눈다.
- `template_id` 단위로 하위 디렉터리를 만든다.
- 파일명은 `v{version}.template.json`으로 고정하면 배포와 캐시 관리가 단순해진다.
- 현재 산출물 예시는 `templates/examples`에 둔다.

## 최상위 JSON 포맷

```json
{
  "schema_version": "1.0",
  "template_id": "contract_review_request",
  "template_name": "계약 검토 요청서",
  "document_type": "contract_review",
  "version": "1.0.0",
  "status": "approved",
  "created_at": "2026-03-14T09:00:00+09:00",
  "updated_at": "2026-03-14T09:00:00+09:00",
  "created_by": "llm-extractor",
  "updated_by": "policy-owner",
  "approval": {
    "approved_by": "reviewer@ipu.co.kr",
    "approved_at": "2026-03-14T10:00:00+09:00"
  },
  "fields": [],
  "template_text": "문서 본문 템플릿",
  "validation_rules": {},
  "sensitivity_profile": {}
}
```

## 최상위 필드 정의

- `schema_version`: 템플릿 저장 포맷 버전. 파서 호환성 판단 기준이다.
- `template_id`: 같은 템플릿 계열을 식별하는 고정 ID다.
- `template_name`: 운영자와 사용자에게 보여줄 이름이다.
- `document_type`: 문서 카테고리다. 검색, 분류, UI 그룹핑 기준으로 사용한다.
- `version`: SemVer 스타일 문자열을 권장한다.
- `status`: `draft`, `review`, `approved`, `deprecated`, `archived` 중 하나를 권장한다.
- `created_at`, `updated_at`: ISO 8601 타임스탬프를 사용한다.
- `created_by`, `updated_by`: 생성 주체와 마지막 수정 주체다.
- `approval`: 승인자와 승인 시각이다. 승인 전에는 `null` 가능하다.
- `fields`: 웹 폼과 치환 렌더링에 사용하는 필드 배열이다.
- `template_text`: 플레이스홀더를 포함한 본문 템플릿이다.
- `validation_rules`: 필드 단위 및 템플릿 단위 제약 조건이다.
- `sensitivity_profile`: 민감정보 처리 강도와 마스킹 전략 정의다.

## 필드 타입 체계

지원 타입은 다음과 같이 고정한다.

- `person`
- `org`
- `email`
- `phone`
- `amount`
- `date`
- `address`
- `business_reg_no`
- `clause`
- `free_text`

각 타입은 기본 UI 위젯과 기본 검증 규칙을 갖는다.

| field type | 기본 위젯 | 기본 검증 포인트 |
| --- | --- | --- |
| `person` | text | 길이, 호칭 포함 여부, 실명/별칭 메모 |
| `org` | text | 법인명/조직명 길이, 접미어 또는 사업자 정보 연결 |
| `email` | email | 이메일 형식 |
| `phone` | tel | 전화번호 형식 |
| `amount` | number 또는 text | 숫자 범위, 통화, 표현 방식 |
| `date` | date | 날짜 형식, 최소/최대 |
| `address` | textarea | 최소 길이 |
| `business_reg_no` | text | 사업자등록번호 형식 |
| `clause` | textarea | 조항 번호, 멀티라인 허용 |
| `free_text` | textarea | 길이 제한, 금칙어 또는 참고 문구 |

## `fields` 배열 구조

각 `fields[]` 항목은 아래 구조를 권장한다.

```json
{
  "field_id": "counterparty_org",
  "field_name": "counterparty_org",
  "type": "org",
  "label": "상대 기관명",
  "description": "계약 상대방의 공식 조직명",
  "required": true,
  "placeholder": "주식회사 아이피유테크",
  "default_value": null,
  "example_value": "주식회사 미래전자",
  "multiple": false,
  "sensitive": true,
  "ui": {
    "widget": "text",
    "order": 1,
    "group": "party",
    "width": "full"
  },
  "validation": {
    "min_length": 2,
    "max_length": 100
  },
  "render": {
    "token": "{{counterparty_org}}",
    "inline": true
  }
}
```

### 필드 메타데이터 설명

- `field_id`: 템플릿 내부 고유 ID다.
- `field_name`: API, 폼 submit payload, LLM extraction key에서 공통 사용한다.
- `type`: 위에서 정의한 고정 타입 중 하나다.
- `label`: 웹 폼 노출용 라벨이다.
- `description`: 운영자와 사용자 설명 문구다.
- `required`: 입력 필수 여부다.
- `placeholder`: 폼 기본 힌트다.
- `default_value`: 사전 채움 값이다.
- `example_value`: 예시 입력 값이다.
- `multiple`: 배열 입력 여부다.
- `sensitive`: 민감정보 여부다.
- `ui`: 웹 폼 렌더링 정보다.
- `validation`: 필드 단위 검증 규칙이다.
- `render`: 템플릿 본문 치환 규칙이다.

## `validation_rules` 구조

`validation_rules`는 템플릿 전체 수준 제약을 담는다.

```json
{
  "required_fields": [
    "counterparty_org",
    "requester_name",
    "requester_email"
  ],
  "field_rules": {
    "requester_email": {
      "pattern": "^[^@]+@[^@]+\\.[^@]+$"
    },
    "contract_amount": {
      "min_value": 0,
      "currency": "KRW"
    }
  },
  "cross_field_rules": [
    {
      "rule_id": "end_date_after_start_date",
      "type": "date_order",
      "left": "contract_start_date",
      "right": "contract_end_date",
      "message": "종료일은 시작일 이후여야 합니다."
    }
  ]
}
```

### 설계 의도

- `required_fields`는 빠른 렌더링과 저장 전 검증에 바로 사용 가능하다.
- `field_rules`는 타입 기본 검증 외의 개별 규칙을 덧씌운다.
- `cross_field_rules`는 날짜 순서나 금액 조합 같은 필드 간 제약을 표현한다.

## `sensitivity_profile` 구조

`sensitivity_profile`은 템플릿 단위 민감도 정책 메타데이터다.

```json
{
  "profile_id": "contract_strict_v1",
  "level": "high",
  "contains": [
    "person",
    "org",
    "email",
    "phone",
    "amount",
    "business_reg_no",
    "address"
  ],
  "default_masking": "strict_token",
  "field_overrides": {
    "review_clause_text": {
      "masking": "partial"
    }
  },
  "retention": {
    "store_original_input": false,
    "store_rendered_output": true
  }
}
```

### 설계 의도

- 템플릿 생성 단계에서 어떤 민감정보 타입이 포함되는지 선언할 수 있다.
- 추후 엔진 정책 프리셋과 연결할 수 있다.
- 필드별 예외 정책을 둘 수 있어 재사용성이 높다.

## `template_text` 작성 규칙

- 본문은 사람이 읽을 수 있는 문장 단위 템플릿으로 저장한다.
- 치환 토큰은 `{{field_name}}` 형식을 권장한다.
- 다단 문단도 문자열 그대로 저장한다.
- 조항 반복이 필요한 경우에는 `multiple=true` 필드를 두고 렌더러에서 반복 확장한다.

예시:

```text
{{counterparty_org}}와 {{requester_org}} 간 {{contract_type}} 검토를 요청드립니다.
담당자는 {{requester_name}}({{requester_email}}, {{requester_phone}})입니다.
검토 대상 금액은 {{contract_amount}}이며, 주요 조항은 아래와 같습니다.
{{review_clause_text}}
```

## 버전관리 규칙 제안

- `template_id`는 고정하고 `version`만 올린다.
- 승인된 버전은 수정하지 않고 새 파일로 발행한다.
- `draft` 상태에서는 자유 수정 가능하지만 배포 대상은 아니다.
- `approved` 버전만 제품 기본 선택지에 노출한다.
- 긴급 수정은 `1.0.0 -> 1.0.1`, 필드 구조 변경은 `1.0.0 -> 1.1.0`, 비호환 변경은 `1.0.0 -> 2.0.0`을 권장한다.

## 웹 폼 렌더링 적합성

이 구조는 아래 이유로 웹 폼에 바로 연결하기 쉽다.

- `fields` 배열이 입력 순서와 그룹 정보를 이미 포함한다.
- `type`, `required`, `placeholder`, `ui.widget`만으로 기본 폼을 그릴 수 있다.
- `validation`과 `validation_rules`를 프런트와 백엔드가 공통 해석할 수 있다.
- `render.token`과 `template_text`가 있어 입력값을 바로 문서 텍스트로 조립할 수 있다.

## 향후 확장 포인트

- 다국어 라벨을 위한 `i18n` 블록 추가
- 선택형 필드를 위한 `options` 배열 표준화
- 반복 섹션을 위한 `sections` 또는 `repeaters` 구조 추가
- 변경 이력 diff를 위한 `changelog` 블록 추가

## 결론

제안한 구조는 템플릿 정의, 폼 렌더링, 검증, 민감도 메타데이터를 한 JSON에 묶어 제품 내부 저장 포맷으로 쓰기 적합하다.  
특히 `template_id + version` 조합과 `fields + template_text + validation_rules + sensitivity_profile` 조합이 있어 운영과 재사용 양쪽을 동시에 만족시킨다.
