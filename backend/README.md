# Backend

웹 API, 업로드 오케스트레이션, 세션 관리 계층이다. 현재는 수동 모드 워크벤치를 프론트엔드와 연결하기 위한 `manual-preview` API가 내부 `engine` 을 호출하는 구조까지 연결된 상태다. 파일 업로드는 parser 계층을 통해 텍스트를 추출한 뒤 엔진에 전달한다.

## 현재 구현 범위

- FastAPI 앱 진입점
- CORS 허용 설정
- `/api/v1/mode/manual-preview` 라우터
- `/api/v1/mode/manual-preview/file` 라우터
- `/api/v1/mode/manual-preview/audio` 라우터
- `/api/v1/mode/manual-preview/restore` 라우터
- request/response schema
- `engine` 연동 기반 수동 모드 orchestration 서비스
- 추후 자동 모드와 파일/음성 입력 확장을 위한 서비스 분리

## 구조

```text
backend/
├── README.md
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py
    ├── api/
    │   ├── __init__.py
    │   ├── router.py
    │   ├── routes/
    │   │   ├── __init__.py
    │   │   └── manual_mode.py
    │   └── schemas/
    │       ├── __init__.py
    │       └── manual_preview.py
    ├── core/
    │   └── __init__.py
    └── services/
        ├── file_parser.py
        ├── __init__.py
        └── manual_preview_service.py
```

## 실행 방법

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8241
```

기본 세션 저장소는 SQLite다. 기본 경로는 프로젝트 루트 기준 `data/runtime/manual_preview_sessions.sqlite3` 이며, 아래 환경변수로 바꿀 수 있다.

```bash
export IPU_SESSION_STORE_KIND=sqlite
export IPU_SESSION_STORE_PATH=/tmp/ipu_manual_preview_sessions.sqlite3
export IPU_SESSION_TTL_SECONDS=900
export IPU_AUDIO_TRANSCRIBER=whisper
export IPU_WHISPER_MODEL_NAME=small
export IPU_WHISPER_MODEL_DIR="G:/Ddrive/BatangD/task/workdiary/48. 2024_성장지원/New_dev/models/whisper"
export IPU_WHISPER_LANGUAGE=auto
export IPU_WHISPER_TASK=transcribe
export IPU_WHISPER_USE_GPU=true
```

- `IPU_SESSION_STORE_KIND=memory` 로 두면 기존 메모리 저장소로 되돌릴 수 있다
- SQLite 저장소를 쓰면 백엔드 프로세스 재시작 후에도 TTL 범위 내에서는 restore 매핑을 유지할 수 있다
- `IPU_AUDIO_TRANSCRIBER=whisper` 가 기본값이며, 테스트나 비활성화 목적이면 `placeholder` 로 둘 수 있다
- 기본 Whisper 모델 경로는 `49-1-padiem-rnd`에서 이미 쓰던 자산 위치(`48.../models/whisper`)를 재사용한다
- 세션 저장소 상태 확인: `python3 scripts/manage_manual_preview_sessions.py stats`
- 만료 세션 정리: `python3 scripts/manage_manual_preview_sessions.py cleanup`

자동화 smoke test 실행:

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall/backend
source .venv/bin/activate
python3 -m unittest tests.test_manual_preview_api
```

WSL에서 `/mnt/...` 아래 가상환경이 지나치게 느리면 빠른 임시 가상환경으로 우회하는 편이 안정적이다.

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall
FAST_BACKEND_PY="$(./scripts/ensure_fast_backend_venv.sh)"

cd backend
"$FAST_BACKEND_PY" -m unittest tests.test_manual_preview_api
```

- 기본 임시 경로는 `/tmp/ipu_backend_test_venv`
- `IPU_FAST_BACKEND_VENV=/path/to/venv` 로 경로를 바꿀 수 있다
- [`run_verification_suite.sh`](../run_verification_suite.sh) 도 이 빠른 경로를 우선 사용하며, backend API smoke와 PDF 품질 샘플 테스트를 함께 돌린다

기본 확인:

- `GET http://127.0.0.1:8241/health`
- `POST http://127.0.0.1:8241/api/v1/mode/manual-preview`
- `POST http://127.0.0.1:8241/api/v1/mode/manual-preview/file`
- `POST http://127.0.0.1:8241/api/v1/mode/manual-preview/audio`
- `POST http://127.0.0.1:8241/api/v1/mode/manual-preview/restore`

간단한 smoke test:

