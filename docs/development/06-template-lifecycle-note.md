# 06. Template Lifecycle Note

## 목적

이 문서는 템플릿 버전업, 수정, 승인, 배포 흐름을 운영 메모 수준으로 정리한다.

## 기본 흐름

1. LLM 또는 운영자가 초안 템플릿을 생성한다.
2. 초안은 `draft` 상태로 저장한다.
3. 템플릿 오너가 필드 정의, 본문, 검증 규칙을 보정한다.
4. 보안/정책 리뷰어가 민감도와 저장 가능 여부를 검토한다.
5. 리뷰 통과 후 `approved` 상태의 새 버전을 발행한다.
6. 제품은 최신 `approved` 버전만 기본 목록에 노출한다.
7. 구버전은 `deprecated`로 내리되 기존 문서 재현 용도로 유지한다.

## 상태 전이 제안

```text
draft -> review -> approved -> deprecated -> archived
```

- `draft`: 편집 중. 사용자 기본 목록에 노출하지 않는다.
- `review`: 필드 체계와 민감도 검토 대기 상태다.
- `approved`: 제품 사용 가능 상태다.
- `deprecated`: 신규 생성에는 비권장이나 기존 문서 호환은 유지한다.
- `archived`: 운영 화면 기본 목록에서 숨기고 감사용으로만 보관한다.

## 버전업 규칙

### patch

아래와 같은 경우 `1.0.0 -> 1.0.1`을 권장한다.

- 오탈자 수정
- placeholder 문구 수정
- 설명 문구 변경
- 검증 메시지 문안 수정

### minor

아래와 같은 경우 `1.0.0 -> 1.1.0`을 권장한다.

- 선택 필드 추가
- 검증 규칙 강화
- 민감도 프로필 조정
- UI 그룹 또는 렌더 순서 변경

### major

아래와 같은 경우 `1.0.0 -> 2.0.0`을 권장한다.

- 필수 필드 삭제 또는 이름 변경
- `template_text` 플레이스홀더 호환성 파괴
- 필드 타입 변경
- 기존 저장 payload와 호환되지 않는 구조 변경

## 수정 원칙

- 승인된 템플릿 파일은 덮어쓰지 않는다.
- 수정이 필요하면 새 버전을 만든다.
- `template_id`는 유지하고 `version`, `updated_at`, `updated_by`를 갱신한다.
- 어떤 필드가 왜 바뀌었는지는 별도 변경 로그 또는 PR 설명에 남긴다.

## 승인 체크리스트

- `template_id`, `document_type`, `version`이 일관적인가
- 필수 필드가 `template_text`에서 실제 사용되는가
- `fields[].type`이 허용 목록 안에 있는가
- `validation_rules.required_fields`와 `fields[].required`가 충돌하지 않는가
- `sensitivity_profile.contains`가 실제 필드 타입과 맞는가
- 민감 필드가 누락 없이 `sensitive=true`로 표시되었는가
- deprecated 또는 archived 대상과 혼동되지 않는가

## 운영 메모

- 제품은 `(template_id, version)`을 키로 저장하면 재현성이 좋아진다.
- 화면 기본 노출은 `latest approved by template_id` 기준이 적합하다.
- 특정 문서가 어느 템플릿 버전으로 생성되었는지는 문서 메타데이터에 함께 남겨야 한다.
- LLM 추출 초안은 그대로 승인하지 말고 사람이 `fields`와 `validation_rules`를 반드시 검토해야 한다.

## 권장 역할 분리

- `creator`: 초안 생성
- `editor`: 필드/본문 정제
- `reviewer`: 정책 및 품질 검토
- `approver`: 배포 승인

## 남은 운영 과제

- 승인 로그 저장 위치 결정
- 템플릿 diff 시각화 방식 정의
- deprecated 버전 자동 숨김 정책 정의
- 템플릿별 접근 권한 모델 결정

## 결론

템플릿은 문서 조각이 아니라 제품 설정 자산으로 다루는 편이 안전하다.  
따라서 승인 후 불변 버전 관리와 명시적 상태 전이가 필수다.
