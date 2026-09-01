# 13. PoC Sample Corpus And Approved Template Set

## 목적

이 문서는 IPU AI Firewall의 첫 PoC/commercialization demo에서 사용할 샘플 문서 코퍼스와 approved template 최소 세트를 정의한다.

핵심 원칙은 다음 두 가지다.

1. GitHub에는 synthetic sample과 안전한 메타데이터만 둔다.
2. 실제 고객/사용자 문서는 원문을 repository에 넣지 않고, 별도 private/local evidence로만 다룬다.

## 현재 main 기준 출발점

현재 repository에는 이미 다음 자산이 존재한다.

### Approved template 3개

| Template ID | Version | Demo role | Status |
| --- | --- | --- | --- |
| `contract_review_request` | `v1.1.0` | 계약 검토 의뢰서 | Required PoC template |
| `customer_inquiry_intake` | `v1.1.0` | 고객 문의 접수서 | Required PoC template |
| `internal_report_weekly` | `v1.1.0` | 주간 내부 보고서 | Required PoC template |

이 3개를 첫 PoC의 최소 approved template set으로 고정한다.

### Demo sample 8개 이상

| Sample | Category | Role |
| --- | --- | --- |
| `sample-contract-review.txt` | contract / agreement | 짧은 계약 검토 샘플 |
| `sample-customer-inquiry.txt` | customer inquiry | 짧은 고객 문의 샘플 |
| `sample-internal-report.txt` | internal report | 짧은 내부 보고 샘플 |
| `sample-long-contract-review.txt` | contract / agreement | 긴 계약 검토 데모 샘플 |
| `sample-long-customer-inquiry.txt` | customer inquiry | 긴 고객 문의 데모 샘플 |
| `sample-long-internal-report.txt` | internal report | 긴 내부 보고 데모 샘플 |
| `sample-long-vendor-coordination.txt` | vendor / partner coordination | 협력사 관리 데모 샘플 |
| `sample-long-security-incident-note.txt` | security incident / response | 보안 사고 대응 데모 샘플 |

`sample-empty.txt`는 제품 데모 샘플이 아니라 empty-file error path 검증용으로만 유지한다.

## 첫 PoC 샘플 카테고리

첫 PoC에서 다룰 문서 카테고리는 아래 5개로 제한한다.

| Category | Purpose | Representative samples | Template target |
| --- | --- | --- | --- |
| Contract / agreement | 계약 검토, 금액, 회사명, 담당자, 이메일/전화 치환 | `sample-contract-review.txt`, `sample-long-contract-review.txt` | `contract_review_request` |
| Customer inquiry / 민원 접수 | 고객 문의, 민원성 요청, 후속 조치, 담당자 치환 | `sample-customer-inquiry.txt`, `sample-long-customer-inquiry.txt` | `customer_inquiry_intake` |
| Internal report | 주간 보고, 예산, 인력, 일정, 리스크 정리 | `sample-internal-report.txt`, `sample-long-internal-report.txt` | `internal_report_weekly` |
| Vendor coordination | 협력사/외주사 조율, 비용, 계약, 일정 | `sample-long-vendor-coordination.txt` | Future template candidate |
| Security incident note | 보안 사고 대응, 이해관계자, 외부 연락처, 비용 추정 | `sample-long-security-incident-note.txt` | Future template candidate |

첫 공개 demo에서는 앞의 3개 category를 우선 노출하고, vendor/security incident는 전문가/내부 PoC 시나리오로 보수적으로 사용한다.

## GitHub commit 가능 샘플 정책

GitHub에 commit할 수 있는 샘플은 아래 조건을 모두 만족해야 한다.

- 완전 synthetic 문서일 것.
- 실존 개인의 주민등록번호, 여권번호, 운전면허번호, 계좌번호, 카드번호, 전화번호, 주소, 의료기록, 실제 고객 식별자가 없어야 한다.
- 실존 회사/기관명이 들어갈 경우 공개적으로 알려진 일반 예시인지, 아니면 가상명인지 문서화해야 한다.
- 탐지 테스트를 위해 숫자/전화/이메일 형식을 사용할 수는 있으나, 실제 연락처로 오인되지 않도록 reserved/example domain 또는 명확한 가상명을 사용해야 한다.
- 데모 목적상 민감정보처럼 보이는 문자열을 넣을 수 있으나, 실제 사람/고객/계약/사건과 연결되면 안 된다.
- 샘플 본문에 `SYNTHETIC_SAMPLE = YES` 성격이 README 또는 registry에서 추적되어야 한다.

