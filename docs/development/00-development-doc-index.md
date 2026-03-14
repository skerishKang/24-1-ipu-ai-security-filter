# IPU AI 보안필터 Development Document Index

## 목적

이 문서는 `docs/development` 아래의 개발 문서를 한 번에 찾고, 어떤 문서를 먼저 읽어야 하는지 안내하는 인덱스다.

## 핵심 개발 문서

- [01-product-overview.md](./01-product-overview.md)
  - 개발 관점 제품 개요
- [02-system-architecture.md](./02-system-architecture.md)
  - 현재 시스템 구조와 레이어 분리
- [03-mvp-scope.md](./03-mvp-scope.md)
  - MVP 범위와 제외 범위
- [04-backlog.md](./04-backlog.md)
  - 기술 백로그와 우선순위
- [05-template-storage-design.md](./05-template-storage-design.md)
  - 템플릿 JSON 저장 포맷과 메타데이터 구조
- [06-template-lifecycle-note.md](./06-template-lifecycle-note.md)
  - 템플릿 버전업, 수정, 승인 흐름 메모
- [07-template-pipeline-integration.md](./07-template-pipeline-integration.md)
  - draft 추출부터 승인 템플릿 연동까지의 파이프라인 메모
- [08-template-approval-workflow.md](./08-template-approval-workflow.md)
  - draft를 reviewed/approved로 승격하는 최소 운영 흐름
- [09-first-approved-template-note.md](./09-first-approved-template-note.md)
  - 첫 approved 템플릿 승격 메모
- [10-second-approved-template-note.md](./10-second-approved-template-note.md)
  - 두 번째 approved 템플릿 승격 메모
- [11-commercialization-development-plan.md](./11-commercialization-development-plan.md)
  - 상용화 기준 개발 계획
- [12-third-approved-template-note.md](./12-third-approved-template-note.md)
  - 세 번째 approved 템플릿 승격 메모

## 추천 읽기 순서

### 처음 참여하는 개발자

1. [01-product-overview.md](./01-product-overview.md)
2. [02-system-architecture.md](./02-system-architecture.md)
3. [03-mvp-scope.md](./03-mvp-scope.md)
4. [04-backlog.md](./04-backlog.md)
5. [05-template-storage-design.md](./05-template-storage-design.md)
6. [06-template-lifecycle-note.md](./06-template-lifecycle-note.md)
7. [07-template-pipeline-integration.md](./07-template-pipeline-integration.md)
8. [08-template-approval-workflow.md](./08-template-approval-workflow.md)
9. [11-commercialization-development-plan.md](./11-commercialization-development-plan.md)

### 구현 작업 직전

1. [02-system-architecture.md](./02-system-architecture.md)
2. [03-mvp-scope.md](./03-mvp-scope.md)
3. [04-backlog.md](./04-backlog.md)
4. [05-template-storage-design.md](./05-template-storage-design.md)
5. [06-template-lifecycle-note.md](./06-template-lifecycle-note.md)
6. [07-template-pipeline-integration.md](./07-template-pipeline-integration.md)
7. [08-template-approval-workflow.md](./08-template-approval-workflow.md)
8. [11-commercialization-development-plan.md](./11-commercialization-development-plan.md)

## 현재 개발 상태 요약

- 프론트엔드:
  - 텍스트 입력 manual-preview
  - `.txt` 파일 업로드 manual-preview
  - backend 연결 및 fallback 흐름
- 백엔드:
  - `/health`
  - `/api/v1/mode/manual-preview`
  - `/api/v1/mode/manual-preview/file`
  - smoke test
- 엔진:
  - detect / replace / restore / build_report
  - TTL 기반 세션 저장소

## 다음 기술 문서로 확장하기 좋은 영역

- API 계약 문서
- 엔진 세부 설계 문서
- 테스트 전략 문서
- 파일 파서 확장 문서
- 정책/설정 구조 문서
- 템플릿 저장 구조 문서
- 템플릿 승인 워크플로 문서

## 문서 운영 원칙

- 개발 방향 변경 시 먼저 `02-system-architecture` 또는 `03-mvp-scope`에 반영한다.
- 새로운 구현 상세가 반복되면 별도 개발 문서로 분리한다.
- 문서가 늘어나면 이 인덱스에 링크를 추가한다.

## 결론

`docs/development`는 구현 전에 방향을 맞추고, 구현 중에는 우선순위를 잃지 않게 하는 역할을 한다.  
처음 보는 개발자는 이 인덱스부터 들어와서 현재 범위와 구조를 먼저 이해하는 것이 좋다.
