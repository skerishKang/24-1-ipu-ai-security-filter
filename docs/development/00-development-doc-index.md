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
- [13-hwp-conversion-candidates.md](./13-hwp-conversion-candidates.md)
  - 바이너리 HWP 변환 후보와 현재 운영 전략
- [14-deployment-environment-strategy.md](./14-deployment-environment-strategy.md)
  - dev/demo/ops 환경 구분과 현재 배포 기준
- [15-logging-and-audit-scope.md](./15-logging-and-audit-scope.md)
  - 운영 메타 로그와 감사 범위 기준
- [16-report-format-standard.md](./16-report-format-standard.md)
  - manual-preview report 필드와 enum 표준
- [17-security-policy-presets.md](./17-security-policy-presets.md)
  - manual-preview 공식 policy preset 정의
- [18-audio-intake-placeholder.md](./18-audio-intake-placeholder.md)
  - 음성 업로드/STT 연결 전 placeholder 계약
- [19-local-stt-reuse-strategy.md](./19-local-stt-reuse-strategy.md)
  - 기존 Whisper 자산 재사용 기준과 로컬 STT 판단
- [20-real-whisper-smoke.md](./20-real-whisper-smoke.md)
  - 짧은 샘플 기준 real whisper 수동 검증
- [21-real-audio-api-smoke.md](./21-real-audio-api-smoke.md)
  - real whisper 기반 audio API opt-in smoke
- [22-audio-quality-and-speed-baseline.md](./22-audio-quality-and-speed-baseline.md)
  - 짧은 음성 샘플 기준 STT 품질/속도 baseline
- [23-audio-live-integration-policy.md](./23-audio-live-integration-policy.md)
  - audio live integration을 기본 검증선에 넣지 않는 기준
- [24-audio-transcription-quality-samples.md](./24-audio-transcription-quality-samples.md)
  - 짧은 음성 샘플의 실제 전사 결과 관찰 baseline
- [25-long-audio-handling-policy.md](./25-long-audio-handling-policy.md)
  - 긴 음성의 현재 운영 범위와 분할 권장 기준
- [26-audio-segment-and-timestamp-policy.md](./26-audio-segment-and-timestamp-policy.md)
  - segment/timestamp를 현재 기본 계약에서 보류하는 기준
- [27-multi-speaker-and-meeting-audio-policy.md](./27-multi-speaker-and-meeting-audio-policy.md)
  - 다화자 음성과 회의 녹음을 현재 기본 지원에서 보류하는 기준
- [28-long-audio-verification-policy.md](./28-long-audio-verification-policy.md)
  - 긴 음성 검증선을 기본 verification에서 분리하는 기준
- [29-debug-diarization-candidates.md](./29-debug-diarization-candidates.md)
  - debug-only diarization 후보와 현재 우선순위
- [30-meeting-audio-sample-set-policy.md](./30-meeting-audio-sample-set-policy.md)
  - 회의 녹음 / 다화자 샘플셋을 어떤 기준으로 모을지 정리한 문서
- [31-meeting-audio-sample-metadata-format.md](./31-meeting-audio-sample-metadata-format.md)
  - 회의 녹음 샘플 1건을 기록하는 표준 메타 포맷
- [templates/meeting-audio-sample.template.yaml](./templates/meeting-audio-sample.template.yaml)
  - 회의 녹음 샘플 메타를 바로 복사해 쓰는 YAML 템플릿
- [samples/meeting-audio-sample-001.yaml](./samples/meeting-audio-sample-001.yaml)
  - 첫 seed sample 메타 예시
- [samples/meeting-audio-sample-001.observation.md](./samples/meeting-audio-sample-001.observation.md)
  - sample-001 실제 전사 관찰 노트
- [samples/meeting-audio-sample-002.yaml](./samples/meeting-audio-sample-002.yaml)
  - 2명 대화 planned sample 메타 예시
- [samples/meeting-audio-sample-003.yaml](./samples/meeting-audio-sample-003.yaml)
  - 3명 이상 회의 planned sample 메타 예시
