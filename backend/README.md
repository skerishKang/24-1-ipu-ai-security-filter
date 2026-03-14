# Backend

웹 API, 업로드 오케스트레이션, 세션 관리 계층이다. 현재는 수동 모드 워크벤치를 프론트엔드와 연결하기 위한 `manual-preview` API가 내부 `engine` 을 호출하는 구조까지 연결된 상태다.

## 현재 구현 범위

- FastAPI 앱 진입점
- CORS 허용 설정
- `/api/v1/mode/manual-preview` 라우터
- `/api/v1/mode/manual-preview/file` 라우터
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
        ├── __init__.py
        └── manual_preview_service.py
```

## 실행 방법

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8241
```

자동화 smoke test 실행:

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter/backend
source .venv/bin/activate
python3 -m unittest tests.test_manual_preview_api
```

기본 확인:

- `GET http://127.0.0.1:8241/health`
- `POST http://127.0.0.1:8241/api/v1/mode/manual-preview`
- `POST http://127.0.0.1:8241/api/v1/mode/manual-preview/file`

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

프론트엔드 mock UI가 기대하는 필드명과 맞춰 두었다.

## 파일 입력 지원 범위

- 현재는 `.txt` 업로드만 지원한다.
- `multipart/form-data` 로 파일을 받는다.
- 내용은 UTF-8 텍스트로 해석한 뒤 기존 manual-preview 엔진 흐름에 연결한다.
- 최대 파일 크기는 `1MB` 다.
- `PDF`, `DOCX`, `HWP`, 바이너리 파일은 아직 지원하지 않는다.
- 지원하지 않는 파일 형식은 `415` 에러로 응답한다.

## placeholder 동작 설명

- 현재 탐지, 치환, 세션 매핑, 리포트 생성은 `engine/src/manual_preview_engine.py` 가 담당한다.
- 백엔드 `manual_preview_service.py` 는 요청을 엔진에 전달하고 결과를 API schema로 감싸는 얇은 orchestration 계층이다.
- 목적은 프론트 연동 계약을 유지하면서 엔진과 웹 레이어의 경계를 분리하는 것이다.

## policy 동작

- frontend 가 보내는 `policy` 값은 backend 를 거쳐 engine 으로 전달된다.
- `default` 는 현재 `EMAIL`, `PHONE`, `PERSON` 만 탐지하고 `[EMAIL_ALIAS_01]` 같은 alias 토큰으로 치환한다.
- `strict_token` 은 `ORG`, `AMOUNT` 까지 포함해 더 넓게 탐지하고 `[EMAIL_01]` 같은 strict token 으로 치환한다.
- 응답 스키마는 동일하며, policy 차이는 `detections`, `replacements`, `replaced_text`, `report` 값에 반영된다.
- 다만 둘 다 아직 정규식 기반 placeholder 정책이므로 운영 등급의 정밀 정책 엔진은 아니다.

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

## import 경로 처리

- backend `requirements.txt` 는 `-e ..` 로 프로젝트 루트의 `engine` 패키지를 editable install 한다.
- 따라서 `manual_preview_service.py` 는 `sys.path` 를 직접 조작하지 않고 `engine.src.manual_preview_engine` 를 import 한다.
- 새 환경에서는 `pip install -r requirements.txt` 를 먼저 실행해야 한다.

## 다음 연동 포인트

- `policy` 와 `content_type` 를 실제 엔진 정책 선택과 입력 타입 분기로 연결
- 세션 저장소를 메모리에서 TTL 기반 저장소로 교체
- 텍스트 외 문서 포맷용 파서 계층 추가
- 파일/음성 입력 라우트가 추가되면 같은 엔진 계층을 재사용하도록 확장
