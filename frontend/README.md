# Frontend

웹 기반 수동 모드 보안 치환 워크벤치 영역이다. 현재 구현은 다른 모델 작업과 충돌을 피하기 위해 `frontend/` 내부에서만 동작하는 무의존성 정적 UI로 구성했다.

## 현재 구현 범위

- 일반인 / 전문가 화면 모드 전환
- 텍스트 입력 화면
- `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.hwpx` 파일 업로드 화면
- `.wav`, `.mp3`, `.m4a`, `.mp4`, `.webm` 음성 업로드 화면
- 문서 파일 드래그앤드롭 업로드
- 간단한 policy 선택 UI
- 원문과 치환본 비교 패널
- 탐지 리포트 패널
- 외부 AI용 복사 프롬프트 패널
- 수동 모드 중심 4영역 레이아웃
- `manual-preview` API 연동
- 백엔드 실패 시 mock fallback

## 구조

```text
frontend/
├── index.html
├── README.md
├── runtime-config.js
└── src/
    ├── config.js
    ├── main.js
    ├── styles.css
    ├── components/
    │   ├── AppShell.js
    │   ├── CopyPromptPanel.js
    │   ├── InputPanel.js
    │   ├── ReportPanel.js
    │   └── ResultPanel.js
    │   ├── SimpleResultPanel.js
    │   └── ViewModeToggle.js
    ├── services/
    │   ├── manualPreviewApi.js
    │   └── manualPreviewMock.js
    ├── ui/
    │   └── createPanelFrame.js
    └── utils/
        └── createSessionId.js
```

## 실행 방법

별도 의존성 없이 정적 파일로 열 수 있다.

```bash
cd frontend
python3 -m http.server 4241
```

브라우저에서 `http://localhost:4241` 로 접속하면 된다.

## 브라우저 smoke test

핵심 수동 모드 흐름은 Playwright 기반 smoke script로 확인할 수 있다.

```bash
# Windows
cd 24-1-ipu-ai-security-filter\frontend
node tests\runSmokeTests.js

# Linux/WSL
cd frontend
node tests/runSmokeTests.js
```

현재 자동화 범위:

- 첫 로드 시 4영역 워크벤치 렌더링
- 텍스트 요청 fallback 상태 표시
- 텍스트 파일 업로드 성공 상태와 결과 패널 반영
- 지원하지 않는 파일 선택 시 상태 문구
- 빈 업로드 파일 선택 시 상태 문구
- 일반인/전문가 모드 음성 업로드 성공 상태와 결과 패널 반영

현재 smoke test는 프론트 상태 흐름 검증에 집중하기 위해 Playwright route interception을 사용한다. 즉, fallback 케이스는 backend 미연결 상태를, 파일 성공 케이스는 backend 성공 응답을 브라우저 레벨에서 재현한다.

## 브라우저 live integration test

실제 backend 서버가 실행 중일 때 frontend가 live 응답을 반영하는지 검증한다.

```bash
# Windows - backend 먼저 실행 필요
cd 24-1-ipu-ai-security-filter\backend
.venv-win\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8241

# Windows - frontend 서버 실행 (다른 터미널)
cd 24-1-ipu-ai-security-filter\frontend
python -m http.server 4241

# Windows - live integration test 실행
cd 24-1-ipu-ai-security-filter\frontend
node tests\runLiveIntegrationTests.js
```

현재 검증 범위:

- 전문가 모드 첫 로드 시 session/source 에 backend 표시
- 전문가 모드 텍스트 요청 시 session/source 에 backend 표시
- 전문가 모드 파일 업로드 시 session/source 에 backend-file 표시
- audio live integration은 기본 검증선에 포함하지 않는다. 현재는 backend Whisper 의존이 있어 opt-in smoke 로 분리한다.

## API 설정 변경 방법

기본 backend URL은 `http://127.0.0.1:8241` 이며, [`runtime-config.js`](./runtime-config.js) 에서 바꿀 수 있다.

```js
window.IPU_RUNTIME_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:9000",
};
```

- 값이 없으면 [`src/config.js`](./src/config.js) 의 기본값으로 돌아간다.
- 현재는 정적 서버 구조이므로 복잡한 환경변수 대신 런타임 설정 파일 1개만 바꾸면 된다.
- `manualPreviewApi.js` 는 이 설정을 읽어 `/api/v1/mode/manual-preview` URL을 조합한다.

런타임 smoke test 기준:

