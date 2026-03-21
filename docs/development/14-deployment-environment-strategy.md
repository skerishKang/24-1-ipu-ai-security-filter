# 14. Deployment Environment Strategy

## 목적

이 문서는 IPU AI Firewall를 어떤 환경 기준으로 개발, 데모, 운영할지 구분하기 위한 기준선이다.  
핵심은 "같은 코드베이스를 어디까지 같은 방식으로 돌릴지"를 정리해, 환경 차이 때문에 검증선이 흔들리지 않게 하는 것이다.

## 결론 요약

현재 기준으로 환경은 아래 3단계로 나눈다.

1. `dev-local`
2. `demo-stack`
3. `ops-target`

이 세 단계는 같은 기능을 공유하지만, 허용하는 의존성과 검증 기준은 다르게 둔다.

## 1. dev-local

목적:

- 가장 빠르게 구현하고 테스트하는 환경
- mounted drive / WSL / Windows 혼합 환경까지 허용

현재 특징:

- backend mounted-drive venv 는 느릴 수 있다
- `/tmp/ipu_backend_test_venv` 우회 경로를 허용한다
- `tesseract`, `pdftoppm`, `pdftocairo` 같은 로컬 도구가 있으면 OCR fallback 을 바로 검증할 수 있다
- `manual-preview` 중심 단일 사용자 개발 흐름을 전제로 한다

허용 기준:

- 임시 경로 기반 fast venv 허용
- sqlite 세션 저장소 허용
- 정적 frontend 서버 허용
- 로컬 포트 고정 허용 (`8241`, `4241`)

필수 기준:

- `run_verification_suite.sh` 또는 동등한 테스트 흐름이 통과해야 한다
- `.hwp` 는 자동 변환이 아니라 안내 전략으로 유지한다
- mounted-drive 성능 문제는 코드 문제가 아니라 환경 이슈로 분리해 기록한다

## 2. demo-stack

목적:

- 외부 시연 또는 PoC 데모에 쓰는 최소 배포 형태
- "보여주는 흐름"이 끊기지 않는 것이 중요하다

현재 특징:

- frontend 는 정적 호스팅
- backend 는 단일 웹 서비스
- sqlite 세션 저장소 허용
- OCR 도구가 있으면 PDF fallback 까지 포함 가능
- `.hwp` 는 계속 변환 안내 전략 유지

필수 기준:

- `manual-preview`
- file upload (`.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.hwpx`)
- preview -> restore
- strict_token / default 차이 설명 가능
- live integration smoke 통과

권장 기준:

- OCR 도구 설치 여부 명시
- demo용 샘플 문서 별도 보관
- `run_demo_stack.sh` 로 최소 기동 가능
- `scripts/check_demo_stack_deps.py` 로 기동 전 의존성 상태 확인 가능
- audio whisper smoke는 기본 검증선이 아니라 opt-in smoke 로 분리

## 3. ops-target

목적:

- 고객사 내부망 또는 사설망 배포를 상정한 운영 기준

현재 전제:

- 아직 실제 운영 배포를 열 단계는 아니다
- 다만 지금부터 dev/demo 기준과 분리해 둬야 한다

운영 요구사항:

- 고정된 python/runtime 버전
- OCR 도구 설치 여부를 배포 명세에 포함
- 파일 저장 위치와 TTL 정책 분리
- 사용자 식별 또는 감사 로그 기준 확정
- 세션 저장소 경로를 환경변수로 고정
- mounted-drive 같은 개발 편의 우회 제거

운영 금지사항:

- `/tmp` 기반 임시 venv 의존
- 수동 생성된 로컬 경로 가정
- 사용자 PC에만 있는 변환기 의존

## 환경별 의존성 표

### 공통

- Python backend
- 정적 frontend
- SQLite session store
- manual-preview engine

### dev-local 전용 허용

- `/tmp/ipu_backend_test_venv`
- WSL mounted drive
- 로컬 OCR 툴 존재 여부 차이

### demo-stack 권장

- `tesseract`
- `pdftoppm`
- `pdftocairo`

### ops-target 필수 후보

- 고정 python runtime
- OCR 툴 설치 명세
- 세션/로그 저장 경로 표준화

## 현재 재시작 지점

지금 단계에서 가장 먼저 맞춰야 하는 환경 문서는 아래다.

1. dev-local: 빠른 검증 경로 유지
2. demo-stack: 실제 데모 필수 의존성 고정
3. ops-target: 나중에 따로 배포 명세 문서 분리

즉 현재는 `ops-target 구현`보다 `demo-stack 안정화`가 우선이다.

## 바로 이어질 작업

- `run_verification_suite.sh` 에 PDF 품질 샘플 테스트 포함
- demo-stack 필수 의존성 체크 스크립트 추가
- OCR 툴 미설치 시 안내 문구 정리
- 세션 저장소 stats / cleanup 스크립트 추가
