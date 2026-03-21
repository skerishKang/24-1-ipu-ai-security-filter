# IPU AI Firewall

IPU AI Firewall은 민감정보를 내부에서 탐지, 치환, 복원한 뒤 생성형 AI 요청과 응답을 정책에 따라 통제하는 기업용 AI 방화벽이다. IPU는 "I'll Protect You"의 약자이며, 초기 MVP는 완성형 AI 비서보다 "보안 치환 워크벤치"에 가깝게 설계한다.

## 라이선스

이 저장소는 `UNLICENSED` 상태의 proprietary repository다. 사전 서면 허가 없이 사용, 복제, 수정, 재배포할 수 없다.

## 빠른 문서 진입점

- [docs/README.md](./docs/README.md)
  - 전체 문서 허브
- [00-master-roadmap.md](./docs/00-master-roadmap.md)
  - 상위 로드맵
- [30-business-doc-index.md](./docs/business/30-business-doc-index.md)
  - 사업 문서 인덱스
- [00-development-doc-index.md](./docs/development/00-development-doc-index.md)
  - 개발 문서 인덱스

## 기본 로컬 포트

- backend: `8241`
- frontend: `4241`

## 실행 보조 스크립트

- Windows: `run_demo_stack.bat`, `run_verification_suite.bat`
- Linux/WSL/macOS: `run_demo_stack.sh`, `run_verification_suite.sh`
- WSL mounted drive 환경에서 backend 테스트가 느리면 `scripts/ensure_fast_backend_venv.sh` 로 `/tmp` 기반 빠른 검증용 venv를 준비할 수 있다
- demo-stack 기동 전에는 `scripts/check_demo_stack_deps.py` 로 Python/Node/OCR 도구 상태를 확인할 수 있다

## 주요 환경변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `IPU_SESSION_STORE_KIND` | `sqlite` | 세션 저장소 종류. 세션 히스토리 API는 `sqlite` 모드에서만 지원한다. |
| `IPU_SESSION_STORE_PATH` | `data/runtime/manual_preview_sessions.sqlite3` | SQLite 세션 DB 경로 |
| `IPU_SESSION_TTL_SECONDS` | `900` | 세션 TTL(초) |
| `IPU_AUDIO_TRANSCRIBER` | `whisper` | 음성 전사기 종류 (`whisper`, `placeholder`) |
| `IPU_WHISPER_MODEL_NAME` | `small` | Whisper 모델 이름 |
| `IPU_WHISPER_MODEL_DIR` | 환경별 기본 경로 | Whisper 모델 디렉터리 override |
| `IPU_WHISPER_LANGUAGE` | `auto` | Whisper 언어 설정. `auto`면 자동 감지 |
| `IPU_WHISPER_TASK` | `transcribe` | Whisper 작업 종류 |
| `IPU_WHISPER_USE_GPU` | `true` | GPU 사용 여부 |

세션 히스토리 API와 관련된 운영 기준은 [`docs/development/41-session-history-api.md`](./docs/development/41-session-history-api.md)를 따른다.

## 서비스 정의

- 사용자가 텍스트, 문서, 음성 데이터를 업로드한다.
- 내부 보안 엔진이 민감정보를 탐지하고 세션별로 동적 치환한다.
- 초기에는 치환 결과와 리포트를 보여주고 사용자가 직접 외부 모델에 붙여넣는 수동 모드를 제공한다.
- 이후 자동 모드에서는 치환본을 서버가 외부 모델 API로 전달하고 응답을 역치환한다.

## 왜 필요한가

기업은 최신 외부 AI의 성능을 활용하고 싶지만, 원문 데이터가 외부로 유출되거나 재사용될 위험 때문에 도입이 지연된다. IPU는 이 간극을 줄이기 위해 원문 보호와 생성형 AI 활용 사이에 위치하는 정책기반 게이트웨이를 제공한다.

핵심 가치는 다음과 같다.

- 원문 데이터는 내부 보안 레이어에서 먼저 처리한다.
- 외부 모델에는 치환된 데이터만 전달하도록 설계한다.
- 세션 단위 매핑과 복원 흐름을 분리해 운영 정책을 명확히 한다.
- 수동 모드부터 시작해 보안 검토와 운영 신뢰를 먼저 확보한다.

## 수동 모드와 자동 모드

### 수동 모드