```bash
curl -s http://127.0.0.1:8241/health

curl -s -X POST http://127.0.0.1:8241/api/v1/mode/manual-preview \
  -H "Content-Type: application/json" \
  -d '{
    "content": "아이피유테크 홍길동 이사는 고객사 contact@ipu.co.kr 과 010-1234-5678 정보를 포함한 제안서를 검토해 주세요. 계약 금액은 12,500,000원입니다.",
    "content_type": "text",
    "policy": "default"
  }'

curl -s -X POST http://127.0.0.1:8241/api/v1/mode/manual-preview/file \
  -F "file=@sample.txt;type=text/plain" \
  -F "policy=default"

curl -s -X POST http://127.0.0.1:8241/api/v1/mode/manual-preview/audio \
  -F "file=@sample.wav;type=audio/wav" \
  -F "policy=default"

curl -s -X POST http://127.0.0.1:8241/api/v1/mode/manual-preview/restore \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "ipu-20260315000000-abcdef",
    "replaced_text": "[ORG_01] [PERSON_01] 이사는 [EMAIL_01] 로 연락합니다."
  }'
```

예시 요청:

```json
{
  "content": "아이피유테크 홍길동 이사는 고객사 contact@ipu.co.kr 과 010-1234-5678 정보를 포함한 제안서를 검토해 주세요. 계약 금액은 12,500,000원입니다.",
  "content_type": "text",
  "policy": "default"
}
```

## 응답 필드

- `session_id`
- `original_text`
- `replaced_text`
- `detections`
- `replacements`
- `report`
- `copy_ready_prompt`

`report` 표준 필드:

- `total_detections`
- `risk_level`: `low-risk` | `moderate-risk` | `high-risk`
- `strategy`: `alias` | `strict_token`
- `review_status`: `clean` | `review-required`

자세한 기준은 [`docs/development/16-report-format-standard.md`](../docs/development/16-report-format-standard.md) 를 따른다.

restore 응답 필드:

- `session_id`
- `restored_text`
- `restored`

프론트엔드 mock UI가 기대하는 필드명과 맞춰 두었다.

## 파일 입력 지원 범위

- 현재는 `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.hwpx` 업로드를 지원한다.
- 음성 업로드는 별도 `/audio` route 를 통해 처리한다.
- 음성 업로드는 기본적으로 로컬 Whisper transcriber 를 시도하며, 테스트/비활성화 시에는 `IPU_AUDIO_TRANSCRIBER=placeholder` 로 placeholder 경로를 강제할 수 있다.
- `multipart/form-data` 로 파일을 받는다.
- `.txt`, `.md`, `.csv` 는 UTF-8 텍스트로 해석하고, `.pdf` 는 텍스트 추출 가능한 PDF만, `.docx` 는 본문 텍스트가 있는 Word 문서만, `.hwpx` 는 section XML에서 본문 텍스트를 추출 가능한 문서만 지원한다.
- `.pdf` 는 페이지별 텍스트를 추출한 뒤 공백을 정리해 합친다.
- `.pdf` 에 텍스트 레이어가 없으면 `pdftoppm -> tesseract` OCR fallback 을 시도한다.
- backend 테스트에는 텍스트 레이어 PDF 2종, OCR fallback PDF 2종 품질 샘플이 포함돼 있다.
- OCR 도구가 없으면 generic 실패가 아니라 `tesseract` / `pdftoppm` 설치 안내 메시지로 응답한다.
- 암호화된 PDF 는 아직 지원하지 않는다.
- 최대 파일 크기는 `100MB` 다.
- 음성도 현재 `.wav`, `.mp3`, `.m4a`, `.mp4`, `.webm` 와 `100MB` 기준으로 받는다.
- 짧은 샘플 데모 기준은 `5초 ~ 15초` 쪽이 안전하고, `30초 미만`은 내부 검증 범위다.
- `1분 이상` 긴 음성은 현재 기본 지원으로 보지 않고, 분할 후 업로드를 권장한다.
- 다화자 음성, 회의 녹음 전체본, 화자 분리 결과는 현재 기본 지원으로 보지 않는다.
- 바이너리 `.hwp` 는 현재 직접 파싱하지 않고, `.hwpx`, `.pdf`, `.docx`, `.txt` 중 하나로 변환한 뒤 업로드하도록 안내한다.
- 이미지 스캔 PDF와 기타 바이너리 파일은 아직 지원하지 않는다.
- 지원하지 않는 파일 형식은 `415` 에러로 응답한다.

자세한 긴 음성 기준은 [`docs/development/25-long-audio-handling-policy.md`](../docs/development/25-long-audio-handling-policy.md) 를 따른다.
다화자 / 회의 녹음 기준은 [`docs/development/27-multi-speaker-and-meeting-audio-policy.md`](../docs/development/27-multi-speaker-and-meeting-audio-policy.md) 를 따른다.

## 현재 동작 설명

