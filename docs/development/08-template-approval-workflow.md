# 08. Template Approval Workflow

## 목적

이 문서는 `demo-samples/derived/*.template.json`에 저장된 draft 템플릿을 사람이 검토해 `templates/approved/...` 아래 approved 템플릿으로 승격하는 최소 운영 흐름을 정의한다.

이번 범위는 full admin UI가 아니라 다음 세 가지다.

- 사람이 어떤 항목을 확인해야 승인 가능한지 명시
- draft와 approved 저장 위치를 안전하게 구분
- 작은 CLI 도구로 승격 전 점검과 복제를 보조

## 저장 경로 원칙

### draft

- 위치: `demo-samples/derived/*.template.json`
- 의미: LLM 또는 실험 파이프라인이 만든 초안
- 상태: 기본적으로 `status: "draft"`
- 성격: 누락 필드, 미완성 placeholder, 임시 타입이 남아 있을 수 있다

### approved

- 위치: `templates/approved/<template_id>/v<version>.template.json`
- 의미: 사람 검토와 승인 메타가 채워진 운영용 템플릿
- 상태: `status: "approved"`
- 성격: 제품 재사용 기준선

## 최소 승인 체크리스트

아래 항목을 모두 통과해야 approved로 승격한다.

### 1. 최상위 메타데이터

- `template_id`, `template_name`, `document_type`, `version`이 채워져 있는가
- `status`가 `draft` 또는 `review`인가
- `created_at`, `updated_at`, `created_by`, `updated_by`가 있는가
- `source_document.path`가 원본 draft 또는 자유문서를 추적 가능하게 남아 있는가

### 2. 필드 정의 완성도

- `fields`가 비어 있지 않은가
- 모든 필드에 `field_id`, `field_name`, `type`, `label`, `required`, `sensitive`가 있는가
- `field_id`와 `field_name`이 중복되지 않는가
- `label`이 빈 문자열이 아닌가
- `ui.widget`, `ui.order`, `render.token`이 채워져 있는가

### 3. 승인 가능 타입 점검

approved 템플릿에서는 아래 타입만 허용한다.

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
- `text`
- `enum`
- `list_text`

아래 타입은 draft에서 흔히 나오지만 approved 전에는 정리해야 한다.

- `business_id`
  - `business_reg_no`로 변경

## 4. 본문 placeholder 일치

- `template_text`에 쓰인 `{{placeholder}}`가 모두 `fields[].field_name`에 존재하는가
- `fields[].render.token`이 `{{field_name}}` 형식과 정확히 일치하는가
- `required: true`인 필드는 `template_text` 또는 운영상 별도 섹션에서 반드시 사용되는가

## 5. 검증 규칙

- `validation_rules.required_fields`가 필수 필드 목록과 어긋나지 않는가
- 이메일, 전화번호, 사업자등록번호, 금액처럼 규칙 기반 검증 가능한 필드에 최소 검증이 있는가
- 비필수 필드가 필수 목록에 잘못 들어가지 않았는가

## 6. 민감도 프로파일

- `sensitivity_profile.profile_id`가 있는가
- `sensitivity_profile.level`이 정의되어 있는가
- `sensitivity_profile.default_masking`이 정의되어 있는가
- 민감 필드 타입이 `contains` 또는 field override와 크게 어긋나지 않는가

## 7. 승인 메타데이터

승격 시 최소한 아래 항목을 기록한다.

```json
{
  "approval": {
    "reviewer": "reviewer@ipu.co.kr",
    "approved_by": "reviewer@ipu.co.kr",
    "approved_at": "2026-03-14T22:10:00+09:00",
    "checklist_version": "template-approval-minimum-v1"
  }
}
```

- `reviewer`: 실제 체크리스트 검토자
- `approved_by`: 승인한 사람. 현재 최소 흐름에서는 reviewer와 동일하게 둘 수 있다
- `approved_at`: ISO 8601 타임스탬프
- `checklist_version`: 어떤 승인 기준으로 통과했는지 추적하기 위한 값

## 최소 운영 절차

1. draft 템플릿을 연다.
2. 체크리스트 기준으로 필드명, 라벨, 타입, placeholder, 민감도 메타를 보정한다.
3. `python3 scripts/promote_template.py --draft ... --reviewer ... --dry-run` 으로 승인 불가 사유를 확인한다.
4. 에러를 모두 해결한다.
5. `--version`, `--approved-at`을 지정해 실제 promotion을 실행한다.
6. 생성된 `templates/approved/<template_id>/v<version>.template.json`을 다시 리뷰한다.

## 최소 CLI 예시

```bash
python3 scripts/promote_template.py \
  --draft demo-samples/derived/sample-long-contract-review.template.json \
  --version 1.1.0 \
  --reviewer reviewer@ipu.co.kr \
  --dry-run
```

```bash
python3 scripts/promote_template.py \
  --draft demo-samples/derived/sample-long-contract-review.template.json \
  --version 1.1.0 \
  --reviewer reviewer@ipu.co.kr \
  --approved-at 2026-03-14T22:10:00+09:00
```

## 현재 draft 샘플에서 실제로 자주 나오는 승인 차단 사유

- `business_id` 같은 임시 타입이 남아 있음
- `template_text`에 있으나 `fields`에는 없는 placeholder가 남아 있음
- 필드는 있는데 `template_text`에서 쓰이지 않는 항목이 있음
- `validation_rules` 또는 `sensitivity_profile`이 비어 있음
- `approval` 메타가 비어 있음

## 승인 가능한 템플릿의 기준 예시

현재 승인 구조 예시는 [v1.0.0.template.json](/mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter/templates/approved/contract_review_request/v1.0.0.template.json)에서 확인할 수 있다.

이 파일은 다음 특성을 가진다.

- `status: "approved"`
- `approval` 메타 존재
- `validation_rules` 존재
- `sensitivity_profile` 존재
- 주요 placeholder와 필드가 일치

## 결론

이번 단계의 최소 승인 흐름은 “문서화된 체크리스트 + dry-run 검증 + approved 경로 복사”다.  
이 정도만 있어도 draft와 approved를 안전하게 분리하고, 사람이 어떻게 승인하는지 재현 가능한 프로세스를 만들 수 있다.