- 민감정보 탐지와 치환은 내부 엔진이 수행한다.
- 치환 결과, 탐지 리포트, 복사 가능한 프롬프트를 사용자에게 보여준다.
- 외부 SOTA 모델 호출은 하지 않는다.
- 초기 MVP의 기본 운영 방식이다.

### 자동 모드

- 수동 모드의 치환 단계를 그대로 유지한다.
- 서버가 치환본을 외부 모델 API로 전달한다.
- 응답을 세션 매핑으로 역치환해 사용자에게 보여준다.
- 지금 단계에서는 깊게 구현하지 않고 인터페이스와 확장 포인트만 설계한다.

## 기존 `24-secure-bridge`와의 차이

- `24-secure-bridge`는 참고용 레퍼런스이며, 구조를 그대로 복사하지 않는다.
- 기존 프로젝트는 Electron 성격이 강했지만, IPU는 웹 기반 워크벤치를 중심으로 설계한다.
- 기존 프로젝트가 보안 브리지와 AI 호출을 함께 담았다면, IPU는 보안 엔진, 웹 애플리케이션, 외부 모델 연동 경계를 더 명확히 분리한다.
- IPU의 초기 목표는 "기업용 AI 방화벽 MVP 구조 확립"이며, 자동 호출보다 수동 검토 경험을 우선한다.

## 초기 개발 방향

- 문서 우선: 제품 정의, 아키텍처, MVP 범위, 백로그를 먼저 고정한다.
- 웹 우선: 브라우저 기반 업로드, 치환 결과 확인, 리포트 검토 경험을 기본으로 설계한다.
- 엔진 분리: 민감정보 탐지, 치환, 세션 매핑, 역치환 로직을 독립된 보안 엔진으로 설계한다.
- 확장 가능성: 외부 모델 커넥터, 파일 파서, 음성 처리, 정책 엔진은 후속 단계에서 모듈식으로 연결한다.

## 디렉터리 구조

```text
24-1-ipu-ai-firewall/
├── AGENTS.md
├── README.md
├── docs/
│   ├── README.md
│   ├── 00-master-roadmap.md
│   ├── business/
│   └── development/
├── frontend/
│   ├── README.md
│   ├── runtime-config.js
│   ├── src/
│   └── tests/
├── backend/
│   ├── README.md
│   └── app/
│       ├── api/
│       ├── core/
│       └── services/
├── engine/
│   ├── README.md
│   ├── src/
│   └── tests/
└── prompts/
    └── README.md
```

## 현재 상태

현재는 문서 우선 구조 위에 수동 모드 MVP의 기본 end-to-end 흐름까지 연결된 상태다.

- 프론트엔드:
  - 텍스트 입력
  - `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.hwpx` 파일 업로드
  - 일반인/전문가 공통 음성 업로드
  - policy 선택
  - 상태 메시지 분리
  - 4영역 워크벤치 렌더링
- 백엔드:
  - `/health`
  - `/api/v1/mode/manual-preview`
  - `/api/v1/mode/manual-preview/file`
  - `/api/v1/mode/manual-preview/audio`
  - 최소 observability/timing 로그
- 엔진:
  - detect / replace / restore / build_report
  - TTL 기반 메모리 세션 저장소
- 테스트:
  - backend API smoke test
  - frontend smoke test
  - frontend-backend live integration smoke test
  - real whisper smoke / real audio API smoke

현재 음성 입력 기준은 보수적으로 잡는다.

- `5초 ~ 15초` 짧은 샘플은 데모 가능 범위다.
- `30초 미만`은 내부 검증 범위로 본다.
- `1분 이상` 긴 음성은 아직 기본 지원으로 말하지 않고, 분할 후 업로드를 권장한다.
- 다화자 음성과 회의 녹음 전체본은 아직 기본 지원으로 말하지 않는다.
- 긴 음성 benchmark는 기본 verification이 아니라 opt-in 검증선으로 유지한다.

자세한 기준은 [`docs/development/25-long-audio-handling-policy.md`](./docs/development/25-long-audio-handling-policy.md), [`docs/development/27-multi-speaker-and-meeting-audio-policy.md`](./docs/development/27-multi-speaker-and-meeting-audio-policy.md), [`docs/development/28-long-audio-verification-policy.md`](./docs/development/28-long-audio-verification-policy.md) 를 따른다.
