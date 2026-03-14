# Third Approved Template Note

## 목적

이 문서는 세 번째 approved 템플릿 승격 결과를 간단히 고정한다.  
이번 승격으로 template pipeline은 계약 검토, 고객 문의, 내부 보고 3개 축을 모두 승인 템플릿 기준으로 시연할 수 있게 되었다.

## 승격 대상

- draft:
  - `demo-samples/derived/sample-long-internal-report.template.json`
- approved:
  - `templates/approved/internal_report_weekly/v1.1.0.template.json`

## 핵심 보정 사항

- 식별자 정리
  - `template_id`: `internal_report_weekly`
  - `document_type`: `internal_report`
- placeholder 정합성 보정
  - `reporter_email`
  - `reporter_phone`
  - `business_status_summary`
  - `hiring_plan_summary`
  - `customer_feedback_summary`
  - `labor_cost`
  - `infrastructure_cost`
  - `net_profit`
  - `owner_person`
  - `owner_phone`
  - `owner_email`
- 승인 메타 보강
  - `validation_rules`
  - `sensitivity_profile`
  - `sample_values`

## 검증 결과

- `promote_template.py --dry-run` 통과
- 실제 승격 완료
- approved JSON parse 통과
- `templates/approved/internal_report_weekly/v1.1.0.template.json` 경로 생성 확인

## 의미

이제 template mode에서 아래 3개 승인 템플릿을 선택할 수 있다.

- 계약 검토 의뢰서
- 고객 문의 접수서
- 주간 내부 보고서

즉 IPU는 `자유문서 -> draft -> approved -> 선택 -> 입력 -> 문서 초안` 흐름을 3개 문서 유형으로 시연 가능한 상태가 되었다.