- 전문가 모드에서 백엔드가 정상 실행 중이면 상단 세션 표시가 `... · backend` 로 보인다.
- 이때 입력 패널 상태 문구는 `백엔드 응답으로 치환 결과를 갱신했습니다.` 로 표시된다.
- 전문가 모드에서 백엔드가 꺼져 있거나 연결 실패하면 상단 세션 표시가 `... · mock-fallback` 으로 바뀐다.
- 일반인 모드에서는 session/source 를 숨기고, 상태 문구와 결과 카드만 보여준다.

## 화면 모드

- 기본 진입은 `일반인 모드` 다.
- `일반인 모드`
  - 입력 영역
  - 치환 미리보기 생성 버튼
  - 안전하게 바뀐 텍스트
  - 보호된 항목 수 요약
  - 결과 복사 버튼
  - 원문 보기 접기/펼치기
- `전문가 모드`
  - 기존 4영역 워크벤치 구조를 그대로 유지
  - policy, 치환 상세, 탐지 리포트, 복사 프롬프트, session/source 정보를 확인 가능
  - 텍스트, 문서 파일, 음성 파일 입력을 모두 다룬다
- 일반인 모드에서는 `policy`, 상세 탐지 목록, 상세 치환 목록, 리포트 metric, session/source 같은 내부 정보는 숨긴다.
- 음성 업로드는 현재 일반인/전문가 모드 모두에서 노출한다.

## 파일 업로드 사용 방법

- 입력 패널에서 `텍스트 파일 업로드` 모드를 선택한다.
- `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.hwpx` 파일을 고르거나 드롭존에 끌어다 놓은 뒤 `치환 미리보기 생성` 을 누르면 `POST /api/v1/mode/manual-preview/file` 로 요청한다.
- 응답 결과는 기존과 동일하게 원문, 치환본, 리포트, 복사용 프롬프트 4영역에 렌더링된다.
- 파일 업로드는 backend live 응답만 사용하며, 실패 시 명확한 상태 문구를 보여준다.
- 현재 지원 범위는 `.txt`, `.md`, `.csv` 의 UTF-8 텍스트, 텍스트 추출 가능한 `.pdf`, 본문 텍스트가 있는 `.docx`, section XML에서 본문 텍스트를 읽을 수 있는 `.hwpx` 다.
- 바이너리 `.hwp` 파일을 선택하면 직접 업로드하지 않고 `.hwpx`, `.pdf`, `.docx`, `.txt` 변환 안내 문구를 보여준다.
- 리렌더 후에도 선택한 파일명은 패널에 유지되며, 다시 선택하지 않고 바로 재요청할 수 있다.

현재 에러 상태 정리:

- 텍스트 입력은 backend 성공, backend 실패 후 mock fallback, 로딩 상태를 구분해 보여준다.
- 파일 업로드는 미선택, 지원하지 않는 확장자, 비어 있는 파일, backend 요청 실패를 각각 다른 문구로 보여준다.
- 파일 업로드는 mock fallback 없이 backend 결과 또는 에러 상태만 표시한다.
- 상태 문구는 [`src/statusMessages.js`](./src/statusMessages.js) 에서 한 곳으로 관리한다.

## 음성 업로드 사용 방법

- 입력 패널에서 `음성 업로드` 모드를 선택한다.
- `.wav`, `.mp3`, `.m4a`, `.mp4`, `.webm` 파일을 고른 뒤 `치환 미리보기 생성` 을 누르면 `POST /api/v1/mode/manual-preview/audio` 로 요청한다.
- backend 는 로컬 Whisper STT로 먼저 전사한 뒤, 전사 텍스트를 기존 manual-preview 엔진으로 보낸다.
- 전문가 모드에서는 성공 시 session/source 가 `backend-audio` 로 표시된다.
- 일반인 모드에서는 session/source 대신 상태 문구와 결과 카드로만 보여준다.
- 음성 업로드는 mock fallback 없이 backend live 응답만 사용한다.
- 로컬 STT가 준비되지 않았으면 별도 안내 문구를 보여준다.
- 현재 데모에 바로 쓰는 권장 길이는 `5초 ~ 15초` 다.
- `30초 미만`은 내부 검증 범위로 보지만, 품질과 속도를 기본 보장으로 말하지 않는다.
- `1분 이상` 긴 음성은 현재 기본 경로로 권장하지 않고, 분할 후 업로드를 권장한다.
- 현재는 segment / timestamp 를 UI에 노출하지 않고, plain text 전사 결과만 사용한다.
- 다화자 음성, 회의 녹음 전체본, 화자별 결과 UI는 현재 기본 노출 범위에 넣지 않는다.