- [32-audio-sample-observation-note-format.md](./32-audio-sample-observation-note-format.md)
  - 샘플 전사 결과를 기록하는 관찰 메모 표준 포맷
- [33-sample-002-asset-acquisition-todo.md](./33-sample-002-asset-acquisition-todo.md)
  - sample-002를 planned에서 observed로 올리기 위한 자산 확보 TODO
- [34-sample-003-asset-acquisition-todo.md](./34-sample-003-asset-acquisition-todo.md)
  - sample-003를 planned에서 observed로 올리기 위한 자산 확보 TODO
- [35-audio-asset-acquisition-checklist.md](./35-audio-asset-acquisition-checklist.md)
  - sample-002/sample-003 자산 확보 공통 체크리스트
- [36-audio-sample-registry.md](./36-audio-sample-registry.md)
  - 현재 audio sample 상태와 다음 액션을 한눈에 보는 레지스트리
- [37-sample-002-source-investigation-note.md](./37-sample-002-source-investigation-note.md)
  - sample-002 실제 자산 후보 소스 조사 메모
- [38-sample-003-source-investigation-note.md](./38-sample-003-source-investigation-note.md)
  - sample-003 실제 자산 후보 소스 조사 메모
- [39-sample-002-shortlist-note.md](./39-sample-002-shortlist-note.md)
  - sample-002 1차 shortlist 메모
- [40-reentry-intent-and-next-plan.md](./40-reentry-intent-and-next-plan.md)
  - 재부팅 후 바로 읽는 의도/우선순위/다음 계획 문서

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
10. [13-hwp-conversion-candidates.md](./13-hwp-conversion-candidates.md)
11. [14-deployment-environment-strategy.md](./14-deployment-environment-strategy.md)
12. [15-logging-and-audit-scope.md](./15-logging-and-audit-scope.md)
13. [16-report-format-standard.md](./16-report-format-standard.md)
14. [17-security-policy-presets.md](./17-security-policy-presets.md)
15. [18-audio-intake-placeholder.md](./18-audio-intake-placeholder.md)
16. [19-local-stt-reuse-strategy.md](./19-local-stt-reuse-strategy.md)
17. [20-real-whisper-smoke.md](./20-real-whisper-smoke.md)
18. [21-real-audio-api-smoke.md](./21-real-audio-api-smoke.md)
19. [22-audio-quality-and-speed-baseline.md](./22-audio-quality-and-speed-baseline.md)
20. [23-audio-live-integration-policy.md](./23-audio-live-integration-policy.md)
21. [24-audio-transcription-quality-samples.md](./24-audio-transcription-quality-samples.md)
22. [25-long-audio-handling-policy.md](./25-long-audio-handling-policy.md)
23. [26-audio-segment-and-timestamp-policy.md](./26-audio-segment-and-timestamp-policy.md)
24. [27-multi-speaker-and-meeting-audio-policy.md](./27-multi-speaker-and-meeting-audio-policy.md)
25. [28-long-audio-verification-policy.md](./28-long-audio-verification-policy.md)
26. [29-debug-diarization-candidates.md](./29-debug-diarization-candidates.md)
27. [30-meeting-audio-sample-set-policy.md](./30-meeting-audio-sample-set-policy.md)
28. [31-meeting-audio-sample-metadata-format.md](./31-meeting-audio-sample-metadata-format.md)
29. [32-audio-sample-observation-note-format.md](./32-audio-sample-observation-note-format.md)
30. [33-sample-002-asset-acquisition-todo.md](./33-sample-002-asset-acquisition-todo.md)
31. [34-sample-003-asset-acquisition-todo.md](./34-sample-003-asset-acquisition-todo.md)
32. [35-audio-asset-acquisition-checklist.md](./35-audio-asset-acquisition-checklist.md)
33. [36-audio-sample-registry.md](./36-audio-sample-registry.md)
34. [37-sample-002-source-investigation-note.md](./37-sample-002-source-investigation-note.md)
35. [38-sample-003-source-investigation-note.md](./38-sample-003-source-investigation-note.md)
36. [39-sample-002-shortlist-note.md](./39-sample-002-shortlist-note.md)
37. [40-reentry-intent-and-next-plan.md](./40-reentry-intent-and-next-plan.md)