- 현재 탐지, 치환, 세션 매핑, 리포트 생성은 `engine/src/manual_preview_engine.py` 가 담당한다.
- 백엔드 `manual_preview_service.py` 는 요청을 엔진에 전달하고 결과를 API schema로 감싸는 얇은 orchestration 계층이다.
- 파일 입력은 `services/file_parser.py` 의 parser 계층이 먼저 확장자/인코딩/크기를 검증하고, 텍스트/PDF/DOCX/HWPX 본문을 추출한다.
- 음성 입력은 `services/audio_transcriber.py` 의 transcriber 계층을 통해 로컬 Whisper 또는 placeholder 경로를 분기한다.
- 현재 기본 로컬 STT 후보는 `whisper` 이며, `49-1-padiem-rnd/modules/stt_whisper/run.py` 에서 이미 쓰던 model 계열과 경로를 그대로 재사용한다.
- 실제 Whisper 경로 확인은 `python3 scripts/run_real_whisper_smoke.py` 로 짧은 샘플 기준 수동 검증을 수행한다.
- API 전체 경로 기준 실측은 `python3 scripts/run_real_whisper_api_smoke.py` 로 별도 opt-in smoke를 수행한다.
- 현재는 segment / timestamp 를 API 응답 계약에 올리지 않고 plain text 전사만 사용한다.
- 현재는 speaker label, diarization, meeting transcript 전용 계약도 올리지 않는다.
- OCR fallback 을 쓰려면 실행 환경에 `pdftoppm` 과 `tesseract` 가 있어야 한다.
- 목적은 프론트 연동 계약을 유지하면서 엔진과 웹 레이어의 경계를 분리하는 것이다.

segment / timestamp 기준은 [`docs/development/26-audio-segment-and-timestamp-policy.md`](../docs/development/26-audio-segment-and-timestamp-policy.md) 를 따른다.

## policy 동작

- frontend 가 보내는 `policy` 값은 backend 를 거쳐 engine 으로 전달된다.
- 현재 공식 preset은 `default`, `strict_token`, `local_rewrite` 세 가지다.
- `default` 는 현재 직접 표기된 `EMAIL`, `PHONE`, `PERSON` 만 탐지하고 `[EMAIL_ALIAS_01]` 같은 alias 토큰으로 치환한다.
- `strict_token` 은 `ORG`, `AMOUNT` 까지 포함해 더 넓게 탐지하고, `security at ipu dot co kr` 같은 변형 이메일과 직함 없는 실명 전달 문맥도 추가로 잡아 `[EMAIL_01]` 같은 strict token 으로 치환한다.
- `local_rewrite` 는 strict_token 수준의 탐지 범위를 사용하고, Ollama 로컬 모델이 생성한 문맥 기반 일반화 표현으로 치환한다. 모델 실패 시 deterministic fallback을 사용한다.
- 응답 스키마는 동일하며, policy 차이는 `detections`, `replacements`, `replaced_text`, `report` 값에 반영된다.
- preset 기준 문서는 [`docs/development/17-security-policy-presets.md`](../docs/development/17-security-policy-presets.md) 를 따른다.

## 최소 운영 로그 범위

- `manual_preview_started`
- `manual_preview_succeeded`
- `manual_preview_failed`

현재 로그에는 아래 메타 정보만 남긴다.

- `request_type`: `text` 또는 `file`
- `policy`
- `content_type`
- `session_id`
- `detection_count`
- `replacement_count`
- `report_strategy`
- `processing_ms`

민감정보 보호 원칙:

- 원문 전체 텍스트는 로그에 남기지 않는다.
- 이메일, 전화번호, 사람 이름 같은 실제 탐지 값도 로그에 남기지 않는다.
- 운영 관찰 목적의 최소 메타 정보만 기록한다.
- 자세한 기준은 [`docs/development/15-logging-and-audit-scope.md`](../docs/development/15-logging-and-audit-scope.md) 를 따른다.

## import 경로 처리

- backend `requirements.txt` 는 `-e ..` 로 프로젝트 루트의 `engine` 패키지를 editable install 한다.
- 따라서 `manual_preview_service.py` 는 `sys.path` 를 직접 조작하지 않고 `engine.src.manual_preview_engine` 를 import 한다.
- 새 환경에서는 `pip install -r requirements.txt` 를 먼저 실행해야 한다.

## 다음 연동 포인트

- 바이너리 `.hwp` 는 직접 파싱 대신 변환 안내 전략 유지
- 스캔형 PDF/OCR 경로 검토
- OCR 품질 샘플셋 확대
- PDF 품질 샘플셋 확대
- DOCX 스타일/표/머리글 처리 범위 확장
- HWPX 표/중첩 객체 추출 범위 확장
- 파일/음성 입력 라우트가 추가되면 같은 엔진 계층을 재사용하도록 확장