## Private/local-only 샘플 정책

아래 유형은 repository에 원문을 commit하지 않는다.

- 실제 고객 문서.
- 실제 아파트/주민/민원/계약/사건 문서.
- 실제 이름, 전화번호, 주소, 계좌, 카드, 주민번호, 의료정보가 포함된 문서.
- 비공개 회의록, 내부 보고서, 법무 검토서, 경찰/행정/공공기관 원문.
- 사용자가 직접 제공한 개인 문서 또는 제3자 문서.

이런 샘플이 PoC 품질 검증에 필요하면 GitHub에는 아래 메타데이터만 기록한다.

```text
SAMPLE_ID = private-poc-001
SOURCE_CLASS = customer_private | owner_private | public_redacted
DOCUMENT_CATEGORY = contract | inquiry | internal_report | vendor | security_incident | other
ORIGINAL_LOCATION = local/private only, not GitHub
REDACTION_STATUS = raw_private | redacted_private | synthetic_derivative
PII_PRESENT_IN_REPO = NO
EVALUATION_NOTES_COMMITTED = redacted summary only
OWNER_APPROVAL_REQUIRED = YES
```

## 샘플 메타데이터 포맷

향후 registry 파일을 만들 경우 각 샘플은 아래 필드를 가진다.

```json
{
  "sample_id": "synthetic-contract-001",
  "path": "demo-samples/sample-long-contract-review.txt",
  "source_class": "synthetic",
  "document_category": "contract",
  "length_class": "long",
  "intended_flow": ["manual_preview", "strict_token", "template_candidate"],
  "contains_real_sensitive_data": false,
  "commit_allowed": true,
  "expected_sensitive_types": ["PERSON", "ORG", "EMAIL", "PHONE", "MONEY"],
  "demo_priority": "primary",
  "approved_template_id": "contract_review_request",
  "quality_status": "ready_for_demo_smoke"
}
```

## Demo-ready quality criteria

샘플 또는 template이 첫 PoC demo-ready로 인정되려면 아래 기준을 만족해야 한다.

### 자유문서 전처리 샘플

```text
STRICT_TOKEN_PREVIEW_COMPLETES = YES
NO_RUNTIME_ERROR = YES
REPLACED_TEXT_PRESENT = YES
REPORT_PRESENT = YES
COPY_READY_TEXT_PRESENT = YES
HIGH_RISK_TOKEN_TYPES_REVIEWED = YES
NO_REAL_SENSITIVE_DATA_COMMITTED = YES
```

### Template mode 샘플/template

```text
APPROVED_TEMPLATE_HAS_APPROVAL_METADATA = YES
TEMPLATE_PICKER_LOADS = YES
FORM_FIELDS_RENDER = YES
REQUIRED_FIELD_MISSING_STATE_VISIBLE = YES
SAMPLE_VALUES_FILL = YES
DRAFT_RECONSTRUCTION_WORKS = YES
USER_VALUES_ESCAPED_IN_PREVIEW = YES
STATE_RESETS_ON_TEMPLATE_SWITCH = YES
```

### Private sample evaluation

```text
ORIGINAL_STAYS_PRIVATE = YES
GITHUB_ONLY_HAS_METADATA_OR_REDACTED_SUMMARY = YES
OWNER_APPROVAL_RECORDED = YES
RESULT_SUMMARY_CONTAINS_NO_RAW_PII = YES
```

## 첫 PoC 최소 세트 판정

현재 main 기준 판정은 다음과 같다.

```text
APPROVED_TEMPLATE_MINIMUM_SET_DEFINED = YES
APPROVED_TEMPLATE_MINIMUM_COUNT = 3
POC_SAMPLE_CATEGORIES_DEFINED = YES
SYNTHETIC_SAMPLE_POLICY_DEFINED = YES
PRIVATE_SAMPLE_POLICY_DEFINED = YES
SAMPLE_METADATA_FORMAT_DEFINED = YES
DEMO_READY_QUALITY_CRITERIA_DEFINED = YES
NO_REAL_SENSITIVE_DATA_COMMITTED_BY_THIS_DOC = YES
```

## 다음 작업으로 넘길 것

- demo/ops deployment plan에서는 위 3개 approved template과 3개 primary sample category를 기준 demo surface로 삼는다.
- customer/private sample이 들어오면 원문은 local/private에 두고, GitHub에는 registry metadata와 redacted evaluation note만 남긴다.
- vendor coordination과 security incident template은 future template candidate로 남기고 첫 공개 demo claim에는 포함하지 않는다.
