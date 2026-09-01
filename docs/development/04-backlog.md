# 04. Backlog

이 문서는 `main` 기준 구현 상태와 앞으로 남은 제품화 작업을 한눈에 보기 위한 backlog다.

상태 표기는 다음 기준을 따른다.

- `[x]` = 완료 또는 현재 main에서 구현 확인
- `[~]` = 부분 구현 / 구현은 있으나 검증·운영 기준 보강 필요
- `[ ]` = 미구현 또는 다음 작업
- `[deferred]` = 의도적으로 보류

## Phase 0. Foundation

- [x] 프로젝트 문서와 구조 확정
- [x] 워크벤치 핵심 사용자 흐름 정의
- [x] 엔진 서비스 계약 초안 작성
- [x] 수동 모드 기준 API 스펙 초안 작성
- [x] 사업 문서와 개발 문서 분리
- [x] repository branch cleanup 완료: `main` + B63 evidence branch 2개만 보존

## Phase 1. Manual Workbench MVP

- [x] 텍스트 입력 화면 구현
- [x] 치환 결과 패널 구현
- [x] 탐지 리포트 패널 구현
- [x] 복사 가능한 외부 AI 프롬프트 패널 구현
- [x] 세션 생성 및 만료 규칙 정의
- [x] 기본 민감정보 탐지 규칙 구현
- [x] 세션별 동적 치환 규칙 구현
- [x] 역치환 API 초안 구현
- [x] frontend/backend/engine end-to-end 수동 preview 경로 연결
- [x] 일반인/전문가 view mode 분리
- [x] frontend smoke/unit test 경로 구성
- [~] 고객 샘플 기준 수동 워크벤치 품질 검증
- [~] demo 시나리오 기준 브라우저 검증 기록

## Phase 2. File And Audio Intake

- [x] 파일 업로드 UI 구현
- [x] 파일 preview API 연결
- [x] 파일 파서 인터페이스 정의
- [x] 지원 포맷 우선순위 선정
- [x] 스캔형 PDF OCR fallback 연결
- [x] OCR 품질 샘플셋 확장
- [x] PDF 품질 샘플셋 확장
- [x] DOCX parser 추가
- [x] HWPX parser 추가
- [x] 바이너리 HWP parser 전략 결정
- [x] 바이너리 HWP 변환 도구 후보 검토
- [x] 음성 업로드 파이프라인 자리 마련
- [x] 음성 preview API 연결
- [x] 로컬 STT 연결 가능성 검토
- [x] local Whisper opt-in 구조 정리
- [x] 긴 음성 처리 정책 분리
- [x] segment / timestamp 활용 여부 결정
- [x] 다화자 / 긴 회의 녹음 정책 분리
- [x] 긴 음성 전용 검증선 분리 여부 결정
- [x] debug-only diarization 후보 검토
- [x] 회의 녹음 샘플셋 확보 기준 문서화
- [x] 회의 녹음 샘플 메타 포맷 정의
- [x] 샘플 관찰 메모 포맷 정의
- [x] sample-002 실제 자산 확보 전용 TODO 정리
- [x] sample-003 실제 자산 확보 전용 TODO 정리
- [x] sample-002 / sample-003 자산 확보 공통 체크리스트 정리
- [x] audio sample registry 문서 추가
- [x] sample-002 확보용 후보 소스 조사 메모
- [x] sample-003 확보용 후보 소스 조사 메모
- [x] sample-002 실제 확보 후보 1차 shortlist 문서화
- [~] real audio 품질/속도 baseline 확장
- [deferred] 긴 음성 자동 분할과 다화자 diarization 기본 지원
- [deferred] broader compressed package inspection 기본 활성화

## Phase 3. Policy And Operations

- [x] 보안 정책 프리셋 정의
- [x] 리포트 포맷 표준화
- [x] 로그와 감사 범위 정의
- [x] 배포 환경 구분 전략 정리
- [x] public/ops minimized response guard
- [x] public/ops API key hash startup guard
- [x] public/ops CORS origin fail-closed guard
- [x] public OpenAPI/docs disable guard
- [x] restore token / owner boundary 보강
- [x] upload size / concurrency / parser limit guardrail 보강
- [ ] main branch protection 적용 여부 결정
- [ ] demo/ops 배포 계획 확정
- [ ] demo smoke checklist 확정
- [ ] 운영 로그 필드와 민감정보 비저장 기준 재검증

## Phase 4. Automatic Mode Extension

- [ ] 외부 모델 커넥터 인터페이스 구현
- [ ] 자동 전송 전 정책 체크 추가
- [ ] 응답 역치환 검증 플로우 구현
- [ ] 모델별 실패 처리 전략 정의
- [deferred] 자동 모드 production claim
- [deferred] 조직 단위 관리자 정책 UI
- [deferred] 멀티테넌트 enterprise 관리 기능

## Commercialization Track

- [ ] template mode 브라우저 검증 완료
- [ ] approved template 최소 3개 정의
- [ ] 고객/PoC 샘플 문서 5~10개 정책 정의
- [ ] synthetic sample과 private sample 경계 정의
- [ ] demo/ops hosting target 선정
- [ ] public demo URL 공유 전 smoke 기준 확정
- [ ] 제안서/PoC 설명용 제품 상태 요약 갱신

## Reference Review

- [~] `24-secure-bridge`에서 개념적으로 재사용 가능한 모듈 목록화
- [~] 그대로 가져오면 안 되는 구조적 요소 명시
- [~] IPU 전용 웹 구조 기준으로 재설계 포인트 정리

Reference review는 초기 방향 설정에는 충분히 사용되었으나, 새 구현은 현재 repository 구조와 IPU 전용 계약을 source of truth로 삼는다.

## 현재 우선순위

1. #106 roadmap/backlog 현실화
2. #107 template mode browser verification
3. #108 customer sample corpus / approved template minimum set
4. #109 demo and ops deployment plan
5. main branch protection decision
