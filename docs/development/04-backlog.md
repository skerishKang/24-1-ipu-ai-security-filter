# 04. Backlog

## Phase 0. Foundation

- [ ] 프로젝트 문서와 구조 확정
- [ ] 워크벤치 핵심 사용자 흐름 정의
- [ ] 엔진 서비스 계약 초안 작성
- [ ] 수동 모드 기준 API 스펙 초안 작성

## Phase 1. Manual Workbench MVP

- [ ] 텍스트 입력 화면 구현
- [ ] 치환 결과 패널 구현
- [ ] 탐지 리포트 패널 구현
- [ ] 복사 가능한 외부 AI 프롬프트 패널 구현
- [ ] 세션 생성 및 만료 규칙 정의
- [ ] 기본 민감정보 탐지 규칙 구현
- [ ] 세션별 동적 치환 규칙 구현
- [ ] 역치환 API 초안 구현

## Phase 2. File And Audio Intake

- [ ] 파일 업로드 UI 구현
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
- [x] 로컬 STT 연결 가능성 검토
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

## Phase 3. Policy And Operations

- [x] 보안 정책 프리셋 정의
- [x] 리포트 포맷 표준화
- [x] 로그와 감사 범위 정의
- [x] 배포 환경 구분 전략 정리

## Phase 4. Automatic Mode Extension

- [ ] 외부 모델 커넥터 인터페이스 구현
- [ ] 자동 전송 전 정책 체크 추가
- [ ] 응답 역치환 검증 플로우 구현
- [ ] 모델별 실패 처리 전략 정의

## Reference Review

- [ ] `24-secure-bridge`에서 개념적으로 재사용 가능한 모듈 목록화
- [ ] 그대로 가져오면 안 되는 구조적 요소 명시
- [ ] IPU 전용 웹 구조 기준으로 재설계 포인트 정리