자세한 기준은 [`../docs/development/25-long-audio-handling-policy.md`](../docs/development/25-long-audio-handling-policy.md), [`../docs/development/26-audio-segment-and-timestamp-policy.md`](../docs/development/26-audio-segment-and-timestamp-policy.md), [`../docs/development/27-multi-speaker-and-meeting-audio-policy.md`](../docs/development/27-multi-speaker-and-meeting-audio-policy.md) 를 따른다.

## policy 선택 사용 방법

- 입력 패널에서 `Policy` 를 `default`, `strict_token`, `local_rewrite` 중에서 선택할 수 있다.
- 각 policy의 의미:
  - `default`: 읽기 쉬운 기본 보호
  - `strict_token`: 보수적 비식별화
  - `local_rewrite`: 로컬 모델 보조 치환 (Ollama 기반)
- 텍스트 입력과 파일 업로드 요청 모두 같은 선택 값을 사용한다.
- `default`와 `strict_token`은 정규식 기반, `local_rewrite`는 Ollama 로컬 모델 기반 치환을 수행한다.

## 연동 동작 설명

- 기본 흐름은 `src/services/manualPreviewApi.js` 를 통해 `POST /api/v1/mode/manual-preview` 를 호출한다.
- API base URL은 `runtime-config.js` -> `src/config.js` 순서로 결정된다.
- 요청 본문은 `{ content, content_type: "text", policy }` 형태다.
- 파일 업로드는 `multipart/form-data` 로 `POST /api/v1/mode/manual-preview/file` 를 호출한다.
- 음성 업로드는 `multipart/form-data` 로 `POST /api/v1/mode/manual-preview/audio` 를 호출한다.
- 백엔드가 정상 응답하면 해당 결과를 그대로 4영역에 렌더링한다.
- 텍스트 입력에서 백엔드가 꺼져 있거나 실패하면 `src/services/manualPreviewMock.js` 로 자동 fallback 한다.
- 파일/음성 업로드는 mock fallback 없이 에러 상태만 보여준다.
- mock 서비스는 비교용이자 비상 대체 경로로 유지한다.

## 다음 연동 포인트

- 백엔드 응답의 `session_id`, `detections`, `replacements`, `report`, `copy_ready_prompt` 필드 검증 강화
- 파일 업로드 drag-and-drop 개선
- 자동 모드가 붙더라도 현재 4영역 레이아웃은 유지하고 결과 패널만 확장

## 템플릿 모드 실험

기존 manual-preview 와 별개로, 저장된 승인 템플릿 JSON을 읽어 입력 폼을 만들고 문서 초안을 재구성하는 프론트엔드 전용 데모 진입점을 추가했다.

- 진입 파일: [`template-mode.html`](./template-mode.html)
- 메인 스크립트: [`src/template-mode-main.js`](./src/template-mode-main.js)
- 템플릿 카탈로그: [`src/data/templateCatalog.js`](./src/data/templateCatalog.js)
- 현재 선택 가능 템플릿:
  - 기본 승인 버전: [`templates/approved/contract_review_request/v1.1.0.template.json`](../templates/approved/contract_review_request/v1.1.0.template.json)
  - [`templates/approved/customer_inquiry_intake/v1.1.0.template.json`](../templates/approved/customer_inquiry_intake/v1.1.0.template.json)
  - [`templates/approved/internal_report_weekly/v1.1.0.template.json`](../templates/approved/internal_report_weekly/v1.1.0.template.json)

현재 템플릿 모드 범위:

- 승인 템플릿 선택 UI
- 승인 템플릿 JSON fetch
- 공통 템플릿 스키마를 단순 UI 모델로 정규화
- `text`, `textarea`, `amount`, `date`, `email`, `phone` 필드 타입 렌더링
- 템플릿 field 정의 기반 동적 입력 UI 생성
- 입력값을 `template_text` 에 주입해 실시간 문서 초안 재구성
- 별도 미리보기 패널에서 생성된 초안과 필드별 입력 상태 표시

실행 방법:

```bash
# 프로젝트 루트에서 실행
python3 -m http.server 4241
```

- manual-preview: `http://localhost:4241/frontend/index.html`
- template mode demo: `http://localhost:4241/frontend/template-mode.html`

주의:

- 템플릿 모드는 `../templates/approved/...` 경로의 실제 JSON을 읽으므로, `frontend/` 가 아니라 프로젝트 루트에서 정적 서버를 띄워야 한다.
- `manual-preview` 기존 흐름은 그대로 유지된다.
- 추출 초안 템플릿은 `demo-samples/derived/*.template.json`, 승인 템플릿은 `templates/approved/.../*.template.json` 에 둔다.
- 상단 선택기에서 템플릿을 바꾸면 입력 폼과 문서 초안이 함께 새 템플릿 기준으로 갱신된다.
