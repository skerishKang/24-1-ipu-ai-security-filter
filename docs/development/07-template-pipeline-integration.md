# Template Pipeline Integration

## 목적

이 문서는 `자유문서 -> 추출 초안 템플릿 JSON -> 승인 템플릿 저장 -> 템플릿 기반 폼 렌더링 -> 문서 초안 재구성` 흐름을 하나의 파이프라인으로 묶기 위한 통합 메모다.

이번 단계의 목표는 세 가지 산출물을 서로 다른 실험 결과로 두지 않고, 같은 템플릿 스키마 계열 안에서 연결하는 것이다.

- 자유문서 기반 템플릿 추출 실험
- 저장/승인 가능한 템플릿 구조
- 프론트 템플릿 모드 데모

## 공통 템플릿 구조

추출 초안과 승인 템플릿은 같은 최상위 구조를 공유한다.

```json
{
  "schema_version": "1.0",
  "template_id": "contract_review_request",
  "template_name": "계약 검토 의뢰서",
  "document_type": "contract_review_request",
  "document_purpose": "외부 자문 또는 내부 결재용 계약 검토 의뢰",
  "version": "1.0.0",
  "status": "approved",
  "created_at": "2026-03-14T21:00:00+09:00",
  "updated_at": "2026-03-14T21:00:00+09:00",
  "approval": {},
  "source_document": {},
  "field_groups": [],
  "fields": [],
  "template_text": "..."
}
```

핵심 필드:

- `status`: `draft`, `review`, `approved`, `deprecated`, `archived`
- `field_groups`: 폼 렌더링용 그룹
- `fields`: 실제 입력 필드 정의
- `template_text`: 최종 문서 초안 재구성용 본문
- `source_document`: 어떤 자유문서나 초안에서 파생됐는지 추적

## 추출 초안과 승인 템플릿의 차이

### 추출 초안

위치:

- `demo-samples/derived/*.template.json`

특징:

- `status: "draft"`
- 자유문서에서 뽑은 후보 필드와 초안 본문을 담는다
- `approval` 은 `null`
- `description`, `validation`, `ui` 는 최소 수준일 수 있다
- 사람이 검토하기 전 단계이므로 누락 필드와 애매한 문맥 필드가 남을 수 있다

### 승인 템플릿

위치:

- `templates/approved/.../*.template.json`

특징:

- `status: "approved"`
- `approval` 메타가 채워진다
- 폼 렌더링에 필요한 `ui`, `placeholder`, `example_value`, `validation` 이 더 구체적이다
- 프론트 템플릿 모드는 이 승인이 끝난 템플릿을 우선 사용한다

## 현재 연결된 최소 파이프라인

1. 자유문서에서 필드 후보와 `template_text` 를 추출한다.
2. 결과를 `demo-samples/derived/*.template.json` 에 `draft` 상태로 저장한다.
3. 검토 후 `templates/approved/.../*.template.json` 으로 승격한다.
4. `frontend/template-mode.html` 이 승인 템플릿 JSON을 읽는다.
5. 프론트가 `fields` 를 기반으로 입력 폼을 렌더링한다.
6. 사용자가 입력한 값으로 `template_text` 를 치환해 문서 초안을 다시 만든다.

## 현재 프론트 연동 대상

현재 템플릿 모드는 아래 승인 템플릿을 실제로 읽는다.

- `templates/approved/contract_review_request/v1.0.0.template.json`

이 템플릿은 다음 흐름을 보여주는 데모 기준선이다.

- 계약 검토 요청 자유문서
- 추출 초안 JSON
- 승인 템플릿 JSON
- 템플릿 폼 입력
- 재구성된 계약 검토 의뢰서 초안

## 현재 한계

- 추출 초안에서 승인 템플릿으로 넘어가는 리뷰 UI는 아직 없다
- `derived` 와 `approved` 가 같은 스키마 계열이지만, 승인 템플릿 쪽 메타가 더 풍부하다
- 문맥형 필드의 정확도는 여전히 사람 검토 또는 LLM 보조가 필요하다

## 운영상 해석

- 규칙 기반으로 강한 필드:
  - 이메일
  - 전화번호
  - 금액
  - 날짜
  - 주소
  - 사업자등록번호
- LLM 문맥 판별이 필요한 필드:
  - 계약 유형
  - 내부 검토 포인트
  - 고객 문의 핵심 요약
  - 보고서형 자유문서의 섹션 요약

즉 현재 파이프라인은 `규칙 기반 후보 추출 + 문맥형 필드 정리 + 승인 템플릿 저장 + 폼 재사용` 구조로 설명하는 것이 가장 정확하다.
