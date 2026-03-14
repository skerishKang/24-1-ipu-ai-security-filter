# Template JSON Schema Draft

## 목적

자유문서를 읽고 반복 가능한 템플릿 구조로 바꾸기 위한 초안 스키마다.  
현재 목적은 "LLM이 문서 본문을 읽고 어떤 필드를 안정적으로 템플릿화할 수 있는가"를 검증하는 것이다.

## 설계 원칙

- 규칙 기반으로 잘 잡히는 필드와 문맥 해석이 필요한 필드를 구분한다.
- 문서 유형별 공통 필드와 섹션별 필드를 함께 담는다.
- 템플릿 텍스트와 필드 정의를 한 묶음으로 저장한다.
- 실제 값 예시는 `source_examples` 로 남겨 추출 품질을 검토한다.

## 초안 스키마

```json
{
  "template_name": "contract_review_request_v1",
  "document_type": "contract_review_request",
  "document_purpose": "외부 계약 검토 의뢰",
  "field_groups": [
    {
      "name": "document_meta",
      "label": "문서 메타",
      "fields": ["request_date", "document_title", "sender_org", "sender_person"]
    }
  ],
  "fields": [
    {
      "name": "sender_org",
      "label": "의뢰 회사명",
      "type": "org",
      "required": true,
      "multiple": false,
      "inference_mode": "rule_preferred",
      "source_examples": ["아이피유테크"],
      "description": "문서 발신 조직"
    }
  ],
  "sections": [
    {
      "name": "contract_overview",
      "label": "계약 개요",
      "repeatable": false,
      "field_refs": ["counterparty_org", "contract_name", "contract_type", "contract_amount"]
    }
  ],
  "template_text": "..."
}
```

## 필드 타입 후보

- `org`: 회사명, 법인명, 부서명
- `person`: 담당자명, 검토자명, 결재권자명
- `email`: 이메일
- `phone`: 전화번호
- `amount`: 금액, 연간 계약액, 예산, 비용
- `date`: 일자, 마감일, 체결일, 보고일
- `address`: 주소
- `business_id`: 사업자등록번호
- `enum`: 계약유형, 접수채널, 고객등급, 검토상태
- `text`: 계약명, 문의 제목, 내부 메모
- `list_text`: 조항 목록, 내부 검토 포인트, 후속 조치 목록

## inference_mode 해석

- `rule_preferred`
  - 이메일, 전화번호, 금액, 날짜, 사업자등록번호처럼 규칙 기반으로 우선 추출 가능한 항목
- `rule_plus_context`
  - 회사명, 담당자명처럼 규칙 기반 후보를 뽑고 문맥으로 역할을 확정해야 하는 항목
- `llm_context_required`
  - 내부 검토 포인트, 계약 리스크, 비공개 논의 사항처럼 역할/의미를 문맥으로 해석해야 하는 항목

## 문서 유형별 공통 필드 후보

- `document_title`
- `document_date`
- `sender_org`
- `sender_person`
- `sender_email`
- `sender_phone`
- `recipient_org`
- `recipient_person`
- `due_date`
- `internal_review_points`
- `follow_up_actions`

## 결론

현재 초안은 자유문서를 "문서 유형 + 필드 목록 + 섹션 구조 + 템플릿 본문"으로 나누는 방식이다.  
규칙 기반 엔진은 값 후보를 먼저 찾고, LLM은 각 후보가 문서 안에서 어떤 역할인지 정리하는 방식이 적합해 보인다.