### 구현 작업 직전

1. [02-system-architecture.md](./02-system-architecture.md)
2. [03-mvp-scope.md](./03-mvp-scope.md)
3. [04-backlog.md](./04-backlog.md)
4. [05-template-storage-design.md](./05-template-storage-design.md)
5. [06-template-lifecycle-note.md](./06-template-lifecycle-note.md)
6. [07-template-pipeline-integration.md](./07-template-pipeline-integration.md)
7. [08-template-approval-workflow.md](./08-template-approval-workflow.md)
8. [11-commercialization-development-plan.md](./11-commercialization-development-plan.md)
9. [13-hwp-conversion-candidates.md](./13-hwp-conversion-candidates.md)
10. [14-deployment-environment-strategy.md](./14-deployment-environment-strategy.md)
11. [15-logging-and-audit-scope.md](./15-logging-and-audit-scope.md)
12. [16-report-format-standard.md](./16-report-format-standard.md)
13. [17-security-policy-presets.md](./17-security-policy-presets.md)
14. [18-audio-intake-placeholder.md](./18-audio-intake-placeholder.md)
15. [19-local-stt-reuse-strategy.md](./19-local-stt-reuse-strategy.md)
16. [20-real-whisper-smoke.md](./20-real-whisper-smoke.md)
17. [21-real-audio-api-smoke.md](./21-real-audio-api-smoke.md)
18. [22-audio-quality-and-speed-baseline.md](./22-audio-quality-and-speed-baseline.md)
19. [23-audio-live-integration-policy.md](./23-audio-live-integration-policy.md)
20. [24-audio-transcription-quality-samples.md](./24-audio-transcription-quality-samples.md)
21. [25-long-audio-handling-policy.md](./25-long-audio-handling-policy.md)
22. [26-audio-segment-and-timestamp-policy.md](./26-audio-segment-and-timestamp-policy.md)
23. [27-multi-speaker-and-meeting-audio-policy.md](./27-multi-speaker-and-meeting-audio-policy.md)
24. [28-long-audio-verification-policy.md](./28-long-audio-verification-policy.md)
25. [29-debug-diarization-candidates.md](./29-debug-diarization-candidates.md)
26. [30-meeting-audio-sample-set-policy.md](./30-meeting-audio-sample-set-policy.md)
27. [31-meeting-audio-sample-metadata-format.md](./31-meeting-audio-sample-metadata-format.md)
28. [32-audio-sample-observation-note-format.md](./32-audio-sample-observation-note-format.md)
29. [33-sample-002-asset-acquisition-todo.md](./33-sample-002-asset-acquisition-todo.md)
30. [34-sample-003-asset-acquisition-todo.md](./34-sample-003-asset-acquisition-todo.md)
31. [35-audio-asset-acquisition-checklist.md](./35-audio-asset-acquisition-checklist.md)
32. [36-audio-sample-registry.md](./36-audio-sample-registry.md)
33. [37-sample-002-source-investigation-note.md](./37-sample-002-source-investigation-note.md)
34. [38-sample-003-source-investigation-note.md](./38-sample-003-source-investigation-note.md)
35. [39-sample-002-shortlist-note.md](./39-sample-002-shortlist-note.md)
36. [40-reentry-intent-and-next-plan.md](./40-reentry-intent-and-next-plan.md)

## 현재 개발 상태 요약

- 프론트엔드:
  - 텍스트 입력 manual-preview
  - `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.hwpx` 파일 업로드 manual-preview
  - 일반인/전문가 공통 음성 업로드
  - backend 연결 및 text mock fallback 흐름
- 백엔드:
  - `/health`
  - `/api/v1/mode/manual-preview`
  - `/api/v1/mode/manual-preview/file`
  - `/api/v1/mode/manual-preview/audio`
  - `/api/v1/mode/manual-preview/restore`
  - backend API smoke / real audio opt-in smoke
- 엔진:
  - detect / replace / restore / build_report
  - SQLite 세션 저장소
  - PDF OCR fallback / Whisper audio path

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
